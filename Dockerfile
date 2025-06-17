# Use the python:3.12-alpine image for a smaller footprint
FROM python:3.12-alpine
RUN apk add --no-cache \
    git \
    build-base \
    libffi-dev \
    openssl-dev \
    ca-certificates
WORKDIR /app
ADD https://raw.githubusercontent.com/procrastinando/mindbloat-bot/main/app.py /app/app.py
CMD ["python", "app.py"]