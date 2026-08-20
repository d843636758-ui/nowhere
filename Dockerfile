FROM python:3.12-slim

WORKDIR /app

RUN echo "=== NOWHERE BUILD ==="

COPY . /app

RUN pip install --no-cache-dir "fastmcp==3.4.5" .

RUN mkdir -p /data

ENV NOWHERE_HOME=/data
ENV PORT=8080

EXPOSE 8080

CMD ["python", "/app/remote.py"]
