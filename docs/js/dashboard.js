const COLORS = {
  us: "#2f5d73",
  prc: "#8c3a2b",
  mexico: "#3d6b4f",
  other: "#6b5a3e",
  unmatched: "#8a9096",
};
const LABELS = {
  us: "U.S.",
  prc: "PRC",
  mexico: "Mexico",
  other: "Other",
  unmatched: "Unmatched",
};
const OWNER_ORDER = ["us", "prc", "mexico", "other", "unmatched"];

let DATA = null;
let ROWS = null;
let map = null;
let layer = null;
let chartOwner = null;
let chartStatus = null;
let chartTime = null;

function $(id) {
  return document.getElementById(id);
}

function selected() {
  return {
    clock: $("clock").value,
    cola: $("cola").value,
    region: $("region").value,
    unmatched: $("unmatched").value,
  };
}

function filterRows() {
  const s = selected();
  return ROWS.filter((r) => {
    if (s.cola !== "all" && r.cola_type !== s.cola) return false;
    if (s.region !== "all" && r.region !== s.region) return false;
    if (s.unmatched === "exclude" && r.owner_class === "unmatched") return false;
    return true;
  });
}

function sumMw(rows) {
  return rows.reduce((a, r) => a + (r.mw || 0), 0);
}

function fmtMw(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + " GW";
  return n.toFixed(0) + " MW";
}

function renderStats(rows) {
  const unmatched = rows.filter((r) => r.owner_class === "unmatched");
  const classified = rows.filter((r) => r.owner_class !== "unmatched");
  const days = rows.map((r) => r.days_in_queue).filter((d) => d != null).sort((a, b) => a - b);
  const median = days.length ? days[Math.floor(days.length / 2)] : null;
  const unlocated = rows.filter((r) => r.geo_source === "unlocated" || r.lat == null);
  const html = [
    ["In-queue MW", fmtMw(sumMw(rows))],
    ["Requests", String(rows.length)],
    ["Unmatched MW", fmtMw(sumMw(unmatched))],
    ["Classified MW", fmtMw(sumMw(classified))],
    ["Median days in queue", median == null ? "—" : String(median)],
    ["Unlocated MW", fmtMw(sumMw(unlocated))],
  ]
    .map(([k, v]) => `<div class="stat"><b>${v}</b><span>${k}</span></div>`)
    .join("");
  $("stats").innerHTML = html;
}

function ownerCounts(rows) {
  return OWNER_ORDER.map((k) => ({
    key: k,
    label: LABELS[k],
    mw: sumMw(rows.filter((r) => r.owner_class === k)),
  }));
}

function destroyChart(c) {
  if (c) c.destroy();
}

function renderOwner(rows) {
  const counts = ownerCounts(rows);
  destroyChart(chartOwner);
  chartOwner = new Chart($("chartOwner"), {
    type: "bar",
    data: {
      labels: counts.map((c) => c.label),
      datasets: [
        {
          label: "MW",
          data: counts.map((c) => c.mw),
          backgroundColor: counts.map((c) => COLORS[c.key]),
        },
      ],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: { x: { title: { display: true, text: "MW in queue" } } },
    },
  });
}

function renderStatus(rows) {
  const by = {};
  rows.forEach((r) => {
    const k = r.estatus || "—";
    by[k] = (by[k] || 0) + r.mw;
  });
  const labels = Object.keys(by);
  destroyChart(chartStatus);
  chartStatus = new Chart($("chartStatus"), {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "MW", data: labels.map((k) => by[k]), backgroundColor: "#2f5d73" }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { title: { display: true, text: "MW" } } },
    },
  });
}

