FROM python:3.12-slim

WORKDIR /app

# 拉取当前 Nowhere 上游代码并应用我们的补丁。
# 构建阶段不会下载 DEM / 全球地形数据。
COPY nowhere_bundle.py /tmp/nowhere_bundle.py
RUN python /tmp/nowhere_bundle.py /app \
    && rm -f /tmp/nowhere_bundle.py

COPY remote.py /app/remote.py

# 不再强行固定 fastmcp==3.4.7。
# 让 Nowhere 自己的 pyproject.toml 解析兼容版本。
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir . \
    && mkdir -p /data /data/tiles

ENV NOWHERE_HOME=/data
ENV NOWHERE_GRID_PATH=/data/grid.npz
ENV NOWHERE_TILES_DIR=/data/tiles
ENV NOWHERE_ONLINE_ELEVATION=1
ENV NOWHERE_ONLINE_ELEVATION_TIMEOUT=4.0
ENV PORT=8080

EXPOSE 8080

CMD ["python", "/app/remote.py"]
