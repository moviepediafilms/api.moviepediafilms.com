#!/bin/bash

# Check deploy
echo "Deploy check"
python manage.py check --deploy

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Create superuser"
    python manage.py createsuperuser --no-input
fi

# Start server
echo "Starting server"
gunicorn --bind 0.0.0.0:80 --access-logfile - --workers 3 --capture-output moviepedia.wsgi:application
