FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY choremane_api.py .

EXPOSE 80

CMD ["uvicorn", "choremane_api:app", "--host", "0.0.0.0", "--port", "80"]
