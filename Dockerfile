FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies in one step
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopencv-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

    
RUN mkdir /home/app
WORKDIR /home/app
    
# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir google-cloud-storage
# Create a non-root user for security
RUN useradd -m rider
RUN chown -R rider:rider /home/app
USER rider

EXPOSE 8080
    
COPY app/ .

ENTRYPOINT [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]