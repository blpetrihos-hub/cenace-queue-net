"""Read every CENACE cola snapshot; emit a tidy parquet/csv of rows.

Public workbooks do not name the applicant. Geography is municipio +
entidad federativa + GCR, not a substation bus. Snapshot date is taken
from the title row ("Información actualizada al: …"), not file mtime.

mw_days = MW × days from fecha de solicitud to that snapshot date.
Rows with MW >= 5000 are flagged as capacity_outlier (unit/typo).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from process.common import (
    classify_status,
    fold,
    normalize_muni,
    normalize_state,
    parse_filename_date,
    parse_spanish_date,
    region_tag,
    titleish,
)

RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUTLIER_MW = 5000.0

COL_MAP = {
    "numero de registro": "registro_id",
    "n mero de registro": "registro_id",
    "fecha de registro solicitud": "fecha_solicitud",
    "estatus": "estatus",
    "fecha estado solicitud": "fecha_estatus",
    "fecha estimada de operacion normal": "fecha_cod",
    "capacidad (mw)": "mw",
    "capacidad mw": "mw",
    "tecnologia": "tecnologia",
    "municipio": "municipio",
    "entidad federativa": "estado_raw",
    "gcr": "gcr",
}


def find_header_row(raw: pd.DataFrame) -> int:
    for i, row in raw.iterrows():
        vals = [fold(x) for x in row.tolist()]
        blob = " ".join(vals)
        if "registro" in blob and "estatus" in blob and "capacidad" in blob:
            return int(i)
    raise ValueError("header row not found")


def snapshot_date(raw: pd.DataFrame, path: Path) -> str:
    head = " ".join(str(x) for x in raw.iloc[: header_safe(raw)].to_numpy().ravel())
    d = parse_spanish_date(head)
    if d is None:
        d = parse_filename_date(path.name)
    if d is None:
        raise ValueError(f"no snapshot date in {path}")
    return d.isoformat()


def header_safe(raw: pd.DataFrame) -> int:
    try:
        return find_header_row(raw)
    except ValueError:
        return 8


def cola_type_from_name(name: str) -> str:
    n = fold(name)
    if "interconexion" in n:
        return "interconexion"
    if "conexion" in n:
        return "conexion"
    return "unknown"


def load_workbook(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None)
    hdr = find_header_row(raw)
    snap = snapshot_date(raw, path)
    listing_year = path.parent.name
    cola_type = cola_type_from_name(path.name)

    df = pd.read_excel(path, header=hdr)
    rename = {}
    for c in df.columns:
        key = fold(c)
        key = key.replace("n mero de registro", "numero de registro")
        key = key.replace("numero de registro", "numero de registro")
        if key.startswith("unnamed"):
            continue
        if key in COL_MAP:
            rename[c] = COL_MAP[key]
    df = df.rename(columns=rename)
    keep = list(dict.fromkeys(c for c in COL_MAP.values() if c in df.columns))
    df = df[keep].copy()

    if "registro_id" not in df.columns or "mw" not in df.columns:
        raise ValueError(f"missing columns in {path}: {list(df.columns)}")

    df["registro_id"] = df["registro_id"].astype(str).str.strip()
    df = df[df["registro_id"].notna() & ~df["registro_id"].isin(["", "nan", "None"])]
    df["mw"] = pd.to_numeric(df["mw"], errors="coerce")
    df = df[df["mw"].notna() & (df["mw"] >= 0)]

    for col in ("fecha_solicitud", "fecha_estatus", "fecha_cod"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    df["snapshot_date"] = snap
    df["listing_year"] = listing_year
    df["cola_type"] = cola_type
    df["source_file"] = str(path.relative_to(ROOT)).replace("\\", "/")
    df["estatus"] = df["estatus"].map(titleish) if "estatus" in df.columns else ""
    df["status_class"] = df["estatus"].map(classify_status)
    df["tecnologia"] = df.get("tecnologia", pd.Series("", index=df.index)).map(
        lambda x: titleish(x) if pd.notna(x) else ""
    )
    df["municipio"] = df.get("municipio", pd.Series("", index=df.index)).map(titleish)
    df["estado_raw"] = df.get("estado_raw", pd.Series("", index=df.index)).map(titleish)
    df["estado"] = df["estado_raw"].map(normalize_state)
    df["municipio_key"] = df["municipio"].map(normalize_muni)
    df["gcr"] = df.get("gcr", pd.Series("", index=df.index)).map(titleish)
    df["region"] = df["estado"].map(region_tag)
    df["capacity_outlier"] = df["mw"] >= OUTLIER_MW

    snap_ts = pd.Timestamp(snap)
    if "fecha_solicitud" in df.columns:
        days = (snap_ts - df["fecha_solicitud"]).dt.days
        days = days.clip(lower=0)
        df["days_in_queue"] = days
        df["mw_days"] = df["mw"] * days
        df.loc[df["capacity_outlier"], "mw_days"] = pd.NA
    else:
        df["days_in_queue"] = pd.NA
        df["mw_days"] = pd.NA

    df["in_queue"] = df["status_class"] == "in_queue"
    df = df.drop_duplicates(
        subset=["registro_id", "snapshot_date", "cola_type"], keep="last"
    )
    return df.reset_index(drop=True)


def main() -> None:
    files = sorted(RAW.rglob("*.xlsx"))
    files = [p for p in files if not p.name.startswith("~$")]
    if not files:
        raise SystemExit("no xlsx under data/raw; run scrape/fetch_colas.py")

    frames = []
    for p in files:
        df = load_workbook(p)
        print(p.name, len(df), df["snapshot_date"].iloc[0], df["cola_type"].iloc[0])
        frames.append(df)

    all_rows = pd.concat(frames, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "rows.csv"
    all_rows.to_csv(csv_path, index=False)
    meta = {
        "n_rows": int(len(all_rows)),
        "n_files": len(files),
        "snapshots": sorted(all_rows["snapshot_date"].unique().tolist()),
        "outlier_mw_threshold": OUTLIER_MW,
        "status_class_counts": all_rows["status_class"].value_counts().to_dict(),
    }
    (OUT / "normalize_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE", csv_path, "n=", len(all_rows))


if __name__ == "__main__":
    main()
