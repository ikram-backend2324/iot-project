# IoT Analyzer — AI-Powered IoT Device Analysis

A Django web application that analyzes IoT device performance using AI (via OpenRouter API).

## Features
- 🔐 User registration & login system
- 📡 IoT device management (add, edit, delete, filter)
- 📊 Metric logging with interactive charts
- 🧠 AI-powered device analysis with rich, multi-section reports + visual health scorecards
- 🧊 Interactive 3D visualizations (Three.js): live network globe, per-device 3D models, animated PC tower
- 🗺️ Maps (Leaflet, dark theme): device fleet map, per-device location, click-to-pick coordinates on the form
- 💻 "Check My PC" — reads browser-available stats (RAM, cores, battery, network, GPU) and runs an AI diagnosis,
     with an optional downloadable Python agent for real CPU temperature / exact RAM / disk usage
- 🌍 3-language support (English, Russian, Uzbek) — translates the entire UI **and** the AI's response language
- 📱 Fully responsive, including the 3D scenes and maps
- 🎨 Dark cyberpunk UI with Space Mono + Sora fonts
- ⚡ Django Jazzmin admin panel

## What's new in this version
- The AI analysis is now rendered as clean, formatted sections (no raw markdown/asterisks) with numbered
  recommendation lists, an anomaly flag, and a colored risk pill — replacing the previous plain-text dump.
- Each analysis returns a machine-readable scorecard (health, performance, reliability, efficiency, security,
  risk) shown as animated score bars.
- Switching the language now also makes the AI respond in that language.

### Optional PC agent
The "Check My PC" page can use a tiny local agent for hardware data the browser can't expose:
```bash
pip install psutil
python iot_pc_agent.py --serve     # then click "Use Local Agent" on the page
# or:  python iot_pc_agent.py       # prints JSON you can inspect
```
The agent only serves data on 127.0.0.1 and uploads nothing by itself.

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
