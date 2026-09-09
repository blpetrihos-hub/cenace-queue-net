"""Propose codebook candidates: announcement → unique in-queue load row.

Does not write ownership.csv. One surviving row in the filing window is
`probable`. Zero rows stay unnamed. Two or more are `contested`.
Dashboard megawatts remain CENACE's even when the seed reports MW.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from process.common import normalize_muni, normalize_state

ROWS = ROOT / "data" / "processed" / "rows.csv"
SEEDS = ROOT / "data" / "seeds" / "announcements.csv"
OUT_DIR = ROOT / "data" / "processed"
ATTR = ROOT / "data" / "attribution"
EVID = OUT_DIR / "evidence"

DAYS_BEFORE = 90
DAYS_AFTER = 540
OUTLIER_MW = 5000.0


def load_latest_load() -> pd.DataFrame:
    rows = pd.read_csv(ROWS, parse_dates=["snapshot_date", "fecha_solicitud"])
    snap = rows["snapshot_date"].max()
    q = rows[
        (rows["snapshot_date"] == snap)
        & (rows["in_queue"] == True)  # noqa: E712
        & (rows["capacity_outlier"] == False)  # noqa: E712
        & (rows["cola_type"] == "conexion")
        & (rows["mw"] < OUTLIER_MW)
    ].copy()
    q["municipio_key"] = q["municipio_key"].fillna("").map(lambda x: str(x).strip())
    q["estado"] = q["estado"].fillna("")
    return q, str(pd.Timestamp(snap).date())


def in_window(fecha, announce: pd.Timestamp) -> bool:
    if pd.isna(fecha):
        return False
    lo = announce - pd.Timedelta(days=DAYS_BEFORE)
    hi = announce + pd.Timedelta(days=DAYS_AFTER)
    ts = pd.Timestamp(fecha)
    return lo <= ts <= hi


def main() -> None:
    cola, snap = load_latest_load()
    seeds = pd.read_csv(SEEDS, dtype=str).fillna("")
    records = []
    collisions = []
    for rec in seeds.itertuples(index=False):
        estado = normalize_state(rec.estado)
        muni = normalize_muni(rec.municipio)
        announce = pd.Timestamp(rec.announce_date)
        sub = cola[(cola["estado"] == estado) & (cola["municipio_key"] == muni)].copy()
        sub = sub[sub["fecha_solicitud"].map(lambda d: in_window(d, announce))]
        n = int(len(sub))
        ids = [str(x) for x in sub["registro_id"].tolist()]
        mws = [round(float(x), 3) for x in sub["mw"].tolist()]
        reported = rec.reported_mw.strip()
        clash = ""
        if n == 1 and reported:
            try:
                rmw = float(reported)
                cmw = mws[0]
                if abs(rmw - cmw) > 0.05:
                    clash = f"seed_reported_mw={rmw}; cenace_mw={cmw}"
            except ValueError:
                clash = "seed_reported_mw_unparsed"
        if n == 1:
            gate = "probable"
        elif n == 0:
            gate = "none"
        else:
            gate = "contested"
        collisions.append(
            {
                "seed_id": rec.seed_id,
                "operator": rec.operator,
                "owner_class": rec.owner_class,
                "municipio_key": muni,
                "estado": estado or "",
                "announce_date": rec.announce_date,
                "n_matches": n,
                "gate": gate,
                "registro_ids": "|".join(ids),
                "cenace_mw": "|".join(str(x) for x in mws),
                "mw_clash": clash,
                "url": rec.url,
                "source_id": rec.source_id,
                "notes": rec.notes,
            }
        )
        if n == 1:
            rid = ids[0]
            cmw = mws[0]
            records.append(
                {
                    "registro_id": rid,
                    "cola_type": "conexion",
                    "seed_id": rec.seed_id,
                    "operator": rec.operator,
                    "owner_class": rec.owner_class,
                    "confidence": "probable",
                    "municipio_key": muni,
                    "estado": estado or "",
                    "announce_date": rec.announce_date,
                    "cenace_mw": cmw,
                    "reported_mw": reported,
                    "mw_clash": clash,
                    "source_id": rec.source_id,
                    "url": rec.url,
                    "n_matches": 1,
                    "promote": "review",
                    "match_note": (
                        f"Only in-queue load row in {rec.municipio}, {rec.estado} "
                        f"inside announce−{DAYS_BEFORE}/+{DAYS_AFTER} days. "
                        "MW from CENACE. Not a confirmed UBO. Human must still write the codebook note."
                    ),
                }
            )
            pack = {
                "registro_id": rid,
                "seed_id": rec.seed_id,
                "gate": "probable",
                "snapshot": snap,
                "operator": rec.operator,
                "owner_class": rec.owner_class,
                "municipio": rec.municipio,
                "estado": rec.estado,
                "announce_date": rec.announce_date,
                "cenace_mw": cmw,
                "reported_mw": reported or None,
                "url": rec.url,
                "source_id": rec.source_id,
                "window_days": {"before": DAYS_BEFORE, "after": DAYS_AFTER},
            }
            EVID.mkdir(parents=True, exist_ok=True)
            (EVID / f"{rid}.json").write_text(
                json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8"
            )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ATTR.mkdir(parents=True, exist_ok=True)
    cand = pd.DataFrame(records)
    coll = pd.DataFrame(collisions)
    cand.to_csv(OUT_DIR / "candidates.csv", index=False)
    coll.to_csv(OUT_DIR / "collisions.csv", index=False)
    cand.to_csv(ATTR / "candidates.csv", index=False)
    coll.to_csv(ATTR / "collisions.csv", index=False)
    print("snapshot", snap)
    print("seeds", len(seeds), "probable", len(cand), "contested", int((coll.gate == "contested").sum()), "none", int((coll.gate == "none").sum()))
    if len(coll):
        print(coll[["seed_id", "gate", "n_matches", "registro_ids"]].to_string(index=False))


if __name__ == "__main__":
    main()
