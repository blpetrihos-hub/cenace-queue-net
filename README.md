# CENACE queue net

Diagnostic dashboard of Mexico’s public CENACE interconnection and connection queues. U.S. and PRC-tied projects compete for the same grid. What you can count is **place in line for electricity** (megawatts, municipality, request date, study status)—not industrial-park announcements.

No policy recommendations. Unmatched rows stay unmatched. Ownership is assigned only when a cited, reputable source ties a queue row to a named project.

Live site (GitHub Pages): `https://blpetrihos-hub.github.io/cenace-queue-net/` once Pages is enabled. The repo is **private**; GitHub’s free plan does not allow Pages on private repositories (API 422). Preview locally from `docs/`:

```
python -m http.server 8765
```

Then open `http://127.0.0.1:8765/`. To publish, either make the repo public or use a GitHub plan that includes Pages on private repos, then set Pages source to `/docs` on `main`.

## What the public files actually contain

The 2021–2026 workbooks list registro (SICE / SCCC), dates, status, MW, technology, **municipio**, **entidad federativa**, and GCR. They do **not** list company name or a substation “punto de interconexión.” Mapping is therefore municipal, not bus-level.

Latest snapshot used in v1: 28 February 2026. Directory indexes on cenace.gob.mx return 403; the scraper follows the ASP.NET year dropdown. Filenames require the accented *Interconexión* / *Conexión*.

## Rebuild

```
python scrape/fetch_colas.py
python process/normalize.py
python process/geocode_nodes.py
python process/build_site_data.py
python process/render_bibliography.py
```

Raw files land in `data/raw/` (committed). Tidy CSV is `data/processed/` (gitignored; rebuild from raw). Site JSON is `docs/data/` (committed). Bibliography HTML is generated from `sources/bibliography.yml`.

If GitHub Actions cannot reach CENACE, run the scrape locally. Committed `data/raw` keeps the site reproducible.

## Layout

| Path | Role |
| --- | --- |
| `scrape/fetch_colas.py` | Download XLSX from the CENACE listing; SHA256 log |
| `process/normalize.py` | Standardize columns; `mw_days`; flag MW ≥ 5,000 |
| `process/geocode_nodes.py` | Municipio gazetteer |
| `data/codebook/ownership.csv` | Cited matches only |
| `docs/` | GitHub Pages (Leaflet + Chart.js, no Mapbox token) |
