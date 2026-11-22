

FROM python:3.14-slim

WORKDIR /app

RUN pip install fastapi pydantic uvicorn

COPY ADX/src/main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

