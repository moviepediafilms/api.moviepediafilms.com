#! /bin/bash
docker build . -t backend
docker run -it --rm -e MEDIA_ROOT=/tmp/media \
          -e SECRET_KEY=testingsecretkey \
          -e IN_TEST=true \
          -e DEBUG=true \
          -e LOG_PATH=moviepedia.log \
          -e LOG_PATH_JOB=jobs.moviepedia.log \
          -e DATABASE_URL=sqlite:///db.sqlite3 \
 --entrypoint "/app/unittest.sh" backend