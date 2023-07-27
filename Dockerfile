FROM python:3.11

WORKDIR /app

ENV POETRY_VERSION=1.5.1
ENV POETRY_VIRTUALENVS_CREATE=false

COPY echobot.py /app

RUN pip install poetry

COPY pyproject.toml poetry.lock /app
RUN poetry install --no-dev --no-root --no-interaction --no-ansi

CMD ["poetry", "run", "python", "echobot.py"]
