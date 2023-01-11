#! /bin/bash
echo "make sure to set DATABASE_URL to prod mysql URL"
cd src
DATABASE_URL=sqlite:///db.sqlite3 \
SECRET_KEY=testingsecretkey \
python manage.py makemigrations
