"""Spike: can SEMARNAT MIA/Gaceta be joined like the CNE permit CSV?

Official Gaceta Ecológica is a weekly PDF list, not a bulk table of
promoter + MW + municipio. Consulta tu trámite is one-project lookup.
A third-party GitHub scrape exists; we do not join unofficial copies.
Conclusion: no automation. Use MIA PDFs only as citations inside a
human codebook note.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ATTR = ROOT / "data" / "attribution"
OUT = ROOT / "data" / "processed"

GACETA = "https://www.gob.mx/semarnat/acciones-y-programas/gaceta-ecologica"
CONSULTA = "http://tramites.semarnat.gob.mx/index.php/consulta-tu-tramite"
CSV_PROBE = "https://www.cne.gob.mx/da/PermisosdeGeneracionVigentesporModalidad.csv"


def head(url: str, timeout: int = 20) -> dict:
    rec = {"url": url, "ok": False, "status": None, "content_type": "", "note": ""}
    try:
        req = Request(url, method="GET", headers={"User-Agent": "cenace-queue-net/mia-spike"})
        with urlopen(req, timeout=timeout) as resp:
            rec["ok"] = 200 <= getattr(resp, "status", 200) < 400
            rec["status"] = getattr(resp, "status", 200)
            rec["content_type"] = resp.headers.get("Content-Type", "")
            rec["note"] = "reached"
    except Exception as exc:  # noqa: BLE001
        rec["note"] = type(exc).__name__ + ": " + str(exc)[:200]
    return rec


def main() -> None:
    gaceta = head(GACETA)
    consulta = head(CONSULTA)
    cne = head(CSV_PROBE)
    result = {
        "official_bulk_mia_table": False,
        "reason": (
            "SEMARNAT publishes Gaceta Ecológica as weekly PDF listings and a "
            "per-clue 'Consulta tu trámite' lookup. There is no official CSV of "
            "promoter + MW + municipio comparable to CNE's generation-permit file. "
            "Third-party GitHub scrapes are not an official table and are not joined."
        ),
        "automate_join": False,
        "use_mia_as": "citation inside Method 1 codebook notes, one PDF at a time",
        "probes": {"gaceta": gaceta, "consulta": consulta, "cne_csv_control": cne},
    }
    ATTR.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    (ATTR / "mia_spike.json").write_text(text, encoding="utf-8")
    (OUT / "mia_spike.json").write_text(text, encoding="utf-8")
    print("automate_join", result["automate_join"])
    print(result["reason"])


if __name__ == "__main__":
    main()
