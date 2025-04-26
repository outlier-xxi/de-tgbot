FROM python:3.12-slim

# Устанавливаем Poetry
RUN pip install poetry==2.1.2

# Отключаем создание виртуального окружения (используем системный Python)
ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости
RUN poetry install --no-root --no-interaction --no-ansi --compile --only main

COPY ./alembic.ini              /app/alembic.ini
COPY ./entrypoint.sh            /app/entrypoint.sh
RUN chmod +x                    /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Копируем остальные файлы проекта
COPY  ./src/                    /app/src

CMD ["python", "/app/src/bot.py"]
