#!/bin/bash

# Start server
echo "Starting celery beat"
celery -A moviepedia beat -l INFO
