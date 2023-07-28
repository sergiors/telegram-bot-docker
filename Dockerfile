FROM python:3.11

ENV POETRY_VERSION=1.5.1
ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-root --no-interaction --no-ansi

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

CMD ["./docker-entrypoint.sh"]
