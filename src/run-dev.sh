#!/bin/bash

# static files
echo "running dev server"
python manage.py collectstatic --noinput

python manage.py runserver 0.0.0.0:8000
