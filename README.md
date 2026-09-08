# CENACE queue net

Diagnostic dashboard of **who is waiting for Mexico’s grid**, in megawatts and days: U.S. vs PRC vs Mexico vs other vs unnamed. CENACE still does not name the applicant. CNE names generation permit-holders (`país de origen`); unique fingerprint joins onto in-queue plants are the scoreboard. Factories (load) stay mostly unnamed.

No policy recommendations. Unnamed megawatts stay unnamed. Mixed CNE labels (e.g. “Canadá y China”) are Other, not PRC. A Mexican company can hide PRC capital; that hole stays on Mexico or unnamed bars.

**Live site:** [https://blpetrihos-hub.github.io/cenace-queue-net/](https://blpetrihos-hub.github.io/cenace-queue-net/)

The dashboard is bilingual (EN | ES). Preview locally from `docs/`:

```
python -m http.server 8765
```

Then open `http://127.0.0.1:8765/`.

## What the public files actually contain

CENACE 2021–2026 workbooks list registro (SICE / SCCC), dates, status, MW, technology, **municipio**, **entidad federativa**, and GCR. They do **not** list company name or a substation “punto de interconexión.” Mapping is municipal, not bus-level.

CNE’s [Permisos de generación vigentes por modalidad](https://www.cne.gob.mx/da/PermisosdeGeneracionVigentesporModalidad.csv) names permisionario, MW, technology, state, address, *empresa líder*, and *país de origen*. Join is unique-only: state + rounded MW + tech family, unique in both the queue and the permit book.

Latest CENACE snapshot used here: 28 February 2026. Directory indexes on cenace.gob.mx return 403; the scraper follows the ASP.NET year dropdown.

## Rebuild

```
python scrape/fetch_colas.py
python scrape/fetch_cne_permits.py
python process/normalize.py
python process/geocode_nodes.py
python process/join_cne.py
python process/build_site_data.py
python process/render_bibliography.py
```

Raw files land in `data/raw/` (committed, including `data/raw/cne/`). Tidy CSV is `data/processed/` (gitignored; rebuild from raw). Site JSON is `docs/data/` (committed). Bibliography HTML is generated from `sources/bibliography.yml`.

If GitHub Actions cannot reach CENACE or CNE, run the scrape locally. Committed `data/raw` keeps the site reproducible.

## Layout

| Path | Role |
| --- | --- |
| `scrape/fetch_colas.py` | Download XLSX from the CENACE listing; SHA256 log |
| `scrape/fetch_cne_permits.py` | Download CNE generation-permit CSV |
| `process/normalize.py` | Standardize columns; `mw_days`; flag MW ≥ 5,000 |
| `process/geocode_nodes.py` | Municipio gazetteer |
| `process/join_cne.py` | Unique fingerprint join onto in-queue generators |
| `data/codebook/ownership.csv` | Cited matches (wins over CNE on the same registro) |
| `docs/` | GitHub Pages (Leaflet + Chart.js, EN/ES toggle) |
