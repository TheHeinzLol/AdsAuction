FROM python:3.14-slim

# This is a path inside the container
WORKDIR /DraftRedis

# in COPY the first path is local and second is inside the container
COPY ../requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .

