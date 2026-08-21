#!/usr/bin/env python3
"""Build the real 0.1° global ETOPO1 grid used by Nowhere.

The source is an ERDDAP 1-arc-minute ETOPO1 dataset sampled every 6 cells,
so the download is already 0.1° (1801 x 3600) instead of the full ~377 MB
compressed source archive. The output is a compact grid.npz for runtime use.
"""
from __future__ import annotations

import argparse
import os
import tempfile
import urllib.request
from pathlib import Path

import numpy as np

ERDDAP_URL = (
    "https://pae-paha.pacioos.hawaii.edu/erddap/griddap/"
    "etopo1_ice.nc?z[0:6:10800][0:6:21594]"
)

WATER_OCEAN = 0
WATER_FRESH = 1
ROCK = 2
SAND = 3
SNOW = 4
ICE = 5
FOREST = 6
GRASS = 7
URBAN = 8
BARE = 9
WETLAND = 10


def _classify(elev: np.ndarray) -> np.ndarray:
    nlats, nlons = elev.shape
    lats = np.linspace(90.0, -90.0, nlats, dtype=np.float32)
    lons = np.linspace(-180.0, 179.9, nlons, dtype=np.float32)
    lat_grid = np.broadcast_to(lats[:, None], elev.shape)
    lon_grid = np.broadcast_to(lons[None, :], elev.shape)

    cover = np.full(elev.shape, GRASS, dtype=np.uint8)
    water = elev < 0
    cover[water] = WATER_OCEAN

    ice = (np.abs(lat_grid) > 66) & ~water
    cover[ice] = ICE

    rock = (elev > 3500) & ~water & ~ice
    cover[rock] = ROCK

    snow = (np.abs(lat_grid) > 55) & (elev < 800) & ~water & ~ice & ~rock
    cover[snow] = SNOW

    sahara = (
        (lat_grid >= 15) & (lat_grid <= 33)
        & (lon_grid >= -18) & (lon_grid <= 38)
        & (elev < 1500)
    )
    middle_east = (
        (lat_grid >= 12) & (lat_grid <= 32)
        & (lon_grid >= 35) & (lon_grid <= 60)
        & (elev < 1500)
    )
    australia = (
        (lat_grid >= -35) & (lat_grid <= -18)
        & (lon_grid >= 120) & (lon_grid <= 150)
        & (elev < 800)
    )
    gobi = (
        (lat_grid >= 40) & (lat_grid <= 48)
        & (lon_grid >= 90) & (lon_grid <= 115)
        & (elev < 1500)
    )
    desert = (sahara | middle_east | australia | gobi) & ~water & ~ice & ~rock & ~snow
    cover[desert] = SAND

    remaining = ~(water | ice | rock | snow | desert)
    cover[remaining & (np.abs(lat_grid) < 45)] = FOREST
    cover[remaining & (np.abs(lat_grid) >= 45)] = GRASS
    return cover


def _read_erddap_netcdf(path: Path) -> np.ndarray:
    from scipy.io import netcdf_file

    with netcdf_file(str(path), mode="r", mmap=False) as nc:
        z = np.array(nc.variables["z"][:], dtype=np.float32, copy=True)
        lat = np.array(nc.variables["latitude"][:], dtype=np.float64, copy=True)
        lon = np.array(nc.variables["longitude"][:], dtype=np.float64, copy=True)

    if z.shape != (1801, 3600):
        raise RuntimeError(f"unexpected ETOPO subset shape: {z.shape}, expected (1801, 3600)")
    if lat[0] > lat[-1]:
        # Runtime grid expects north-to-south rows; already correct if descending.
        elev = z
    else:
        elev = z[::-1].copy()
    # ERDDAP query intentionally stops at 179.9, so there is no duplicate +180 column.
    if lon.size != 3600:
        raise RuntimeError(f"unexpected longitude size: {lon.size}")
    return elev


def build(output: Path, source_file: Path | None = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.stat().st_size > 1_000_000:
        print(f"High-precision grid already exists: {output}")
        return

    temp_path: Path | None = None
    try:
        if source_file is None:
            fd, name = tempfile.mkstemp(prefix="etopo1_0p1_", suffix=".nc")
            os.close(fd)
            temp_path = Path(name)
            req = urllib.request.Request(
                ERDDAP_URL,
                headers={"User-Agent": "Nowhere-MCP/1.0 high-precision bootstrap"},
            )
            print("Downloading real ETOPO1 0.1° subset from ERDDAP...")
            with urllib.request.urlopen(req, timeout=180) as response, temp_path.open("wb") as f:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            source_file = temp_path
            print(f"Downloaded {source_file.stat().st_size / 1024 / 1024:.1f} MB")

        elev = _read_erddap_netcdf(source_file)
        elev = np.nan_to_num(elev, nan=0.0, posinf=9000.0, neginf=-11000.0)
        elev = np.clip(elev, -11000, 9000)
        cover = _classify(elev)
        elev_i16 = elev.astype(np.int16)

        # Sanity checks at a few canonical locations.
        def rc(lat: float, lon: float) -> tuple[int, int]:
            r = int(round((90.0 - lat) * 10))
            c = int(round((lon + 180.0) * 10)) % 3600
            return r, c

        er, ec = rc(27.9881, 86.9250)
        dr, dc = rc(31.5, 35.5)
        orow, ocol = rc(0.0, -30.0)
        if elev_i16[er, ec] < 4500:
            raise RuntimeError(f"Everest sanity check failed: {elev_i16[er, ec]} m")
        if elev_i16[dr, dc] > -250:
            raise RuntimeError(f"Dead Sea sanity check failed: {elev_i16[dr, dc]} m")
        if cover[orow, ocol] != WATER_OCEAN:
            raise RuntimeError("Atlantic Ocean surface sanity check failed")

        np.savez_compressed(output, elev=elev_i16, cover=cover)
        print(f"Saved high-precision grid: {output} ({output.stat().st_size / 1024 / 1024:.1f} MB)")
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="/app/nowhere/data/grid.npz")
    parser.add_argument("--source-file", default=None)
    parser.add_argument("--print-url", action="store_true")
    args = parser.parse_args()
    if args.print_url:
        print(ERDDAP_URL)
        return
    build(Path(args.output), Path(args.source_file) if args.source_file else None)


if __name__ == "__main__":
    main()
