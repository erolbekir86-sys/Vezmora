FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    VEZMORA_DATA_DIR=/data

WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
COPY static ./static
COPY docs ./docs
COPY main.py worker.py ./
RUN pip install --no-cache-dir .
RUN mkdir -p /data && useradd -m -u 10001 vezmora && chown -R vezmora:vezmora /app /data
USER vezmora
EXPOSE 8000
CMD ["python", "main.py"]
