#! /bin/bash
# script to deploy api.moviepediafilms.com from local system
# ssh keys should be set up already

# variable used
SERVER=moviepediafilms.com
WORKING_DIR=/home/zeeshan/api.moviepediafilms.com
USER=zeeshan
# commands user
pipenv=/home/zeeshan/.local/bin/pipenv
git=/usr/bin/git
ssh=/usr/bin/ssh
service=/usr/sbin/service

$ssh $USER@$SERVER "
cd $WORKING_DIR &&
echo $git pull; $git pull &&
echo $pipenv clean; $pipenv clean &&
echo $pipenv sync; $pipenv sync &&
echo $pipenv run python manage.py check --deploy; $pipenv run python manage.py check --deploy &&
echo $pipenv run python manage.py collectstatic --noinput; $pipenv run python manage.py collectstatic --noinput &&
echo $pipenv run python manage.py migrate --noinput; $pipenv run python manage.py migrate --noinput &&
echo sudo $service api.moviepediafilms restart; sudo $service api.moviepediafilms restart"
