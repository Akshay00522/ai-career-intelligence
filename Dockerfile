FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt requirements-api.txt requirements-ui.txt ./
RUN pip install --no-cache-dir -r requirements-ui.txt

COPY src ./src
COPY ui ./ui
COPY data ./data
COPY cli.py ./

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000 8501
# Default: the API. docker-compose overrides the command for the UI.
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
