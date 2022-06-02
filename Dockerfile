FROM python:3.8

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY ./src .

EXPOSE 80
ENTRYPOINT ["/app/run.sh"]