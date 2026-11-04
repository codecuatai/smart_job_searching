FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-eng tesseract-ocr-vie && rm -rf /var/lib/apt/lists/*
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY services/__init__.py services/config.py services/run.py ./services/
COPY services/api ./services/api
# The API indexes the shared skill taxonomy during database startup.
COPY services/ai ./services/ai
COPY services/bi ./services/bi
RUN useradd --create-home appuser && mkdir -p var/data && chown -R appuser:appuser /app
USER appuser
ENV SERVICE_HOST=0.0.0.0
EXPOSE 8000
CMD ["python", "-m", "services.run", "api"]
