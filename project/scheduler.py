import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from config import RESTAURANT_ADDRESS, RESTAURANT_NAME, TIMEZONE
from database import get_pending_reminders, update_booking

logger = logging.getLogger(__name__)


async def run_reminder_loop(bot: Bot):
    """Controlla ogni 5 minuti se inviare promemoria T-24h, T-3h e feedback post-pasto."""
    tz = ZoneInfo(TIMEZONE)
    while True:
        try:
            now = datetime.now(tz)
            for b in get_pending_reminders():
                booking_dt = datetime.strptime(
                    f"{b['date']} {b['time']}", "%Y-%m-%d %H:%M"
                ).replace(tzinfo=tz)

                diff = booking_dt - now

                # T-24 ore
                if not b["reminder_24h_sent"] and timedelta(hours=23) <= diff <= timedelta(hours=25):
                    await _send_reminder_24h(bot, b)
                    update_booking(b["id"], reminder_24h_sent=1)

                # T-3 ore
                if not b["reminder_3h_sent"] and timedelta(hours=2, minutes=30) <= diff <= timedelta(hours=3, minutes=30):
                    await _send_reminder_3h(bot, b)
                    update_booking(b["id"], reminder_3h_sent=1)

                # Post-pasto (~3h dopo)
                if not b["feedback_sent"] and now - booking_dt >= timedelta(hours=3):
                    await _send_feedback(bot, b)
                    update_booking(b["id"], feedback_sent=1)

        except Exception as exc:
            logger.error("Errore scheduler: %s", exc)

        import asyncio
        await asyncio.sleep(300)


async def _send_reminder_24h(bot: Bot, b: dict):
    text = (
        f"Promemoria prenotazione — {RESTAURANT_NAME}\n\n"
        f"Ciao {b['guest_name']}, domani ti aspettiamo!\n"
        f"Data: {b['date']} alle {b['time']} ({b['slot']})\n"
        f"Persone: {b['guests']}\n\n"
        f"Per cancellare rispondi /cancel"
    )
    try:
        await bot.send_message(b["user_id"], text)
    except Exception as exc:
        logger.warning("Impossibile inviare T-24h a %s: %s", b["user_id"], exc)


async def _send_reminder_3h(bot: Bot, b: dict):
    maps_url = f"https://maps.google.com/?q={RESTAURANT_ADDRESS.replace(' ', '+')}"
    text = (
        f"Ci vediamo tra poco!\n\n"
        f"{RESTAURANT_NAME} ti aspetta alle {b['time']}.\n"
        f"Indirizzo: {RESTAURANT_ADDRESS}\n\n"
        f"Indicazioni: {maps_url}"
    )
    try:
        await bot.send_message(b["user_id"], text)
    except Exception as exc:
        logger.warning("Impossibile inviare T-3h a %s: %s", b["user_id"], exc)


async def _send_feedback(bot: Bot, b: dict):
    text = (
        f"Grazie per essere venuto da {RESTAURANT_NAME}!\n\n"
        f"Com'è stata la tua esperienza? Rispondi con un voto da 1 a 5.\n"
        f"Se ti è piaciuto, lasciaci una recensione su Google — ci aiuta tantissimo!"
    )
    try:
        await bot.send_message(b["user_id"], text)
    except Exception as exc:
        logger.warning("Impossibile inviare feedback a %s: %s", b["user_id"], exc)
