FROM python:3.12-slim

WORKDIR /app

# 先拉作者当前最新 main，并应用我们已经有的
# QWeather / terrain / Zeabur 适配。
COPY nowhere_bundle.py /tmp/nowhere_bundle.py

RUN python /tmp/nowhere_bundle.py /app \
    && rm -f /tmp/nowhere_bundle.py


# 再做条件式兼容补丁。
# 作者已经修复 -> 什么都不改。
# 作者仍缺变量 -> 自动补上。
COPY hotfix_nowhere.py /tmp/hotfix_nowhere.py

RUN python /tmp/hotfix_nowhere.py \
    && python -m compileall -q /app/nowhere \
    && rm -f /tmp/hotfix_nowhere.py


# 我们自己的 ChatGPT / Zeabur HTTP 入口。
COPY remote.py /app/remote.py


# 不再锁死 FastMCP patch 版本。
# 让当前 Nowhere 的 pyproject.toml 自己解析兼容依赖。
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir . \
    && mkdir -p /data /data/tiles


ENV NOWHERE_HOME=/data
ENV NOWHERE_GRID_PATH=/data/grid.npz
ENV NOWHERE_TILES_DIR=/data/tiles

# 高精度高程：运行时按需查询约 90m 数据，
# 网络失败时自动回退本地 terrain。
ENV NOWHERE_ONLINE_ELEVATION=1
ENV NOWHERE_ONLINE_ELEVATION_TIMEOUT=4.0

ENV PORT=8080

EXPOSE 8080

CMD ["python", "/app/remote.py"]
