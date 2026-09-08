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
  unmatched: "Unnamed",
};
const OWNER_ORDER = ["us", "prc", "mexico", "other", "unmatched"];
const CARTO_BASEMAP_KEY = "cb1_32m3_1_44dc754e68375e8ab5208497";

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

function filterRows(extra) {
  const s = selected();
  const cola = extra && extra.cola ? extra.cola : s.cola;
  return ROWS.filter((r) => {
    if (cola !== "all" && r.cola_type !== cola) return false;
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
  return Math.round(n) + " MW";
}

function renderStats(rows) {
  const unnamed = rows.filter((r) => r.owner_class === "unmatched");
  const named = rows.filter((r) => r.owner_class !== "unmatched");
  const days = rows.map((r) => r.days_in_queue).filter((d) => d != null).sort((a, b) => a - b);
  const median = days.length ? days[Math.floor(days.length / 2)] : null;
  const html = [
    ["Waiting", fmtMw(sumMw(rows))],
    ["Requests", String(rows.length)],
    ["Unnamed", fmtMw(sumMw(unnamed))],
    ["Named", fmtMw(sumMw(named))],
    ["Median days waiting", median == null ? "—" : String(median)],
  ]
    .map(([k, v]) => `<div class="stat"><b>${v}</b><span>${k}</span></div>`)
    .join("");
  $("stats").innerHTML = html;
}

function scoreCell(key, rows) {
  const sub = rows.filter((r) => r.owner_class === key);
  return (
    `<div class="score ${key}">` +
    `<b>${fmtMw(sumMw(sub))}</b>` +
    `<span>${LABELS[key]}</span>` +
    `<small>${sub.length} requests</small>` +
    `</div>`
  );
}

function renderScoreboard() {
  const s = selected();
  const plants = filterRows({ cola: "interconexion" });
  const factories = filterRows({ cola: "conexion" });
  const keys = s.unmatched === "exclude" ? OWNER_ORDER.filter((k) => k !== "unmatched") : OWNER_ORDER;
  $("scorePlants").innerHTML = keys.map((k) => scoreCell(k, plants)).join("");
  $("scoreLoad").innerHTML = keys.map((k) => scoreCell(k, factories)).join("");
  $("scorePlantsWrap").hidden = s.clock === "time" || s.cola === "conexion";
  $("scoreLoadWrap").hidden = s.clock === "time" || s.cola === "interconexion";
}

function ownerCounts(rows) {
  return OWNER_ORDER.map((k) => ({
    key: k,
    label: LABELS[k],
    mw: sumMw(rows.filter((r) => r.owner_class === k)),
  })).filter((c) => selected().unmatched === "include" || c.key !== "unmatched");
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
      scales: { x: { title: { display: true, text: "MW waiting" } } },
    },
  });
}

