#!/bin/bash -x
export WORKSPACE=/home/zeeshan/repos/api.moviepediafilms.com
cd $WORKSPACE
rm $WORKSPACE/api/migrations/0001_initial.py
pipenv run python manage.py makemigrations
pipenv run rm $WORKSPACE/db.sqlite3
pipenv run python manage.py migrate
pipenv run python manage.py loaddata $WORKSPACE/fixtures/backup.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/auth.user.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/authtoken.token.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.role.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.profile.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.package.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.contesttype.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.contest.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.movielanguage.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.moviegenre.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.order.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.movie.json
# pipenv run python manage.py loaddata $WORKSPACE/fixtures/api.crewmember.json
pipenv run black .
