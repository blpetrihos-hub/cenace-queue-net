# CENACE queue net

Diagnostic dashboard of **who is waiting for Mexico’s grid**, in megawatts and days: U.S. vs PRC vs Mexico vs other vs unnamed. CENACE still does not name the applicant. CNE names generation permit-holders (country of origin); unique fingerprint joins onto in-queue plants are the scoreboard. Factories (load) stay mostly unnamed.

No policy recommendations. Unnamed megawatts stay unnamed. Mixed CNE labels (for example Canada and China) are Other, not PRC. A Mexican company can hide PRC capital; that hole stays on Mexico or unnamed bars.

**Live site:** [https://blpetrihos-hub.github.io/cenace-queue-net/](https://blpetrihos-hub.github.io/cenace-queue-net/)

Preview locally from `docs/`:

```
python -m http.server 8765
```

Then open `http://127.0.0.1:8765/`.

## What the public files actually contain

CENACE 2021–2026 workbooks list registry id (SICE / SCCC), dates, status, MW, technology, **municipality**, **state**, and regional control office. They do **not** list company name or a substation interconnection point. Mapping is municipal, not bus-level.

CNE’s [generation permits in force, by modality](https://www.cne.gob.mx/da/PermisosdeGeneracionVigentesporModalidad.csv) names permit-holder, MW, technology, state, address, lead company, and country of origin. Join is unique-only: state + rounded MW + tech family, unique in both the queue and the permit book.

Latest CENACE snapshot used here: 28 February 2026. Directory indexes on cenace.gob.mx return 403; the scraper follows the ASP.NET year dropdown.

## Rebuild

```
python scrape/fetch_colas.py
python scrape/fetch_cne_permits.py
python process/normalize.py
python process/geocode_nodes.py
python process/join_cne.py
python process/propose_from_seeds.py
python process/rank_unnamed.py
python process/mia_spike.py
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
| `process/propose_from_seeds.py` | Announcement → unique load-row candidates (does not color the map) |
| `process/rank_unnamed.py` | Query URLs for leftover unnamed rows (does not color the map) |
| `process/mia_spike.py` | Confirms SEMARNAT MIA has no official bulk table to join |
| `data/seeds/announcements.csv` | Dated plant seeds (municipio + country class + URL) |
| `data/codebook/ownership.csv` | Cited matches (wins over CNE on the same registro) |
| `docs/` | GitHub Pages (Leaflet + Chart.js) |
