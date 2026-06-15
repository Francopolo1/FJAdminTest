FROM python:3.12

WORKDIR /app

COPY requirements/ requirements/

RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .

CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py sync_postgres_schema && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
