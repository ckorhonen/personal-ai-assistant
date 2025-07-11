# syntax=docker/dockerfile:1
FROM python:3.11-alpine
WORKDIR /app
COPY . .
RUN apk add --no-cache build-base && \
    pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]
