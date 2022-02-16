FROM python:3.8

RUN pip install --upgrade pip
RUN pip install pipenv

WORKDIR /app

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy --system

COPY ./src .

EXPOSE 80
ENTRYPOINT ["/app/run.sh"]