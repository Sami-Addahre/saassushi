import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import calendar_service as gcal
from config import (
    BOT_TOKEN,
    DEPOSIT_EUR,
    RESTAURANT_ADDRESS,
    RESTAURANT_NAME,
    SLOT_HOURS,
    TABLES,
    TIMEZONE,
    UPSELL_OPTIONS,
)
from database import (
    add_waitlist,
    cancel_booking,
    create_booking,
    get_bookings_for_slot,
    get_user_active_booking,
    get_waitlist_for_slot,
    init_db,
    mark_waitlist_notified,
    update_booking,
)
from scheduler import run_reminder_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class BookingStates(StatesGroup):
    guest_name = State()
    guests = State()
    date = State()
    slot = State()
    time = State()
    occasion = State()
    upsell = State()


def find_table(guests: int, date: str, slot: str) -> int | None:
    booked_tables = {b["table_id"] for b in get_bookings_for_slot(date, slot) if b["table_id"]}
    cal_count = gcal.count_calendar_bookings(date, slot)
    total_tables = len(TABLES)

    if len(booked_tables) + cal_count >= total_tables:
        pass  # still try individual table match

    for tid, info in sorted(TABLES.items(), key=lambda x: x[1]["seats"]):
        if tid not in booked_tables and info["seats"] >= guests:
            return tid
    return None


def kb_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Prenota tavolo", callback_data="book")],
        [InlineKeyboardButton(text="Lista d'attesa", callback_data="waitlist_info")],
        [InlineKeyboardButton(text="La mia prenotazione", callback_data="my_booking")],
    ])


def kb_guests():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="guests_1"),
            InlineKeyboardButton(text="2", callback_data="guests_2"),
            InlineKeyboardButton(text="3", callback_data="guests_3"),
        ],
        [
            InlineKeyboardButton(text="4", callback_data="guests_4"),
            InlineKeyboardButton(text="5", callback_data="guests_5"),
            InlineKeyboardButton(text="6+", callback_data="guests_6"),
        ],
    ])


def kb_dates():
    tz = ZoneInfo(TIMEZONE)
    today = datetime.now(tz).date()
    tomorrow = today + timedelta(days=1)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Oggi ({today.strftime('%d/%m')})", callback_data=f"date_{today.isoformat()}")],
        [InlineKeyboardButton(text=f"Domani ({tomorrow.strftime('%d/%m')})", callback_data=f"date_{tomorrow.isoformat()}")],
        [InlineKeyboardButton(text="Altra data (GG/MM)", callback_data="date_custom")],
    ])


def kb_slots():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Pranzo (12:00–15:00)", callback_data="slot_pranzo")],
        [InlineKeyboardButton(text="Cena (19:00–23:00)", callback_data="slot_cena")],
    ])


def kb_times(slot: str):
    start, end = SLOT_HOURS[slot]
    buttons = []
    row = []
    for h in range(start, end):
        for m in (0, 30):
            t = f"{h:02d}:{m:02d}"
            row.append(InlineKeyboardButton(text=t, callback_data=f"time_{t}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_occasions():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Compleanno", callback_data="occ_birthday")],
        [InlineKeyboardButton(text="Serata romantica", callback_data="occ_romantic")],
        [InlineKeyboardButton(text="Business", callback_data="occ_business")],
        [InlineKeyboardButton(text="Nessuna occasione", callback_data="occ_none")],
    ])


