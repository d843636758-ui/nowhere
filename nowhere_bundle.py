#!/usr/bin/env python3
"""Fetch upstream Nowhere and apply our Zeabur/ChatGPT runtime patches.

No DEM or terrain dataset is downloaded during Docker build.
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

UPSTREAM_ZIP = "https://codeload.github.com/yuyixuanfu/nowhere/zip/refs/heads/main"


def _download(url: str, attempts: int = 4, timeout: int = 60) -> bytes:
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Nowhere-Zeabur-Builder/1.0",
                    "Accept": "application/zip,application/octet-stream,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if len(data) < 1000 or data[:2] != b"PK":
                raise RuntimeError(f"unexpected upstream archive: {len(data)} bytes")
            return data
        except Exception as exc:
            last = exc
            print(
                f"upstream download attempt {attempt}/{attempts} failed: {exc}",
                file=sys.stderr,
            )
            if attempt < attempts:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"unable to download upstream Nowhere source: {last}")


def _repo_root(extracted: Path) -> Path:
    if (extracted / "pyproject.toml").exists():
        return extracted
    candidates = [
        p for p in extracted.iterdir()
        if p.is_dir() and (p / "pyproject.toml").exists()
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"could not identify repository root: {candidates}")
    return candidates[0]


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"patch anchor not found: {label}")
    return text.replace(old, new, 1)


def _patch_weather(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    qweather_func = '''async def _try_qweather(lat: float, lon: float) -> dict[str, Any] | None:
    """Try QWeather API. Returns dict on success, None on failure.

    Use the account-specific API Host shown in the QWeather console via
    NOWHERE_QWEATHER_HOST.  The old shared devapi.qweather.com host is not
    reliable for newer accounts.
    """
    key = os.environ.get("NOWHERE_QWEATHER_KEY", "").strip()
    host = os.environ.get("NOWHERE_QWEATHER_HOST", "").strip()
    if not key or not host:
        return None

    host = host.removeprefix("https://").removeprefix("http://").rstrip("/")
    location = f"{lon:.2f},{lat:.2f}"
    url = f"https://{host}/v7/weather/now?location={location}&key={key}"

    data = await providers.fetch_json(url, source="qweather", cache_ttl=300)
    if data is None or str(data.get("code")) != "200":
        return None
    now = data.get("now")
    if not now:
        return None
    try:
        temp = float(now["temp"])
        feels = float(now["feelsLike"])
        # QWeather windSpeed is km/h; Nowhere stores m/s.
        wind = float(now["windSpeed"]) / 3.6
        humidity = float(now["humidity"])
        weather_text = now.get("text", "")
    except (KeyError, ValueError, TypeError):
        return None

    return {
        "temp_c": temp,
        "feels_c": feels,
        "wind_ms": round(wind, 1),
        "humidity": humidity,
        "precip": _precip_from_text(weather_text),
        "text": weather_text,
        "source": "qweather",
    }
'''

    pattern = re.compile(
        r"async def _try_qweather\(.*?\n(?=# ── Open-Meteo)",
        re.S,
    )
    text, count = pattern.subn(qweather_func + "\n", text, count=1)
    if count != 1:
        raise RuntimeError("patch anchor not found: QWeather function")

    if "&wind_speed_unit=ms" not in text:
        text = _replace_once(
            text,
            '        f"precipitation,weather_code,wind_speed_10m"\n',
            '        f"precipitation,weather_code,wind_speed_10m"\n'
            '        f"&wind_speed_unit=ms"\n',
            "Open-Meteo wind unit",
        )

    path.write_text(text, encoding="utf-8")


def _patch_terrain(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    if "import os\n" not in text:
        text = _replace_once(
            text,
            "import math\n",
            "import math\nimport os\n",
            "terrain import os",
        )

    text = _replace_once(
        text,
        '_FULL_PATH: Final = _DATA_DIR / "grid.npz"',
        '_FULL_PATH: Final = pathlib.Path(\n'
        '    os.environ.get("NOWHERE_GRID_PATH", str(_DATA_DIR / "grid.npz"))\n'
        ').expanduser()',
        "NOWHERE_GRID_PATH",
    )

    text = _replace_once(
        text,
        '_TILES_DIR: Final = _DATA_DIR / "tiles"',
        '_TILES_DIR: Final = pathlib.Path(\n'
        '    os.environ.get("NOWHERE_TILES_DIR", str(_DATA_DIR / "tiles"))\n'
        ').expanduser()',
        "NOWHERE_TILES_DIR",
    )

    online_block = '''

# ── Optional online ~90 m elevation cache ──────────────────────────

_ONLINE_ELEVATION_ENABLED: Final = os.environ.get(
    "NOWHERE_ONLINE_ELEVATION", "1"
).strip().lower() not in {"0", "false", "no", "off"}
_ONLINE_ELEVATION_TIMEOUT: Final = float(
    os.environ.get("NOWHERE_ONLINE_ELEVATION_TIMEOUT", "4.0")
)
_ONLINE_ELEVATION_CACHE_MAX: Final = 4096
_online_elev_cache: dict[str, float | None] = {}


def _online_elevation(lat: float, lon: float) -> float | None:
    """Best-effort global elevation lookup via Open-Meteo Copernicus GLO-90."""
    if not _ONLINE_ELEVATION_ENABLED:
        return None

    key = f"{lat:.5f},{lon:.5f}"
    if key in _online_elev_cache:
        return _online_elev_cache[key]

    value: float | None = None
    try:
        import httpx

        response = httpx.get(
            "https://api.open-meteo.com/v1/elevation",
            params={"latitude": f"{lat:.6f}", "longitude": f"{lon:.6f}"},
            timeout=_ONLINE_ELEVATION_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "Nowhere-MCP/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
        values = payload.get("elevation") if isinstance(payload, dict) else None
        if isinstance(values, list) and values and values[0] is not None:
            candidate = float(values[0])
            if math.isfinite(candidate) and -12000.0 <= candidate <= 10000.0:
                value = candidate
    except Exception:
        value = None

    if len(_online_elev_cache) >= _ONLINE_ELEVATION_CACHE_MAX:
        _online_elev_cache.pop(next(iter(_online_elev_cache)))
    _online_elev_cache[key] = value
    return value
'''

    if "def _online_elevation(" not in text:
        text = _replace_once(
            text,
            "    return elev_val, surf_val\n\n# ── Pool override",
            "    return elev_val, surf_val" + online_block + "\n# ── Pool override",
            "online elevation block",
        )

    grid_func = '''def _latlon_to_grid(lat: float, lon: float) -> tuple[float, float]:
    """Convert lat/lon to fractional row/col for the loaded grid."""
    if _elev is not None:
        nrows, ncols = _elev.shape
    elif _cover is not None:
        nrows, ncols = _cover.shape
    else:
        nrows, ncols = 181, 360

    row = (90.0 - lat) * ((nrows - 1) / 180.0)
    col = ((lon + 180.0) % 360.0) * (ncols / 360.0)
    return row, col
'''
    pattern = re.compile(
        r"def _latlon_to_grid\(.*?\n(?=def _bilinear)",
        re.S,
    )
    text, count = pattern.subn(grid_func + "\n", text, count=1)
    if count != 1:
        raise RuntimeError("patch anchor not found: grid scaling")

    old_elevation = '''    # Try high-res tile (trust tile over DEM — tile has better resolution)
    tile = _find_tile(lat, lon)
    if tile is not None:
        elev_val, _ = _tile_bilinear(tile, lat, lon)
        return elev_val
    # Fall back to global grid
'''
    new_elevation = '''    # Prefer a local high-resolution tile when one is installed.
    tile = _find_tile(lat, lon)
    if tile is not None:
        elev_val, _ = _tile_bilinear(tile, lat, lon)
        return elev_val

    # Otherwise use the global ~90 m online DEM.  Failure is harmless: the
    # local grid/DEM path below remains the fallback.
    online_val = _online_elevation(lat, lon)
    if online_val is not None:
        return online_val

    # Fall back to global/local grid.
'''
    if old_elevation in text:
        text = text.replace(old_elevation, new_elevation, 1)
    elif "online_val = _online_elevation(lat, lon)" not in text:
        raise RuntimeError("patch anchor not found: elevation priority")

    path.write_text(text, encoding="utf-8")


def build(dest: Path, source_zip: Path | None = None) -> None:
    archive = source_zip.read_bytes() if source_zip else _download(UPSTREAM_ZIP)
    if archive[:2] != b"PK":
        raise RuntimeError("upstream source is not a ZIP archive")

    with tempfile.TemporaryDirectory(prefix="nowhere-src-") as td:
        tmp = Path(td)
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            zf.extractall(tmp)
        repo = _repo_root(tmp)

        if dest.exists():
            for child in dest.iterdir():
                if child.name == "remote.py":
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        else:
            dest.mkdir(parents=True, exist_ok=True)

        for child in repo.iterdir():
            target = dest / child.name
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)

    _patch_weather(dest / "nowhere" / "weather.py")
    _patch_terrain(dest / "nowhere" / "terrain.py")
    print(f"Nowhere source prepared in {dest}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dest", nargs="?", default="/app")
    parser.add_argument("--source-zip", type=Path, default=None)
    args = parser.parse_args()
    build(Path(args.dest).resolve(), args.source_zip)


if __name__ == "__main__":
    main()
