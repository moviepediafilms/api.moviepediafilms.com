#!/bin/bash -x
export WORKSPACE=/home/zeeshan/repos/moviepedia_backend
cd $WORKSPACE
rm $WORKSPACE/api/migrations/0001_initial.py
pipenv run python manage.py makemigrations
pipenv run rm $WORKSPACE/db.sqlite3
pipenv run python manage.py migrate
pipenv run python manage.py loaddata $WORKSPACE/fixtures/basic.json
pipenv run black .
