"""Download CENACE interconnection and connection queue workbooks.

The listing page is ASP.NET. Year changes are postbacks on
ctl00$ContentPlaceHolder1$DrpAnio. Files live under
/Docs/11_CONEXION/SoliciInterconexionRep/{year}/ and
/Docs/11_CONEXION/SoliciConexionRep/{year}/.

Polite delay between requests. Writes data/raw/ and data/raw/fetch_log.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BASE = "https://www.cenace.gob.mx"
LIST_URL = f"{BASE}/Paginas/SIM/SolicitudConexion.aspx"
UA = "cenace-queue-net/0.1 (William & Mary GIAS Futures; academic diagnostic scrape)"
SLEEP_S = 1.2
TIMEOUT = 90

HIDDEN = (
    "__VIEWSTATE",
    "__VIEWSTATEGENERATOR",
    "__EVENTVALIDATION",
    "__EVENTTARGET",
    "__EVENTARGUMENT",
)


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def hidden_fields(soup: BeautifulSoup) -> dict[str, str]:
    out = {}
    for name in HIDDEN:
        el = soup.find("input", {"name": name})
        if el and el.get("value") is not None:
            out[name] = el["value"]
    return out


def extract_xlsx_links(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".xlsx", ".xls", ".csv")):
            found.append((a.get_text(" ", strip=True) or Path(href).name, urljoin(BASE, href)))
    return found


def list_years(soup: BeautifulSoup) -> list[str]:
    sel = soup.find("select", {"name": "ctl00$ContentPlaceHolder1$DrpAnio"})
    if not sel:
        return ["2026"]
    years = [opt.get("value") for opt in sel.find_all("option") if opt.get("value")]
    return years or ["2026"]


def fetch_year(s: requests.Session, fields: dict[str, str], year: str) -> tuple[str, dict[str, str]]:
    data = dict(fields)
    data["__EVENTTARGET"] = "ctl00$ContentPlaceHolder1$DrpAnio"
    data["__EVENTARGUMENT"] = ""
    data["ctl00$ContentPlaceHolder1$DrpAnio"] = year
    r = s.post(LIST_URL, data=data, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    return r.text, hidden_fields(soup)


def slug_filename(url: str) -> str:
    name = Path(url.split("?")[0]).name
    name = name.replace("ó", "o").replace("Ó", "O")
    name = re.sub(r"[^\w.\-]+", "_", name)
    return name


def download(s: requests.Session, url: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = s.get(url, timeout=TIMEOUT)
    rec = {
        "url": url,
        "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
        "status": r.status_code,
        "bytes": len(r.content),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(r.content).hexdigest() if r.ok else None,
        "content_type": r.headers.get("Content-Type"),
    }
    is_xlsx = r.content[:2] == b"PK"
    is_xls = r.content[:8] == b"\xd0\xcf\x11\xe0"
    not_html = "html" not in (r.headers.get("Content-Type") or "").lower()
    if r.ok and (is_xlsx or is_xls):
        dest.write_bytes(r.content)
        rec["ok"] = True
    elif r.ok and not_html and len(r.content) > 500:
        dest.write_bytes(r.content)
        rec["ok"] = True
    else:
        rec["ok"] = False
    return rec


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    s = session()
    r0 = s.get(LIST_URL, timeout=TIMEOUT)
    r0.raise_for_status()
    soup = BeautifulSoup(r0.text, "lxml")
    fields = hidden_fields(soup)
    years = list_years(soup)
    print("years", years)

    log = []
    seen = set()
    html_by_year = {"2026": r0.text}

    for year in years:
        if year != "2026":
            time.sleep(SLEEP_S)
            html, fields = fetch_year(s, fields, year)
            html_by_year[year] = html
        links = extract_xlsx_links(html_by_year[year])
        print(f"{year}: {len(links)} file(s)")
        for label, url in links:
            if url in seen:
                continue
            seen.add(url)
            dest = RAW / year / slug_filename(url)
            time.sleep(SLEEP_S)
            rec = download(s, url, dest)
            rec["label"] = label
            rec["year"] = year
            log.append(rec)
            print(rec["status"], rec["ok"], rec["bytes"], dest.name)

    log_path = RAW / "fetch_log.json"
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print("WROTE", log_path, "n=", len(log), "ok=", sum(1 for x in log if x.get("ok")))


if __name__ == "__main__":
    main()
