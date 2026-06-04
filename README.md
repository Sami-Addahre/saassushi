# SaaS Sushi — Sistema Intelligente di Prenotazione

Bot Telegram per ristoranti sushi con sincronizzazione **Google Calendar**, lista d'attesa, upsell e promemoria automatici.

## Struttura

```
saassushi/
├── website/          → Sito landing che spiega il sistema
├── project/          → Bot Telegram (Python + aiogram)
│   ├── bot.py
│   ├── calendar_service.py
│   ├── database.py
│   └── scheduler.py
└── README.md
```

## Avvio rapido

### 1. Bot Telegram

```bash
cd project
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # Inserisci BOT_TOKEN
python bot.py
```

### 2. Google Calendar

1. Vai su [Google Cloud Console](https://console.cloud.google.com)
2. Crea un progetto e abilita **Google Calendar API**
3. Crea un **Service Account** e scarica `credentials.json` in `project/`
4. Crea un calendario Google e condividilo con l'email del service account (permesso modifica)
5. Copia l'ID del calendario in `.env`:

```
GOOGLE_CALENDAR_ID=xxx@group.calendar.google.com
GOOGLE_CREDENTIALS_FILE=credentials.json
```

Ogni prenotazione confermata viene sincronizzata come evento sul calendario.

### 3. Sito landing

```bash
cd website
npm install
npm run dev
```

Apri http://localhost:5174

## Funzionalità

| Feature | Descrizione |
|---------|-------------|
| Prenotazione guidata | Nome, persone, data, fascia, orario |
| Google Calendar | Eventi automatici con promemoria |
| Lista d'attesa | Notifica quando si libera un tavolo |
| Upsell | Aperitivo, dolce, sake post-conferma |
| Promemoria | T-24h, T-3h con indicazioni stradali |
| Feedback | Richiesta recensione post-pasto |

## Variabili ambiente

Vedi `project/.env.example` per la lista completa.

## Sicurezza

Non committare mai `.env` o `credentials.json`. Se il token Telegram è stato esposto, rigeneralo da [@BotFather](https://t.me/BotFather).
