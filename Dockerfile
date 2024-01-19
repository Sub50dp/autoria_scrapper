FROM python:3.8-slim


RUN apt-get update && apt-get install -y libpq-dev gcc wget
RUN apt-get install -y fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcairo2 libcups2
RUN apt-get install -y libcurl4 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0
RUN apt-get install -y libu2f-udev libvulkan1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils


RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb && \
    apt-get install -f -y && \
    rm google-chrome-stable_current_amd64.deb

RUN apt-get install -y postgresql-client

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY scrapper.py /app/scrapper.py

