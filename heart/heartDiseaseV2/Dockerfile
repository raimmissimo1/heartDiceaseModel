FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --default-timeout=300 --retries 10 --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 1111

CMD ["gunicorn", "-b", "0.0.0.0:1111", "app:app"]