def kb_upsells(selected: list):
    buttons = []
    for opt in UPSELL_OPTIONS:
        mark = "[x]" if opt["id"] in selected else "[ ]"
        buttons.append([
            InlineKeyboardButton(
                text=f"{mark} {opt['label']} — €{opt['price']}",
                callback_data=f"upsell_{opt['id']}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="Conferma prenotazione", callback_data="upsell_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    cal_status = "Google Calendar collegato" if gcal.is_configured() else "Calendario locale (configura credentials.json)"
    await message.answer(
        f"<b>{RESTAURANT_NAME}</b>\n"
        f"Sistema intelligente di prenotazione\n\n"
        f"Prenota il tuo tavolo in pochi tap.\n"
        f"Caparra confirmatoria: €{DEPOSIT_EUR:.0f}\n"
        f"Stato: {cal_status}",
        parse_mode="HTML",
        reply_markup=kb_main(),
    )


@dp.callback_query(F.data == "book")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.guest_name)
    await callback.message.answer("A nome di chi vuoi prenotare?")
    await callback.answer()


@dp.message(BookingStates.guest_name)
async def receive_name(message: Message, state: FSMContext):
    await state.update_data(guest_name=message.text.strip())
    await state.set_state(BookingStates.guests)
    await message.answer("Quante persone?", reply_markup=kb_guests())


@dp.callback_query(F.data.startswith("guests_"), BookingStates.guests)
async def receive_guests(callback: CallbackQuery, state: FSMContext):
    guests = int(callback.data.split("_")[1])
    await state.update_data(guests=guests)
    await state.set_state(BookingStates.date)
    await callback.message.answer("Quando?", reply_markup=kb_dates())
    await callback.answer()


@dp.callback_query(F.data.startswith("date_"), BookingStates.date)
async def receive_date(callback: CallbackQuery, state: FSMContext):
    val = callback.data.replace("date_", "")
    if val == "custom":
        await callback.message.answer("Inserisci la data nel formato GG/MM (es. 15/06):")
        await callback.answer()
        return
    await state.update_data(date=val)
    await state.set_state(BookingStates.slot)
    await callback.message.answer("Pranzo o cena?", reply_markup=kb_slots())
    await callback.answer()


@dp.message(BookingStates.date)
async def receive_custom_date(message: Message, state: FSMContext):
    try:
        d = datetime.strptime(message.text.strip(), "%d/%m")
        tz = ZoneInfo(TIMEZONE)
        year = datetime.now(tz).year
        date_str = d.replace(year=year).date().isoformat()
        await state.update_data(date=date_str)
        await state.set_state(BookingStates.slot)
        await message.answer("Pranzo o cena?", reply_markup=kb_slots())
    except ValueError:
        await message.answer("Formato non valido. Usa GG/MM (es. 15/06)")


@dp.callback_query(F.data.startswith("slot_"), BookingStates.slot)
async def receive_slot(callback: CallbackQuery, state: FSMContext):
    slot = callback.data.replace("slot_", "")
    await state.update_data(slot=slot)
    await state.set_state(BookingStates.time)
    await callback.message.answer("Scegli l'orario:", reply_markup=kb_times(slot))
    await callback.answer()


@dp.callback_query(F.data.startswith("time_"), BookingStates.time)
async def receive_time(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.replace("time_", "")
    data = await state.get_data()
    table_id = find_table(data["guests"], data["date"], data["slot"])

    if not table_id:
        await state.update_data(waitlist_date=data["date"], waitlist_slot=data["slot"])
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Entra in lista d'attesa", callback_data="join_waitlist")],
            [InlineKeyboardButton(text="Cambia orario", callback_data="book")],
        ])
        await callback.message.answer(
            "Tutti i tavoli sono occupati per questa fascia.\n"
            "Vuoi entrare in lista d'attesa prioritaria?",
            reply_markup=kb,
        )
        await callback.answer()
        return

    await state.update_data(time=time_str, table_id=table_id)
    await state.set_state(BookingStates.occasion)
    await callback.message.answer(
        f"Tavolo disponibile: {TABLES[table_id]['label']} ({TABLES[table_id]['seats']} posti)\n\n"
        f"Per quale occasione?",
        reply_markup=kb_occasions(),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("occ_"), BookingStates.occasion)
async def receive_occasion(callback: CallbackQuery, state: FSMContext):
    occ = callback.data.replace("occ_", "")
    await state.update_data(occasion=None if occ == "none" else occ, upsells=[])
    await state.set_state(BookingStates.upsell)
    await callback.message.answer(
        "Rendi speciale la serata — seleziona extra (sconto 10%):",
        reply_markup=kb_upsells([]),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("upsell_"), BookingStates.upsell)
async def toggle_upsell(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("upsells", [])

    if callback.data == "upsell_done":
        await confirm_booking(callback, state, data, selected)
        return

    opt_id = callback.data.replace("upsell_", "")
    if opt_id in selected:
        selected.remove(opt_id)
    else:
        selected.append(opt_id)
    await state.update_data(upsells=selected)
    await callback.message.edit_reply_markup(reply_markup=kb_upsells(selected))
    await callback.answer()


async def confirm_booking(callback: CallbackQuery, state: FSMContext, data: dict, upsells: list):
    table_id = data["table_id"]
    table_label = TABLES[table_id]["label"]
    upsell_labels = [o["label"] for o in UPSELL_OPTIONS if o["id"] in upsells]

    event_id = gcal.create_event(
        guest_name=data["guest_name"],
        guests=data["guests"],
        date_str=data["date"],
        time_str=data["time"],
        slot=data["slot"],
        table_label=table_label,
        occasion=data.get("occasion"),
        upsells=upsell_labels,
        telegram_user=callback.from_user.full_name,
    )

    booking_id = create_booking({
        "user_id": callback.from_user.id,
        "user_name": callback.from_user.full_name,
        "guest_name": data["guest_name"],
        "guests": data["guests"],
        "date": data["date"],
        "slot": data["slot"],
        "time": data["time"],
        "table_id": table_id,
        "occasion": data.get("occasion"),
        "upsells": upsell_labels,
        "status": "confirmed",
        "calendar_event_id": event_id,
        "deposit_paid": True,
    })

    cal_note = "\nSincronizzato su Google Calendar" if event_id else "\n(Calendario locale — configura Google per sync)"

    extra_txt = ""
    if upsell_labels:
        extra_txt = f"\nExtra: {', '.join(upsell_labels)}"

    await callback.message.answer(
        f"Prenotazione confermata\n\n"
        f"Nome: {data['guest_name']}\n"
        f"Data: {data['date']} alle {data['time']}\n"
        f"Fascia: {data['slot']}\n"
        f"Persone: {data['guests']}\n"
        f"Tavolo: {table_label}\n"
        f"Caparra: €{DEPOSIT_EUR:.0f} (demo){extra_txt}"
        f"{cal_note}\n\n"
        f"Riceverai promemoria a 24h e 3h dall'appuntamento.\n"
        f"ID prenotazione: #{booking_id}",
        reply_markup=kb_main(),
    )
    await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "join_waitlist")
async def join_waitlist(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    add_waitlist(
        callback.from_user.id,
        callback.from_user.full_name,
        data.get("guests", 2),
        data.get("waitlist_date", data.get("date", "")),
        data.get("waitlist_slot", data.get("slot", "")),
    )
    await callback.message.answer(
        "Sei in lista d'attesa prioritaria.\n"
        "Ti avviseremo appena si libera un tavolo.",
        reply_markup=kb_main(),
    )
    await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "waitlist_info")
async def waitlist_info(callback: CallbackQuery):
    await callback.message.answer(
        "La lista d'attesa ti avvisa in tempo reale quando un tavolo si libera.\n"
        "Avvia una prenotazione e, se esaurito, potrai iscriverti automaticamente.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Prenota ora", callback_data="book")],
        ]),
    )
    await callback.answer()