function englishStatus(raw) {
  const k = String(raw || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
  if (k.includes("recepcion")) return "Received / under review";
  if (k === "aceptada") return "Accepted";
  if (k === "observada") return "Observations";
  if (k === "atendida") return "Attended";
  if (k === "cancelada") return "Cancelled";
  if (k === "revision") return "Under review";
  if (!k) return "—";
  return "Other";
}

function renderStatus(rows) {
  const by = {};
  rows.forEach((r) => {
    const k = englishStatus(r.estatus);
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
  const labels = ts.map((row) => row.snapshot_date);
  let dataset;
  if (s.cola === "interconexion") {
    dataset = { label: "Power plants waiting", data: ts.map((row) => row.interconexion_in_queue_mw) };
  } else if (s.cola === "conexion") {
    dataset = { label: "Factories waiting", data: ts.map((row) => row.conexion_in_queue_mw) };
  } else {
    dataset = {
      label: "Power plants + factories",
      data: ts.map((row) => row.interconexion_in_queue_mw + row.conexion_in_queue_mw),
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
      scales: { y: { title: { display: true, text: "MW waiting" } } },
    },
  });
}

function radiusFor(mw) {
  return 6 + Math.sqrt(Math.max(mw, 0)) * 0.55;
}

const FS_EXPAND =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"/></svg>';
const FS_COLLAPSE =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3v5H3M16 3v5h5M8 21v-5H3M16 21v-5h5"/></svg>';

function mapIsFullscreen(el) {
  const fs = document.fullscreenElement || document.webkitFullscreenElement;
  return fs === el || el.classList.contains("map-windowed-full");
}

function updateFullscreenButton(el, btn) {
  const on = mapIsFullscreen(el);
  btn.innerHTML = on ? FS_COLLAPSE : FS_EXPAND;
  btn.title = on ? "Exit full screen" : "Full screen";
  btn.setAttribute("aria-label", btn.title);
  btn.setAttribute("aria-pressed", on ? "true" : "false");
}

function enterMapFullscreen(el) {
  const req = el.requestFullscreen || el.webkitRequestFullscreen;
  if (req) {
    const p = req.call(el);
    if (p && typeof p.catch === "function") {
      p.catch(() => el.classList.add("map-windowed-full"));
    }
    return;
  }
  el.classList.add("map-windowed-full");
}

function exitMapFullscreen(el) {
  const cur = document.fullscreenElement || document.webkitFullscreenElement;
  if (cur === el) {
    const exit = document.exitFullscreen || document.webkitExitFullscreen;
    if (exit) exit.call(document);
    return;
  }
  el.classList.remove("map-windowed-full");
}

function addFullscreenControl(leafletMap) {
  const Fullscreen = L.Control.extend({
    options: { position: "topleft" },
    onAdd: function () {
      const bar = L.DomUtil.create("div", "leaflet-bar leaflet-control");
      const btn = L.DomUtil.create("a", "map-fs-btn", bar);
      btn.href = "#";
      btn.innerHTML = FS_EXPAND;
      btn.title = "Full screen";
      btn.setAttribute("role", "button");
      btn.setAttribute("aria-label", "Full screen");
      btn.setAttribute("aria-pressed", "false");
      L.DomEvent.disableClickPropagation(bar);
      L.DomEvent.disableScrollPropagation(bar);
      L.DomEvent.on(btn, "click", L.DomEvent.stop).on(btn, "click", function () {
        const el = leafletMap.getContainer();
        if (mapIsFullscreen(el)) exitMapFullscreen(el);
        else enterMapFullscreen(el);
      });
      const sync = function () {
        updateFullscreenButton(leafletMap.getContainer(), btn);
        setTimeout(function () {
          leafletMap.invalidateSize();
        }, 80);
      };
      document.addEventListener("fullscreenchange", sync);
      document.addEventListener("webkitfullscreenchange", sync);
      window.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && leafletMap.getContainer().classList.contains("map-windowed-full")) {
          exitMapFullscreen(leafletMap.getContainer());
          sync();
        }
      });
      const mo = new MutationObserver(sync);
      mo.observe(leafletMap.getContainer(), { attributes: true, attributeFilter: ["class"] });
      return bar;
    },
  });
  leafletMap.addControl(new Fullscreen());
}

function renderMap(rows) {
  if (!map) {
    map = L.map("map").setView([23.6, -102.5], 5);
    const tiles =
      "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=" +
      encodeURIComponent(CARTO_BASEMAP_KEY);
    L.tileLayer(tiles, {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 20,
    }).addTo(map);
    addFullscreenControl(map);
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
        `${fmtMw(g.mw)} waiting · ${g.n} request(s)<br>` +
        OWNER_ORDER.map((k) => `${LABELS[k]}: ${g.owners[k].toFixed(1)} MW`).join("<br>")
    );
    layer.addLayer(m);
  });
  layer.addTo(map);
}

function render() {
  if (!DATA || !ROWS) return;
  const s = selected();
  $("charts-latest").style.display = s.clock === "latest" ? "" : "none";
  $("charts-time").style.display = s.clock === "time" ? "block" : "none";
  renderScoreboard();
  if (s.clock === "time") {
    renderTime();
    renderStats(filterRows());
    $("note").textContent =
      "Line chart is total megawatts waiting at each snapshot. Country colors apply to the latest snapshot only.";
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
  $("note").textContent =
    `Snapshot ${DATA.latest_snapshot}. ${rows.length} requests in line with current filters.`;
}

async function boot() {
  const [dash, rows] = await Promise.all([
    fetch("data/dashboard.json").then((r) => r.json()),
    fetch("data/open_rows.json").then((r) => r.json()),
  ]);
  DATA = dash;
  ROWS = rows;
  ["clock", "cola", "region", "unmatched"].forEach((id) => $(id).addEventListener("change", render));
  render();
}

boot().catch((err) => {
  $("note").textContent = "Could not load the data files. Rebuild with process/build_site_data.py.";
  console.error(err);
});
