# IoT Analyzer — AI-Powered IoT Device Analysis

A Django web application that analyzes IoT device performance using AI (via OpenRouter API).

## Features
- 🔐 User registration & login system
- 📡 IoT device management (add, edit, delete, filter)
- 📊 Metric logging with interactive charts
- 🧠 AI-powered device analysis (via OpenRouter - Mistral 7B)
- 🌍 3-language support: English, Russian, Uzbek
- 🎨 Dark cyberpunk UI with Space Mono + Sora fonts
- ⚡ Django Jazzmin admin panel

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# 3. Run migrations
python manage.py migrate

# 4. Compile translations
python manage.py compilemessages

# 5. Create superuser (for admin access)
python manage.py createsuperuser

# 6. Run server
python manage.py runserver
```

Visit: http://127.0.0.1:8000

Admin panel: http://127.0.0.1:8000/admin

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | True/False |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |

## AI Model
Uses `mistralai/mistral-7b-instruct` via OpenRouter — cheap, fast, reliable.
To change model, edit `OPENROUTER_MODEL` in `iot_analyzer/settings.py`.

## Languages
Switch language using the EN / RU / UZ buttons in the top bar.
AI analysis responses are automatically returned in the selected language.

## Project Structure
```
iot_project/
├── iot_analyzer/       # Django project config
├── devices/            # Main app (devices, metrics, AI analysis)
│   ├── models.py       # Device, DeviceMetric, AIAnalysis
│   ├── views.py        # All views
│   ├── ai_service.py   # OpenRouter AI integration
│   ├── templates/      # HTML templates
│   └── ...
├── locale/             # Translation files (en, ru, uz)
├── static/             # Static files
└── requirements.txt
```
