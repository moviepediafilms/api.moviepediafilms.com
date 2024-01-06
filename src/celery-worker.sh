#!/bin/bash

# Start server
echo "Starting celery worker"
celery -A moviepedia worker -l INFO --beat

