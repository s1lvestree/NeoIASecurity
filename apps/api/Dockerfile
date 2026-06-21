FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/api/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api ./
COPY apps/streamlit/docs /streamlit-docs
COPY apps/streamlit/data /streamlit-data

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "neotel_api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
