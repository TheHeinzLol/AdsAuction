
FROM python:3.12-slim

WORKDIR /app

COPY SSP/requirements.txt .

#RUN pip install --no-cache-dir -r requirements.txt =====production
RUN pip install -r requirements.txt

COPY SSP/src/ src/

EXPOSE 8000

CMD ["opentelemetry-instrument", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

