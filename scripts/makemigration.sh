#! /bin/bash
docker build . -t backend
docker run -it --rm \
          -v $(pwd)/src:/app \
          -e MEDIA_ROOT=/tmp/media \
          -e SECRET_KEY=testingsecretkey \
          -e IN_TEST=true \
          -e DEBUG=true \
          -e LOG_PATH=moviepedia.log \
          -e LOG_PATH_JOB=jobs.moviepedia.log \
          -e DATABASE_URL=mysql://readonly:Horse_24_ocean@db.moviepediafilms.com:3306/prod \
 --entrypoint /app/dev-entrypoint.sh backend makemigrations 