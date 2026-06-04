import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RESTAURANT_NAME = os.getenv("RESTAURANT_NAME", "Sushi Zen")
RESTAURANT_ADDRESS = os.getenv("RESTAURANT_ADDRESS", "Via Roma 12, Rovereto")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Rome")
DEPOSIT_EUR = float(os.getenv("DEPOSIT_EUR", "10"))
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")

# Tavoli: id -> posti
TABLES = {
    1: {"seats": 2, "label": "Tavolo 1"},
    2: {"seats": 4, "label": "Tavolo 2"},
    3: {"seats": 4, "label": "Tavolo 3"},
    4: {"seats": 6, "label": "Tavolo 4"},
    5: {"seats": 8, "label": "Tavolo 5"},
}

SLOT_HOURS = {
    "pranzo": (12, 15),
    "cena": (19, 23),
}

UPSELL_OPTIONS = [
    {"id": "aperitivo", "label": "Aperitivo di benvenuto", "price": 12},
    {"id": "dolce", "label": "Dolce speciale", "price": 8},
    {"id": "sake", "label": "Degustazione sake", "price": 18},
]
