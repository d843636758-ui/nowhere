FROM python:3.12-slim

WORKDIR /app

# Pull the current upstream Nowhere source, then apply our small runtime patches.
# Important: no DEM / terrain dataset is downloaded during image build.
COPY nowhere_bundle.py /tmp/nowhere_bundle.py
RUN python /tmp/nowhere_bundle.py /app && rm -f /tmp/nowhere_bundle.py

COPY remote.py /app/remote.py

RUN pip install --no-cache-dir "fastmcp==3.4.7" . \
    && mkdir -p /data /data/tiles

ENV NOWHERE_HOME=/data
ENV NOWHERE_GRID_PATH=/data/grid.npz
ENV NOWHERE_TILES_DIR=/data/tiles
ENV NOWHERE_ONLINE_ELEVATION=1
ENV NOWHERE_ONLINE_ELEVATION_TIMEOUT=4.0
ENV PORT=8080

EXPOSE 8080
CMD ["python", "/app/remote.py"]
