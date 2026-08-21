FROM python:3.12-slim

WORKDIR /app

# Only these individual files are needed from the repository.
COPY nowhere_bundle.py /tmp/nowhere_bundle.py
RUN python /tmp/nowhere_bundle.py /app && rm -f /tmp/nowhere_bundle.py

COPY bootstrap_high_precision.py /app/bootstrap_high_precision.py
COPY remote.py /app/remote.py

RUN pip install --no-cache-dir "fastmcp==3.4.7" .

# Build the real 0.1-degree global ETOPO1 terrain grid into the image.
# If the source service is unavailable, the build fails instead of silently
# falling back to the low-resolution grid.
RUN python /app/bootstrap_high_precision.py --output /app/nowhere/data/grid.npz

RUN mkdir -p /data /data/tiles

ENV NOWHERE_HOME=/data
ENV NOWHERE_GRID_PATH=/app/nowhere/data/grid.npz
ENV NOWHERE_TILES_DIR=/data/tiles
ENV PORT=8080

EXPOSE 8080
CMD ["python", "/app/remote.py"]
