FROM python:3.12

WORKDIR /app

COPY requirements/base.txt .

RUN pip install -r base.txt

COPY . .

CMD ["gunicorn","config.wsgi:application","--bind","0.0.0.0:8000"]