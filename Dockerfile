# Use Python 3.10 as base
FROM python:3.10-bullseye as base

# set working directory
WORKDIR /app

# set PYTHONPATH to include the working directory
ENV PYTHONPATH=/app

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxss1 \
    xdg-utils \
    chromium \
    chromium-sandbox \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Chromium path
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# install claude code cli
RUN curl -fsSL https://claude.ai/install.sh | bash

# copy requirements file
COPY requirements.txt .

# install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy core directory
COPY core/ ./core

# copy api directory
COPY api/ ./api

# copy claude skills directory
COPY .claude ./.claude

# copy _base directory
COPY _base/ ./_base

# copy .env file
COPY .env .

# copy config.yaml file
COPY config.yaml .

# backend target
FROM base as backend

# expose port 8000
EXPOSE 8000

# create start script
RUN echo '#!/bin/sh\nmkdir -p /app/temp && \nuvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 8' > /app/start.sh

RUN chmod +x /app/start.sh

# start server
CMD ["/bin/sh", "/app/start.sh"]

# celery target
FROM base as celery

# create temp directory for celery tasks
RUN mkdir -p /app/temp

# start celery worker
CMD ["celery", "-A", "api.core.celery", "worker", "--loglevel=info"]