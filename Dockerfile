FROM python:3.14-slim

# Curl for fastapi healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# This is a path inside the container
WORKDIR /AdsAuction

# in COPY the first path is local and second is inside the container
COPY ./requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY ./app ./app


CMD ["fastapi", "dev", "app/exchange/main.py", "--host", "0.0.0.0", "--port", "8000"]
