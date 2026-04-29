FROM python:3.12-slim

WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m app.scripts.create_admin && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
