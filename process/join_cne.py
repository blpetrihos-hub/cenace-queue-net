"""Join unique CNE generation permits onto in-queue CENACE generator rows.

CENACE does not name the applicant. CNE names permisionario, empresa líder,
and país de origen. We join only when estado + rounded MW + tech family is
unique on both sides. Tighter municipio keys win when unique. The hand
codebook is applied later and wins on registro_id.
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
    classify_pais,
    extract_muni_from_address,
    fold,
    normalize_state,
    round_mw,
    tech_family,
)

ROWS = ROOT / "data" / "processed" / "rows.csv"
CNE = ROOT / "data" / "raw" / "cne" / "PermisosdeGeneracionVigentesporModalidad.csv"
OUT = ROOT / "data" / "processed" / "cne_join.csv"
META = ROOT / "data" / "processed" / "cne_join_meta.json"


def _col(df: pd.DataFrame, *needles: str) -> str | None:
    folded = {fold(c): c for c in df.columns}
    for n in needles:
        if n in folded:
            return folded[n]
    for key, orig in folded.items():
        if all(part in key for part in needles[0].split()):
            return orig
    return None


def load_cne() -> pd.DataFrame:
    raw = pd.read_csv(CNE, encoding="utf-8-sig", header=3)
    perm = _col(raw, "permisionario")
    mw = _col(raw, "capacidad autorizada")
    tech = _col(raw, "tecnologia")
    estado = _col(raw, "entidad federativa")
    addr = _col(raw, "direccion")
    lider = _col(raw, "empresa lider")
    pais = _col(raw, "pais de origen")
    num = _col(raw, "numero de permiso")
    estatus = _col(raw, "estado actual")
    keep = {
        "permisionario": perm,
        "mw": mw,
        "tecnologia": tech,
        "estado_raw": estado,
        "direccion": addr,
        "empresa_lider": lider,
        "pais_origen": pais,
        "permiso": num,
        "estado_actual": estatus,
    }
    df = pd.DataFrame({k: raw[v] if v else "" for k, v in keep.items()})
    df["mw"] = pd.to_numeric(df["mw"], errors="coerce")
    df = df[df["mw"].notna() & (df["mw"] > 0)].copy()
    df["estado"] = df["estado_raw"].map(normalize_state)
    df["tech_family"] = df["tecnologia"].map(tech_family)
    df["municipio_key"] = [
        extract_muni_from_address(a, e) for a, e in zip(df["direccion"], df["estado"])
    ]
    df["owner_class"] = df["pais_origen"].map(classify_pais)
    df["mw_key"] = df["mw"].map(lambda x: round_mw(x, 1))
    df["loose"] = df["estado"].fillna("") + "|" + df["mw_key"] + "|" + df["tech_family"]
    df["tight"] = (
        df["municipio_key"].fillna("")
        + "|"
        + df["estado"].fillna("")
        + "|"
        + df["mw_key"]
        + "|"
        + df["tech_family"]
    )
    return df


def load_cola() -> pd.DataFrame:
    rows = pd.read_csv(ROWS, parse_dates=["snapshot_date"])
    snap = rows["snapshot_date"].max()
    q = rows[
        (rows["snapshot_date"] == snap)
        & (rows["cola_type"] == "interconexion")
        & (rows["in_queue"] == True)  # noqa: E712
        & (rows["capacity_outlier"] == False)  # noqa: E712
    ].copy()
    q["tech_family"] = q["tecnologia"].map(tech_family)
    q["mw_key"] = q["mw"].map(lambda x: round_mw(x, 1))
    q["loose"] = q["estado"].fillna("") + "|" + q["mw_key"] + "|" + q["tech_family"]
    q["tight"] = (
        q["municipio_key"].fillna("").astype(str)
        + "|"
        + q["estado"].fillna("")
        + "|"
        + q["mw_key"]
        + "|"
        + q["tech_family"]
    )
    return q


def unique_map(df: pd.DataFrame, key: str, require_muni: bool = False) -> dict:
    counts = df[key].value_counts()
    ok = set(counts[counts == 1].index)
    out = {}
    for rec in df.itertuples(index=False):
        k = getattr(rec, key)
        if k not in ok:
            continue
        if not str(k).replace("|", "").strip():
            continue
        if require_muni and not str(getattr(rec, "municipio_key", "") or "").strip():
            continue
        out[k] = rec
    return out


def owner_name(rec) -> str:
    lider = str(getattr(rec, "empresa_lider", "") or "").strip()
    perm = str(getattr(rec, "permisionario", "") or "").strip()
    if lider and lider.lower() not in {"nan", "none"}:
        return f"{perm} ({lider})" if perm else lider
    return perm


def main() -> None:
    cne = load_cne()
    cola = load_cola()
    cne_tight = unique_map(cne, "tight", require_muni=True)
    cola_tight = unique_map(cola, "tight", require_muni=True)
    cne_loose = unique_map(cne, "loose")
    cola_loose = unique_map(cola, "loose")

    used = set()
    hits = []
    for rec in cola.itertuples(index=False):
        match = None
        how = None
        if rec.tight in cola_tight and rec.tight in cne_tight:
            match = cne_tight[rec.tight]
            how = "tight"
        elif rec.loose in cola_loose and rec.loose in cne_loose:
            match = cne_loose[rec.loose]
            how = "loose"
        if match is None:
            continue
        oc = match.owner_class
        pais = str(match.pais_origen or "").strip()
        if not pais or pais.lower() in {"nan", "none"}:
            continue
        if oc not in {"us", "prc", "mexico", "other"}:
            continue
        rid = rec.registro_id
        if rid in used:
            continue
        used.add(rid)
        hits.append(
            {
                "registro_id": rid,
                "cola_type": "interconexion",
                "owner_class": oc,
                "owner_name": owner_name(match),
                "confidence": "confirmed",
                "source_id": "cne_permisos_csv",
                "match_source": "cne_join",
                "join_key": how,
                "permiso": match.permiso,
                "pais_origen": match.pais_origen,
                "empresa_lider": match.empresa_lider,
                "mw": rec.mw,
            }
        )

    out = pd.DataFrame(hits)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    meta = {
        "cola_in_queue_generators": int(len(cola)),
        "cne_permits": int(len(cne)),
        "joined": int(len(out)),
        "joined_mw": float(out["mw"].sum()) if len(out) else 0.0,
        "by_class": out["owner_class"].value_counts().to_dict() if len(out) else {},
        "by_key": out["join_key"].value_counts().to_dict() if len(out) else {},
    }
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("WROTE", OUT, "n=", len(out), "mw=", round(meta["joined_mw"], 1))
    print(meta["by_class"])


if __name__ == "__main__":
    main()