function renderTime() {
  const s = selected();
  const ts = DATA.timeseries || [];
  const labels = ts.map((t) => t.snapshot_date);
  let dataset;
  if (s.cola === "interconexion") {
    dataset = { label: "Interconexión in queue", data: ts.map((t) => t.interconexion_in_queue_mw) };
  } else if (s.cola === "conexion") {
    dataset = { label: "Conexión in queue", data: ts.map((t) => t.conexion_in_queue_mw) };
  } else {
    dataset = {
      label: "In-queue MW",
      data: ts.map((t) => t.interconexion_in_queue_mw + t.conexion_in_queue_mw),
    };
  }
  destroyChart(chartTime);
  chartTime = new Chart($("chartTime"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          ...dataset,
          borderColor: "#1b3a4b",
          backgroundColor: "rgba(27,58,75,0.12)",
          fill: true,
          tension: 0.15,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { title: { display: true, text: "MW" } } },
    },
  });
}

function radiusFor(mw) {
  return 6 + Math.sqrt(Math.max(mw, 0)) * 0.55;
}

function renderMap(rows) {
  if (!map) {
    map = L.map("map").setView([23.6, -102.5], 5);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      subdomains: "abcd",
      maxZoom: 18,
    }).addTo(map);
  }
  if (layer) {
    layer.remove();
  }
  const by = new Map();
  rows.forEach((r) => {
    if (r.lat == null || r.lon == null) return;
    const key = r.municipio_key || r.municipio + "|" + r.estado;
    if (!by.has(key)) {
      by.set(key, {
        lat: r.lat,
        lon: r.lon,
        municipio: r.municipio,
        estado: r.estado,
        mw: 0,
        n: 0,
        owners: { us: 0, prc: 0, mexico: 0, other: 0, unmatched: 0 },
      });
    }
    const g = by.get(key);
    g.mw += r.mw;
    g.n += 1;
    g.owners[r.owner_class] = (g.owners[r.owner_class] || 0) + r.mw;
  });
  layer = L.layerGroup();
  by.forEach((g) => {
    let owner = "unmatched";
    let best = -1;
    OWNER_ORDER.forEach((k) => {
      if (g.owners[k] > best) {
        best = g.owners[k];
        owner = k;
      }
    });
    const m = L.circleMarker([g.lat, g.lon], {
      radius: radiusFor(g.mw),
      color: COLORS[owner],
      fillColor: COLORS[owner],
      fillOpacity: 0.55,
      weight: 1,
    });
    m.bindPopup(
      `<strong>${g.municipio || "—"}, ${g.estado || "—"}</strong><br>` +
        `${fmtMw(g.mw)} in queue · ${g.n} request(s)<br>` +
        OWNER_ORDER.map((k) => `${LABELS[k]}: ${g.owners[k].toFixed(1)} MW`).join("<br>")
    );
    layer.addLayer(m);
  });
  layer.addTo(map);
}

function render() {
  const s = selected();
  $("charts-latest").style.display = s.clock === "latest" ? "" : "none";
  $("charts-time").style.display = s.clock === "time" ? "block" : "none";
  if (s.clock === "time") {
    renderTime();
    renderStats(filterRows());
    $("note").textContent =
      "Time series is total in-queue MW by snapshot (outliers ≥ 5,000 MW excluded). Ownership coloring is only on the latest snapshot, where the codebook is applied.";
    return;
  }
  const rows = filterRows();
  renderStats(rows);
  renderOwner(rows);
  renderStatus(rows);
  renderMap(rows);
  if (map) {
    setTimeout(() => map.invalidateSize(), 80);
  }
  const snap = DATA.latest_snapshot;
  $("note").textContent =
    `Latest snapshot ${snap}. ${rows.length} in-queue rows under current filters. ` +
    `Most megawatts are unmatched because CENACE does not publish the applicant.`;
}

async function boot() {
  const [dash, rows] = await Promise.all([
    fetch("data/dashboard.json").then((r) => r.json()),
    fetch("data/open_rows.json").then((r) => r.json()),
  ]);
  DATA = dash;
  ROWS = rows;
  $("caption").textContent = dash.caption;
  ["clock", "cola", "region", "unmatched"].forEach((id) => $(id).addEventListener("change", render));
  render();
}

boot().catch((err) => {
  $("note").textContent = "Could not load data/dashboard.json. Rebuild with process/build_site_data.py.";
  console.error(err);
});
