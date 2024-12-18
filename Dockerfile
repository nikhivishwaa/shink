FROM python:3.10-slim

# Install system dependencies with OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    libopencv-dev \ 
    build-essential \
    libssl-dev \
    libpq-dev \
    libcurl4-gnutls-dev \
    libexpat1-dev \
    libgl1-mesa-dev\
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install opencv-contrib-python

RUN mkdir /home/app

WORKDIR /home/app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY app/ .

EXPOSE 8080

ENTRYPOINT [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]