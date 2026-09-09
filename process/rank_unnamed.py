"""Rank leftover unnamed load/generation rows and emit search queries.

Does not write ownership.csv. Queries use only fields CENACE publishes.
Do not lead the query with China or the United States.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from process.build_site_data import load
from process.common import BAJIO_FOCUS, NL_FOCUS

OUT_DIR = ROOT / "data" / "processed"
ATTR = ROOT / "data" / "attribution"
EVID = OUT_DIR / "evidence"
CAP = 30


def region_rank(estado: str) -> int:
    if estado in NL_FOCUS:
        return 0
    if estado in BAJIO_FOCUS:
        return 1
    return 2


def cola_rank(cola: str) -> int:
    return 0 if cola == "conexion" else 1


def query_for(row) -> str:
    muni = str(row.municipio or "").strip()
    estado = str(row.estado or "").strip()
    return (
        f'"{muni}" "{estado}" (MW OR megawatt OR "parque industrial") '
        f"(planta OR fábrica) 2022..2026"
    )


def main() -> None:
    df = load()
    snap = str(df["snapshot_date"].max().date())
    q = df[
        (df["snapshot_date"] == pd.Timestamp(snap))
        & (df["in_queue"] == True)  # noqa: E712
        & (df["capacity_outlier"] == False)  # noqa: E712
        & (df["owner_class"].eq("unmatched"))
    ].copy()
    q["region_rank"] = q["estado"].map(region_rank)
    q["cola_rank"] = q["cola_type"].map(cola_rank)
    q["fecha_solicitud"] = pd.to_datetime(q["fecha_solicitud"], errors="coerce")
    q = q.sort_values(
        ["cola_rank", "region_rank", "mw", "fecha_solicitud"],
        ascending=[True, True, False, False],
    )
    top = q.head(CAP).copy()
    rows = []
    EVID.mkdir(parents=True, exist_ok=True)
    ATTR.mkdir(parents=True, exist_ok=True)
    for rec in top.itertuples(index=False):
        qtext = query_for(rec)
        ddg = "https://duckduckgo.com/?q=" + quote_plus(qtext)
        pack = {
            "registro_id": rec.registro_id,
            "cola_type": rec.cola_type,
            "mw": round(float(rec.mw), 3),
            "municipio": rec.municipio if isinstance(rec.municipio, str) else "",
            "estado": rec.estado if isinstance(rec.estado, str) else "",
            "fecha_solicitud": None
            if pd.isna(rec.fecha_solicitud)
            else str(pd.Timestamp(rec.fecha_solicitud).date()),
            "query": qtext,
            "query_url": ddg,
            "suggested_class": "unclear",
            "hits": [],
            "note": (
                "Query only. A hit may be filed here later. It does not color the map "
                "unless a human writes a codebook row that would also pass the uniqueness gate."
            ),
        }
        (EVID / f"query_{rec.registro_id}.json").write_text(
            json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        rows.append(
            {
                "registro_id": rec.registro_id,
                "cola_type": rec.cola_type,
                "mw": round(float(rec.mw), 3),
                "municipio": pack["municipio"],
                "estado": pack["estado"],
                "query": qtext,
                "query_url": ddg,
                "suggested_class": "unclear",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "unnamed_queries.csv", index=False)
    out.to_csv(ATTR / "unnamed_queries.csv", index=False)
    print("snapshot", snap, "unnamed", int(len(q)), "queries", len(out))
    print(out[["registro_id", "cola_type", "mw", "municipio", "estado"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
