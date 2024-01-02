FROM python:3.10 as base

RUN pip install --upgrade pip && \
    pip install pipenv

WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy --ignore-pipfile


FROM base as dev
WORKDIR /app
RUN pipenv install --system --deploy --ignore-pipfile --dev
COPY ./src .
CMD ["/app/run-dev.sh"]

FROM base as prod
WORKDIR /app
COPY ./src .
EXPOSE 80
CMD ["/app/run.sh"]