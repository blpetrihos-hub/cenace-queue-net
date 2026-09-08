"""Download CNE/CRE public generation-permit CSV.

Source: https://www.cne.gob.mx/da/PermisosdeGeneracionVigentesporModalidad.csv
Writes data/raw/cne/ and a small fetch log.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DEST_DIR = ROOT / "data" / "raw" / "cne"
URL = "https://www.cne.gob.mx/da/PermisosdeGeneracionVigentesporModalidad.csv"
UA = "cenace-queue-net/0.1 (William & Mary GIAS Futures; academic diagnostic scrape)"
TIMEOUT = 90


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = DEST_DIR / "PermisosdeGeneracionVigentesporModalidad.csv"
    r = requests.get(URL, timeout=TIMEOUT, headers={"User-Agent": UA})
    rec = {
        "url": URL,
        "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
        "status": r.status_code,
        "bytes": len(r.content),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(r.content).hexdigest() if r.ok else None,
        "content_type": r.headers.get("Content-Type"),
        "ok": bool(r.ok and len(r.content) > 1000),
    }
    if rec["ok"]:
        dest.write_bytes(r.content)
    log_path = DEST_DIR / "fetch_log.json"
    log_path.write_text(json.dumps([rec], indent=2, ensure_ascii=False), encoding="utf-8")
    print(rec["status"], rec["ok"], rec["bytes"], dest)
    if not rec["ok"]:
        raise SystemExit("CNE permit CSV fetch failed")


if __name__ == "__main__":
    main()
