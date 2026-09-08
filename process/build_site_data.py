"""Join codebook + gazetteer; write docs/data JSON for GitHub Pages."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from process.common import BAJIO_FOCUS, NL_FOCUS

ROWS = ROOT / "data" / "processed" / "rows.csv"
GAZ = ROOT / "data" / "gazetteer" / "nodes.csv"
CODE = ROOT / "data" / "codebook" / "ownership.csv"
OUT = ROOT / "docs" / "data"

OWNER_ORDER = ["us", "prc", "mexico", "other", "unmatched"]
OWNER_LABEL = {
    "us": "U.S.",
    "prc": "PRC",
    "mexico": "Mexico",
    "other": "Other",
    "unmatched": "Unmatched",
}


def jitter(lat: float, lon: float, key: str) -> tuple[float, float]:
    h = int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)
    dlat = ((h % 1000) / 1000.0 - 0.5) * 0.08
    dlon = (((h // 1000) % 1000) / 1000.0 - 0.5) * 0.08
    return lat + dlat, lon + dlon


def load() -> pd.DataFrame:
    df = pd.read_csv(ROWS, parse_dates=["fecha_solicitud", "snapshot_date"])
    gaz = pd.read_csv(GAZ)
    gaz = gaz.drop_duplicates(["municipio_key", "estado"])
    df = df.merge(gaz, on=["municipio_key", "estado"], how="left", suffixes=("", "_gaz"))
    if "municipio_gaz" in df.columns:
        df["municipio"] = df["municipio"].fillna(df["municipio_gaz"])
    code = pd.read_csv(CODE, dtype=str).fillna("")
    code["registro_id"] = code["registro_id"].str.strip()
    code = code[code["registro_id"] != ""].drop_duplicates(["registro_id", "cola_type"])
    keep = code[["registro_id", "cola_type", "owner_class", "owner_name", "confidence", "source_id"]]
    df = df.merge(keep, on=["registro_id", "cola_type"], how="left")
    df["owner_class"] = df["owner_class"].fillna("unmatched")
    df["confidence"] = df["confidence"].fillna("unmatched")
    df["owner_name"] = df["owner_name"].fillna("")
    df["source_id"] = df["source_id"].fillna("")
    df.loc[df["owner_class"].eq(""), "owner_class"] = "unmatched"
    return df


def latest_snapshot(df: pd.DataFrame) -> str:
    return str(df["snapshot_date"].max().date())


def agg_mw(sub: pd.DataFrame, col: str = "mw") -> float:
    s = sub.loc[~sub["capacity_outlier"], col].sum()
    return float(s) if pd.notna(s) else 0.0


def chart_block(sub: pd.DataFrame) -> dict:
    by_owner = []
    for k in OWNER_ORDER:
        g = sub[sub["owner_class"] == k]
        by_owner.append(
            {
                "key": k,
                "label": OWNER_LABEL[k],
                "mw": round(agg_mw(g), 3),
                "n": int((~g["capacity_outlier"]).sum()),
            }
        )
    by_status = []
    for st, g in sub.groupby("status_class"):
        by_status.append(
            {
                "key": str(st),
                "mw": round(agg_mw(g), 3),
                "n": int((~g["capacity_outlier"]).sum()),
            }
        )
    wait = sub.loc[sub["in_queue"] & ~sub["capacity_outlier"], "days_in_queue"].dropna()
    mw_days = agg_mw(sub.loc[sub["in_queue"]], "mw_days") if "mw_days" in sub.columns else 0.0
    return {
        "by_owner": by_owner,
        "by_status": by_status,
        "in_queue_mw": round(agg_mw(sub.loc[sub["in_queue"]]), 3),
        "in_queue_n": int(sub.loc[sub["in_queue"] & ~sub["capacity_outlier"]].shape[0]),
        "unmatched_in_queue_mw": round(
            agg_mw(sub.loc[sub["in_queue"] & sub["owner_class"].eq("unmatched")]), 3
        ),
        "median_days_in_queue": float(wait.median()) if len(wait) else None,
        "mw_days_in_queue": round(float(mw_days), 1) if mw_days else 0.0,
        "unlocated_in_queue_mw": round(
            agg_mw(sub.loc[sub["in_queue"] & sub["geo_source"].eq("unlocated")]), 3
        ),
    }


def map_features(latest: pd.DataFrame) -> list[dict]:
    q = latest.loc[latest["in_queue"] & ~latest["capacity_outlier"]].copy()
    features = []
    grouped = q.groupby(
        ["municipio_key", "estado", "lat", "lon", "geo_source", "municipio"],
        dropna=False,
    )
    for (mk, estado, lat, lon, geo, muni), g in grouped:
        if pd.isna(lat) or pd.isna(lon):
            continue
        owners = {}
        for k in OWNER_ORDER:
            owners[k] = round(float(g.loc[g["owner_class"] == k, "mw"].sum()), 3)
        total = round(sum(owners.values()), 3)
        if total <= 0:
            continue
        jlat, jlon = jitter(float(lat), float(lon), f"{mk}|{estado}")
        dominant = max(OWNER_ORDER, key=lambda k: owners[k])
        if owners[dominant] == 0:
            dominant = "unmatched"
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [jlon, jlat]},
                "properties": {
                    "municipio": muni if isinstance(muni, str) else "",
                    "estado": estado if isinstance(estado, str) else "",
                    "geo_source": geo if isinstance(geo, str) else "",
                    "mw": total,
                    "n": int(len(g)),
                    "owner": dominant,
                    "owners": owners,
                    "cola_mix": {
                        "interconexion": round(
                            float(g.loc[g["cola_type"] == "interconexion", "mw"].sum()), 3
                        ),
                        "conexion": round(
                            float(g.loc[g["cola_type"] == "conexion", "mw"].sum()), 3
                        ),
                    },
                    "region": "nuevo_leon"
                    if estado in NL_FOCUS
                    else ("bajio" if estado in BAJIO_FOCUS else "other"),
                },
            }
        )
    return features


def timeseries(df: pd.DataFrame) -> list[dict]:
    out = []
    for snap, g in df.groupby("snapshot_date"):
        rec = {
            "snapshot_date": str(pd.Timestamp(snap).date()),
            "interconexion_in_queue_mw": round(
                agg_mw(g.loc[(g["cola_type"] == "interconexion") & g["in_queue"]]), 3
            ),
            "conexion_in_queue_mw": round(
                agg_mw(g.loc[(g["cola_type"] == "conexion") & g["in_queue"]]), 3
            ),
        }
        for k in OWNER_ORDER:
            rec[f"in_queue_mw_{k}"] = round(
                agg_mw(g.loc[g["in_queue"] & g["owner_class"].eq(k)]), 3
            )
        out.append(rec)
    out.sort(key=lambda x: x["snapshot_date"])
    return out


def open_rows(latest: pd.DataFrame) -> list[dict]:
    q = latest.loc[latest["in_queue"] & ~latest["capacity_outlier"]].copy()
    q = q.sort_values("mw", ascending=False)
    rows = []
    for r in q.itertuples(index=False):
        rows.append(
            {
                "registro_id": r.registro_id,
                "cola_type": r.cola_type,
                "mw": round(float(r.mw), 3),
                "estatus": r.estatus if isinstance(r.estatus, str) else "",
                "tecnologia": r.tecnologia if isinstance(r.tecnologia, str) else "",
                "municipio": r.municipio if isinstance(r.municipio, str) else "",
                "municipio_key": r.municipio_key if isinstance(r.municipio_key, str) else "",
                "estado": r.estado if isinstance(r.estado, str) else "",
                "days_in_queue": int(r.days_in_queue) if pd.notna(r.days_in_queue) else None,
                "owner_class": r.owner_class,
                "owner_name": r.owner_name if isinstance(r.owner_name, str) else "",
                "confidence": r.confidence,
                "source_id": r.source_id if isinstance(r.source_id, str) else "",
                "geo_source": r.geo_source if isinstance(r.geo_source, str) else "",
                "lat": None if pd.isna(getattr(r, "lat", None)) else float(r.lat),
                "lon": None if pd.isna(getattr(r, "lon", None)) else float(r.lon),
                "region": "nuevo_leon"
                if r.estado in NL_FOCUS
                else ("bajio" if r.estado in BAJIO_FOCUS else "other"),
            }
        )
    return rows


def main() -> None:
    df = load()
    snap = latest_snapshot(df)
    latest = df[df["snapshot_date"] == pd.Timestamp(snap)].copy()

    dashboard = {
        "generated_from": "CENACE public colas",
        "latest_snapshot": snap,
        "caption": (
            "Relative position in line for electrons, 2026–2036 clock. "
            "Not an influence score. Unmatched megawatts stay unmatched."
        ),
        "meta": {
            "n_latest": int(len(latest)),
            "n_latest_in_queue": int(latest["in_queue"].sum()),
            "n_codebook_matched": int(
                (latest["owner_class"] != "unmatched").sum()
            ),
            "outlier_mw_excluded": 5000,
        },
        "all": chart_block(latest),
        "interconexion": chart_block(latest[latest["cola_type"] == "interconexion"]),
        "conexion": chart_block(latest[latest["cola_type"] == "conexion"]),
        "nuevo_leon": chart_block(latest[latest["estado"].isin(NL_FOCUS)]),
        "bajio": chart_block(latest[latest["estado"].isin(BAJIO_FOCUS)]),
        "timeseries": timeseries(df),
        "map": {"type": "FeatureCollection", "features": map_features(latest)},
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dashboard.json").write_text(
        json.dumps(dashboard, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "open_rows.json").write_text(
        json.dumps(open_rows(latest), ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE", OUT / "dashboard.json")
    print("map features", len(dashboard["map"]["features"]))
    print("open rows", dashboard["meta"]["n_latest_in_queue"])


if __name__ == "__main__":
    main()
