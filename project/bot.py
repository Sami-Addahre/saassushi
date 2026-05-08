import asyncio
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

BOOKINGS_FILE = "bookings.json"
WAITLIST_FILE = "waitlist.json"

# Tavoli demo
TABLES = {
    1: {"free": True},
    2: {"free": True},
    3: {"free": True},
}

pending_booking = {}
waiting_for_name = {}

# =========================
# HELPERS
# =========================

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_free_table():
    for t, v in TABLES.items():
        if v["free"]:
            return t
    return None

def occupy_table(t):
    TABLES[t]["free"] = False

def free_table(t):
    TABLES[t]["free"] = True

# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍾 Prenota Tavolo", callback_data="book")],
        [InlineKeyboardButton(text="⏳ Waiting List", callback_data="waitlist")]
    ])

    await message.answer(
        "🍸 <b>Luxury Booking Demo</b>",
        parse_mode="HTML",
        reply_markup=kb
    )

# =========================
# BOOKING START
# =========================

@dp.callback_query(F.data == "book")
async def booking_start(callback: CallbackQuery):

    table_id = get_free_table()

    if not table_id:
        await callback.message.answer(
            "⚠️ Nessun tavolo disponibile.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏳ Waiting List", callback_data="waitlist")]
            ])
        )
        return

    waiting_for_name[callback.from_user.id] = {"table_id": table_id}

    await callback.message.answer("✨ A nome di chi vuoi prenotare?")

# =========================
# NAME INPUT
# =========================

@dp.message()
async def receive_booking_name(message: Message):

    uid = message.from_user.id

    if uid not in waiting_for_name:
        return

    name = message.text
    table_id = waiting_for_name[uid]["table_id"]

    pending_booking[uid] = {
        "table_id": table_id,
        "name": name
    }

    del waiting_for_name[uid]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎂 Compleanno", callback_data="occasion_birthday")],
        [InlineKeyboardButton(text="❤️ Romantica", callback_data="occasion_romantic")],
        [InlineKeyboardButton(text="💼 Business", callback_data="occasion_business")]
    ])

    await message.answer(
        f"🍸 Perfetto <b>{name}</b>\n✨ Per quale occasione?",
        parse_mode="HTML",
        reply_markup=kb
    )

# =========================
# OCCASION
# =========================

@dp.callback_query(F.data.startswith("occasion_"))
async def occasion(callback: CallbackQuery):

    uid = callback.from_user.id
    occ = callback.data.split("_")[1]

    pending_booking[uid]["occasion"] = occ

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Sì upgrade", callback_data="upsell_yes")],
        [InlineKeyboardButton(text="➡️ No grazie", callback_data="upsell_no")]
    ])

    await callback.message.answer(
        "⭐ Vuoi aggiungere un upgrade?",
        reply_markup=kb
    )

# =========================
# CONFIRM BOOKING
# =========================

@dp.callback_query(F.data.in_(["upsell_yes", "upsell_no"]))
async def confirm(callback: CallbackQuery):

    uid = callback.from_user.id
    data = pending_booking[uid]

    table_id = data["table_id"]
    occupy_table(table_id)

    booking = {
        "user_id": uid,
        "name": data["name"],
        "table": table_id,
        "occasion": data["occasion"],
        "upsell": callback.data == "upsell_yes",
        "time": str(datetime.now()),
        "status": "confirmed"
    }

    bookings = load_json(BOOKINGS_FILE)
    bookings.append(booking)
    save_json(BOOKINGS_FILE, bookings)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Check-in", callback_data=f"checkin_{table_id}")]
    ])

    await callback.message.answer(
        f"""🍾 Prenotazione confermata

• Nome: {booking['name']}
• Tavolo: {table_id}
""",
        reply_markup=kb
    )

    asyncio.create_task(auto_release(table_id))

# =========================
# CHECKIN
# =========================

@dp.callback_query(F.data.startswith("checkin_"))
async def checkin(callback: CallbackQuery):

    table_id = int(callback.data.split("_")[1])

    await callback.message.answer(
        "✅ Check-in confermato.\nIl tavolo si libera in 1h30 (demo veloce 60s)"
    )

# =========================
# AUTO RELEASE
# =========================

async def auto_release(table_id):

    await asyncio.sleep(60)  # demo

    free_table(table_id)

    await notify_waitlist(table_id)

# =========================
# WAITLIST
# =========================

@dp.callback_query(F.data == "waitlist")
async def waitlist(callback: CallbackQuery):

    data = load_json(WAITLIST_FILE)

    data.append({
        "user_id": callback.from_user.id,
        "name": callback.from_user.full_name,
        "time": str(datetime.now())
    })

    save_json(WAITLIST_FILE, data)

    await callback.message.answer("⏳ Sei in waiting list VIP.")

# =========================
# NOTIFY WAITLIST
# =========================

async def notify_waitlist(table_id):

    data = load_json(WAITLIST_FILE)

    for u in data:
        try:
            await bot.send_message(
                u["user_id"],
                f"🔥 Tavolo disponibile!\nTavolo {table_id}"
            )
        except:
            pass

# =========================
# MAIN
# =========================

async def main():
    print("BOT ONLINE 🍸")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())