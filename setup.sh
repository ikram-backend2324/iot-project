#!/bin/bash
# IoT Analyzer Setup Script

echo "=== IoT Analyzer Setup ==="

# Copy .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — please add your OPENROUTER_API_KEY"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Compile translations
echo "Compiling translations..."
python manage.py compilemessages

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "=== Setup Complete ==="
echo "Run: python manage.py seed           (to create admin + demo data)"
echo "Run: python manage.py seed --reset   (to wipe and re-seed)"
echo "Run: python manage.py runserver      (to start server)"
