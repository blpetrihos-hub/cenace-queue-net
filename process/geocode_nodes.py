"""Map municipio + estado to lat/lon.

The public cola does not publish punto de interconexión. Geography is
the municipality of record. Hand-checked municipal seats live in
process/common.py; everything else falls back to the state centroid.
Unmatched geography is kept and tagged, not dropped.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from process.common import MUNI_COORDS, STATE_COORDS, fold, normalize_muni, normalize_state
ROWS = ROOT / "data" / "processed" / "rows.csv"
GAZ = ROOT / "data" / "gazetteer" / "nodes.csv"


def lookup(muni_key: str, state: str | None) -> tuple[float | None, float | None, str]:
    if state and (muni_key, state) in MUNI_COORDS:
        lat, lon = MUNI_COORDS[(muni_key, state)]
        return lat, lon, "municipio_seat"
    # try without diacritics already folded
    if state:
        for (mk, st), (lat, lon) in MUNI_COORDS.items():
            if st == state and (mk == muni_key or mk in muni_key or muni_key in mk):
                if abs(len(mk) - len(muni_key)) <= 2:
                    return lat, lon, "municipio_seat"
    if state and state in STATE_COORDS:
        lat, lon = STATE_COORDS[state]
        return lat, lon, "state_centroid"
    return None, None, "unlocated"


def main() -> None:
    df = pd.read_csv(ROWS, usecols=["municipio", "municipio_key", "estado", "estado_raw"])
    pairs = (
        df.drop_duplicates(["municipio_key", "estado"])
        .sort_values(["estado", "municipio_key"], na_position="last")
    )
    GAZ.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for rec in pairs.itertuples(index=False):
        state = rec.estado if isinstance(rec.estado, str) and rec.estado else None
        if state is None:
            state = normalize_state(rec.estado_raw)
        key = rec.municipio_key if isinstance(rec.municipio_key, str) else fold(rec.municipio)
        key = normalize_muni(key)
        lat, lon, src = lookup(key, state)
        rows.append(
            {
                "municipio": rec.municipio,
                "municipio_key": key,
                "estado": state or "",
                "lat": lat if lat is not None else "",
                "lon": lon if lon is not None else "",
                "geo_source": src,
            }
        )
    with GAZ.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["municipio", "municipio_key", "estado", "lat", "lon", "geo_source"],
        )
        w.writeheader()
        w.writerows(rows)
    n_un = sum(1 for r in rows if r["geo_source"] == "unlocated")
    n_st = sum(1 for r in rows if r["geo_source"] == "state_centroid")
    n_mu = sum(1 for r in rows if r["geo_source"] == "municipio_seat")
    print("WROTE", GAZ, "pairs", len(rows), "muni", n_mu, "state", n_st, "unlocated", n_un)


if __name__ == "__main__":
    main()
