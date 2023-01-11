#!/bin/bash
set -e 
echo "dev entrypoint"
echo ${@}
python manage.py ${@}
