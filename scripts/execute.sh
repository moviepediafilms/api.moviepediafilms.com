#!/bin/bash
export PATH=/home/zeeshan/.local/bin:$PATH
pipenv run python manage.py $1