@dp.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery):
    b = get_user_active_booking(callback.from_user.id)
    if not b:
        await callback.message.answer("Nessuna prenotazione attiva.", reply_markup=kb_main())
        await callback.answer()
        return

    table_label = TABLES.get(b["table_id"], {}).get("label", "—")
    await callback.message.answer(
        f"Prenotazione attiva\n\n"
        f"Nome: {b['guest_name']}\n"
        f"Data: {b['date']} alle {b['time']}\n"
        f"Persone: {b['guests']}\n"
        f"Tavolo: {table_label}\n"
        f"Stato: {b['status']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Cancella", callback_data=f"cancel_{b['id']}")],
        ]),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_cb(callback: CallbackQuery):
    bid = int(callback.data.replace("cancel_", ""))
    from database import get_booking
    b = get_booking(bid)
    if b and b["user_id"] == callback.from_user.id:
        if b.get("calendar_event_id"):
            gcal.delete_event(b["calendar_event_id"])
        cancel_booking(bid)
        await notify_waitlist(callback, b["date"], b["slot"])
        await callback.message.answer("Prenotazione cancellata.", reply_markup=kb_main())
    await callback.answer()


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message):
    b = get_user_active_booking(message.from_user.id)
    if not b:
        await message.answer("Nessuna prenotazione da cancellare.")
        return
    if b.get("calendar_event_id"):
        gcal.delete_event(b["calendar_event_id"])
    cancel_booking(b["id"])
    await notify_waitlist_msg(message, b["date"], b["slot"])
    await message.answer("Prenotazione cancellata.")


async def notify_waitlist(callback: CallbackQuery, date: str, slot: str):
    wl = get_waitlist_for_slot(date, slot)
    if not wl:
        return
    first = wl[0]
    try:
        await bot.send_message(
            first["user_id"],
            f"Si è liberato un tavolo!\n"
            f"Data: {date} — {slot}\n"
            f"Vuoi prenotarlo? Avvia /start e prenota subito.",
        )
        mark_waitlist_notified(first["id"])
    except Exception as exc:
        logger.warning("Notify waitlist failed: %s", exc)


async def notify_waitlist_msg(message: Message, date: str, slot: str):
    wl = get_waitlist_for_slot(date, slot)
    if not wl:
        return
    first = wl[0]
    try:
        await bot.send_message(
            first["user_id"],
            f"Si è liberato un tavolo per {date} ({slot})!\nPrenota subito con /start",
        )
        mark_waitlist_notified(first["id"])
    except Exception:
        pass


async def main():
    init_db()
    asyncio.create_task(run_reminder_loop(bot))
    logger.info("Bot %s online — Calendar: %s", RESTAURANT_NAME, gcal.is_configured())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
