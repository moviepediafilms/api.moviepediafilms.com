#!/bin/bash
HOME=/home/zeeshan/api.moviepediafilms.com
echo "$PATH"
export PATH=/home/zeeshan/.local/bin:$PATH
echo "$PATH"
cd $HOME
pipenv run python manage.py $1
