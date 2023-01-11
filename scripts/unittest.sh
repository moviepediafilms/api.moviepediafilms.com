#! /bin/bash
# docker build . -t backend
# source $PWD/venv/local/bin/activate
mkdir /tmp/media
cd src


MEDIA_ROOT=/tmp/media \
SECRET_KEY=testingsecretkey \
IN_TEST=true \
DEBUG=true \
LOG_LEVEL=DEBUG \
DATABASE_URL=sqlite:///db.sqlite3 \
coverage run --source='.' manage.py test api.tests &&\
coverage html -d ../htmlcov --omit=moviepedia/*,manage.py,api/migrations/*,api/tests/*
rm -rf /tmp/media