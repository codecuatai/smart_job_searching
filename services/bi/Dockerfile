FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY services ./services
RUN useradd --create-home appuser
USER appuser
CMD ["python", "-m", "services.bi.main", "--watch"]
