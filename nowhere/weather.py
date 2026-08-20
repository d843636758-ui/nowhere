"""Weather with three-tier fallback: QWeather -> Open-Meteo -> climate zone.

Never returns None, never raises.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import math
import os
import random
from typing import Any, Final

import httpx

from nowhere import providers

logger = logging.getLogger(__name__)


# ── WMO weather code -> (precip, chinese_text) ─────────────────────

_WMO_MAP: Final[dict[int, tuple[str, str]]] = {
    0: ("none", "晴"),
    1: ("none", "大部晴"),
    2: ("none", "多云"),
    3: ("none", "阴"),
    45: ("none", "雾"),
    48: ("none", "冻雾"),
    51: ("rain", "小毛毛雨"),
    53: ("rain", "毛毛雨"),
    55: ("rain", "大毛毛雨"),
    56: ("rain", "冻毛毛雨"),
    57: ("rain", "冻毛毛雨"),
    61: ("rain", "小雨"),
    63: ("rain", "中雨"),
    65: ("rain", "大雨"),
    66: ("rain", "冻雨"),
    67: ("rain", "大冻雨"),
    71: ("snow", "小雪"),
    73: ("snow", "中雪"),
    75: ("snow", "大雪"),
    77: ("snow", "米雪"),
    80: ("rain", "小阵雨"),
    81: ("rain", "阵雨"),
    82: ("rain", "大阵雨"),
    85: ("snow", "小阵雪"),
    86: ("snow", "大阵雪"),
    95: ("storm", "雷暴"),
    96: ("storm", "雷暴伴冰雹"),
    99: ("storm", "强雷暴伴冰雹"),
}


# ── Climate zone tables ────────────────────────────────────────────

_CLIMATE_TEMP: Final[dict[str, list[float]]] = {
    "equator": [
        27, 27, 27, 27, 27, 27,
        27, 27, 27, 27, 27, 27,
    ],
    "subtropical": [
        15, 16, 19, 23, 27, 30,
        30, 29, 27, 23, 19, 15,
    ],
    "temperate": [
        2, 3, 7, 12, 17, 21,
        23, 22, 18, 12, 7, 3,
    ],
    "subarctic": [
        -15, -13, -5, 3, 10, 15,
        18, 16, 10, 2, -7, -13,
    ],
    "polar": [
        -30, -32, -28, -20, -10, -2,
        0, -2, -10, -20, -28, -30,
    ],
}


def _climate_zone(lat: float) -> str:
    """Map latitude to a climate zone name."""

    abs_lat = abs(lat)

    if abs_lat < 10:
        return "equator"

    if abs_lat < 30:
        return "subtropical"

    if abs_lat < 55:
        return "temperate"

    if abs_lat < 70:
        return "subarctic"

    return "polar"


def _stable_random(
    lat: float,
    lon: float,
    low: float,
    high: float,
) -> float:
    """Return a deterministic pseudo-random float seeded by lat/lon."""

    seed_str = f"{lat:.2f},{lon:.2f}"

    seed = (
        int(
            hashlib.md5(
                seed_str.encode()
            ).hexdigest(),
            16,
        )
        % (2**32)
    )

    return random.Random(seed).uniform(
        low,
        high,
    )


def _climate_fallback(
    lat: float,
    lon: float,
    elevation: float | None = None,
    local_hour: int | None = None,
) -> dict[str, Any]:
    """Offline climate-zone estimate."""

    zone = _climate_zone(lat)

    month = datetime.date.today().month

    if lat < 0:
        month = (
            (month - 1 + 6) % 12
        ) + 1

    temp = _CLIMATE_TEMP[
        zone
    ][month - 1]

    if local_hour is not None:

        amplitude = (
            12.0
            if zone in (
                "equator",
                "subtropical",
            )
            else 8.0
        )

        hour_angle = (
            (local_hour - 5)
            * (2 * math.pi / 24)
        )

        temp += (
            amplitude
            * math.sin(hour_angle)
        )

    if elevation and elevation > 0:

        temp -= (
            elevation
            * 0.0065
        )

    wind = _stable_random(
        lat,
        lon,
        3.0,
        8.0,
    )

    return {
        "temp_c": round(
            temp,
            1,
        ),
        "feels_c": round(
            temp - 2,
            1,
        ),
        "wind_ms": round(
            wind,
            1,
        ),
        "humidity": 60.0,
        "precip": "none",
        "text": "气候估算",
        "source": "climate",
    }


# ── QWeather ───────────────────────────────────────────────────────


def _precip_from_text(
    text: str,
) -> str:
    """Infer precipitation type from Chinese weather description."""

    for kw, precip in [
        ("冰雹", "storm"),
        ("雷", "storm"),
        ("雪", "snow"),
        ("雨", "rain"),
    ]:

        if kw in text:
            return precip

    return "none"


def _qweather_config() -> tuple[str, str]:
    """
    Read QWeather config.

    Prefer Nowhere-specific variables.

    Also accepts the HEFENG_* variables used
    by the standalone weather MCP.
    """

    host = (
        os.environ.get(
            "NOWHERE_QWEATHER_HOST",
            "",
        ).strip()
        or
        os.environ.get(
            "HEFENG_API_HOST",
            "",
        ).strip()
    )

    key = (
        os.environ.get(
            "NOWHERE_QWEATHER_KEY",
            "",
        ).strip()
        or
        os.environ.get(
            "HEFENG_API_KEY",
            "",
        ).strip()
    )

    host = (
        host
        .removeprefix(
            "https://"
        )
        .removeprefix(
            "http://"
        )
        .rstrip("/")
    )

    return host, key


async def _try_qweather(
    lat: float,
    lon: float,
) -> dict[str, Any] | None:
    """
    Try QWeather.

    Uses the account-specific API Host
    and X-QW-Api-Key authentication.
    """

    host, key = (
        _qweather_config()
    )

    if not host or not key:

        logger.warning(
            "QWeather skipped: "
            "missing host/key. "
            "Set "
            "NOWHERE_QWEATHER_HOST + "
            "NOWHERE_QWEATHER_KEY "
            "or "
            "HEFENG_API_HOST + "
            "HEFENG_API_KEY."
        )

        return None

    url = (
        f"https://{host}"
        "/v7/weather/now"
    )

    params = {
        "location": (
            f"{lon:.2f},"
            f"{lat:.2f}"
        ),
        "lang": "zh",
        "unit": "m",
    }

    headers = {
        "X-QW-Api-Key": key,
        "Accept-Encoding": "gzip",
        "User-Agent": (
            "nowhere-mcp/0.1"
        ),
    }

    try:

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(
                8.0
            ),
            headers=headers,
        ) as client:

            response = (
                await client.get(
                    url,
                    params=params,
                )
            )

        if response.status_code != 200:

            logger.warning(
                "QWeather HTTP error: "
                "status=%s body=%s",
                response.status_code,
                response.text[:300],
            )

            return None

        data = response.json()

    except Exception as exc:

        logger.warning(
            "QWeather request failed: %s",
            exc,
        )

        return None

    if str(
        data.get("code")
    ) != "200":

        logger.warning(
            "QWeather API error: "
            "code=%s",
            data.get("code"),
        )

        return None

    now = data.get("now")

    if not now:

        logger.warning(
            "QWeather response "
            "missing 'now' field"
        )

        return None

    try:

        temp = float(
            now["temp"]
        )

        feels = float(
            now["feelsLike"]
        )

        # QWeather windSpeed is km/h.
        # Nowhere uses m/s.
        wind = (
            float(
                now["windSpeed"]
            )
            / 3.6
        )

        humidity = float(
            now["humidity"]
        )

        text = str(
            now.get(
                "text",
                "",
            )
        )

    except (
        KeyError,
        ValueError,
        TypeError,
    ) as exc:

        logger.warning(
            "QWeather response "
            "parse failed: %s",
            exc,
        )

        return None

    return {
        "temp_c": temp,
        "feels_c": feels,
        "wind_ms": round(
            wind,
            1,
        ),
        "humidity": humidity,
        "precip": (
            _precip_from_text(
                text
            )
        ),
        "text": text,
        "source": "qweather",
    }


# ── Open-Meteo ─────────────────────────────────────────────────────


async def _try_openmeteo(
    lat: float,
    lon: float,
) -> dict[str, Any] | None:
    """Try Open-Meteo free API."""

    url = (
        "https://api.open-meteo.com"
        "/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&current="
        "temperature_2m,"
        "relative_humidity_2m,"
        "apparent_temperature,"
        "precipitation,"
        "weather_code,"
        "wind_speed_10m"
        "&wind_speed_unit=ms"
    )

    data = await providers.fetch_json(
        url,
        source="openmeteo",
        cache_ttl=300,
    )

    if data is None:
        return None

    cur = data.get(
        "current"
    )

    if not cur:
        return None

    try:

        temp = float(
            cur["temperature_2m"]
        )

        feels = float(
            cur["apparent_temperature"]
        )

        humidity = float(
            cur[
                "relative_humidity_2m"
            ]
        )

        wind = float(
            cur["wind_speed_10m"]
        )

        code = int(
            cur["weather_code"]
        )

        precip_val = float(
            cur.get(
                "precipitation",
                0,
            )
        )

    except (
        KeyError,
        ValueError,
        TypeError,
    ):

        return None

    precip_type, text = (
        _WMO_MAP.get(
            code,
            (
                "none",
                "未知",
            ),
        )
    )

    if (
        precip_type == "none"
        and precip_val > 0
    ):

        precip_type = "rain"
        text = "降水"

    return {
        "temp_c": temp,
        "feels_c": feels,
        "wind_ms": wind,
        "humidity": humidity,
        "precip": precip_type,
        "text": text,
        "source": "openmeteo",
    }


# ── Public API ─────────────────────────────────────────────────────


async def current(
    lat: float,
    lon: float,
    elevation: float | None = None,
    local_hour: int | None = None,
) -> dict[str, Any]:
    """
    Return weather at lat/lon.

    Fallback chain:

    QWeather
    -> Open-Meteo
    -> offline climate estimate
    """

    try:

        qweather = (
            await _try_qweather(
                lat,
                lon,
            )
        )

        if qweather is not None:
            return qweather

    except Exception as exc:

        logger.warning(
            "QWeather unexpected "
            "failure: %s",
            exc,
        )

    try:

        openmeteo = (
            await _try_openmeteo(
                lat,
                lon,
            )
        )

        if openmeteo is not None:
            return openmeteo

    except Exception as exc:

        logger.warning(
            "Open-Meteo unexpected "
            "failure: %s",
            exc,
        )

    return _climate_fallback(
        lat,
        lon,
        elevation=elevation,
        local_hour=local_hour,
    )
