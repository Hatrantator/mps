FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psycopg2-binary alembic

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000