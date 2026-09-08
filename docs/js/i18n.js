const I18N = {
  en: {
    pageTitleDash: "Dashboard · Who is waiting for Mexico’s grid",
    pageTitleMethods: "Methods · Who is waiting for Mexico’s grid",
    pageTitleBib: "Bibliography · Who is waiting for Mexico’s grid",
    kicker: "William & Mary · GIAS Futures Group · Team 2",
    title: "Who is waiting for Mexico’s grid",
    sub: "U.S. vs PRC vs Mexico, in megawatts and days. Diagnostic only — no policy advice.",
    navDash: "Dashboard",
    navMethods: "Methods",
    navBib: "Bibliography",
    caption:
      "This counts place in line for electricity. Power plants (generation) are named from CNE permits when the match is unique. Factories (load) are mostly unnamed because CENACE does not publish the applicant.",
    clock: "When",
    clockLatest: "Latest snapshot",
    clockTime: "Over time",
    cola: "What",
    colaAll: "Power plants + factories",
    colaGen: "Power plants (generation)",
    colaLoad: "Factories (load)",
    region: "Where",
    regionAll: "All Mexico",
    regionNL: "Nuevo León",
    regionBajio: "Bajío",
    unmatched: "Unnamed",
    unmatchedInc: "Show unnamed megawatts",
    unmatchedExc: "Named rows only",
    scorePlants: "Power plants still in line",
    scorePlantsNote:
      "Country comes from CNE’s official “país de origen” on a unique match of state + megawatts + technology. Mixed or blank labels are Other. PRC behind a Mexican company stays Mexico or unnamed — we do not guess.",
    scoreLoad: "Factories still in line",
    scoreLoadNote:
      "CENACE does not name factories. Only a few cited matches (Tesla, LGMG). The rest stay unnamed.",
    scoreN: "{n} requests",
    statWaiting: "Waiting",
    statRequests: "Requests",
    statUnnamed: "Unnamed",
    statNamed: "Named",
    statDays: "Median days waiting",
    chartOwner: "Megawatts waiting, by country",
    chartStatus: "Study status",
    chartTime: "Megawatts waiting, over time",
    legendNote: "Dot size is megawatts still waiting. Color is country when named.",
    us: "U.S.",
    prc: "PRC",
    mexico: "Mexico",
    other: "Other",
    unmatchedLabel: "Unnamed",
    noteLatest: "Snapshot {snap}. {n} requests in line with current filters.",
    noteTime:
      "Line chart is total megawatts waiting at each snapshot. Country colors apply to the latest snapshot only.",
    footer:
      "No policy recommendations. Unnamed megawatts stay unnamed. Map: Carto / OpenStreetMap.",
    loadFail: "Could not load the data files. Rebuild with process/build_site_data.py.",
    popupWaiting: "waiting",
    popupRequests: "request(s)",
    xMw: "MW waiting",
    timeAll: "Power plants + factories",
    timeGen: "Power plants waiting",
    timeLoad: "Factories waiting",
    langEn: "EN",
    langEs: "ES",
    methodsH2what: "What this measures",
    bibH2: "Annotated bibliography",
    bibLead:
      "Official sources, named academic publishers for context, and established outlets for named factory matches. Built from sources/bibliography.yml so this page cannot drift.",
    bibExclude: "Excluded: World Population Review, anonymous blogs, SOUTHCOM advocacy as finding, AMP-style clips.",
    bibOfficial: "Official",
    bibJournalism: "Journalism (named factory matches)",
    bibAcademic: "Academic / practitioner (context, not the queue)",
    bibSupports: "Supports",
    bibContext: "No codebook row. Context only.",
  },
  es: {
    pageTitleDash: "Tablero · Quién espera en la red eléctrica de México",
    pageTitleMethods: "Métodos · Quién espera en la red eléctrica de México",
    pageTitleBib: "Bibliografía · Quién espera en la red eléctrica de México",
    kicker: "William & Mary · GIAS Futures Group · Equipo 2",
    title: "Quién espera en la red eléctrica de México",
    sub: "EE. UU. frente a RPC frente a México, en megawatts y días. Solo diagnóstico — sin recomendaciones de política.",
    navDash: "Tablero",
    navMethods: "Métodos",
    navBib: "Bibliografía",
    caption:
      "Se mide el lugar en la fila para conectarse a la red. Las centrales se nombran con permisos de la CNE cuando el cruce es único. Las fábricas casi no tienen nombre: CENACE no publica al solicitante.",
    clock: "Cuándo",
    clockLatest: "Última actualización",
    clockTime: "A lo largo del tiempo",
    cola: "Qué",
    colaAll: "Centrales + fábricas",
    colaGen: "Centrales (generación)",
    colaLoad: "Fábricas (carga)",
    region: "Dónde",
    regionAll: "Todo México",
    regionNL: "Nuevo León",
    regionBajio: "Bajío",
    unmatched: "Sin nombre",
    unmatchedInc: "Mostrar megawatts sin nombre",
    unmatchedExc: "Solo filas con nombre",
    scorePlants: "Centrales aún en la fila",
    scorePlantsNote:
      "El país sale del “país de origen” oficial de la CNE cuando coinciden estado + megawatts + tecnología de forma única. Etiquetas mixtas o vacías van a Otros. RPC detrás de una empresa mexicana permanece como México o sin nombre: no se adivina.",
    scoreLoad: "Fábricas aún en la fila",
    scoreLoadNote:
      "CENACE no nombra fábricas. Solo unos cruces citados (Tesla, LGMG). El resto queda sin nombre.",
    scoreN: "{n} solicitudes",
    statWaiting: "En espera",
    statRequests: "Solicitudes",
    statUnnamed: "Sin nombre",
    statNamed: "Con nombre",
    statDays: "Días de espera (mediana)",
    chartOwner: "Megawatts en espera, por país",
    chartStatus: "Estado del estudio",
    chartTime: "Megawatts en espera a lo largo del tiempo",
    legendNote: "El tamaño del punto es megawatts aún en espera. El color es el país cuando hay nombre.",
    us: "EE. UU.",
    prc: "RPC",
    mexico: "México",
    other: "Otros",
    unmatchedLabel: "Sin nombre",
    noteLatest: "Actualización {snap}. {n} solicitudes en fila con los filtros actuales.",
    noteTime:
      "La línea es el total de megawatts en espera en cada actualización. Los colores de país aplican solo a la más reciente.",
    footer:
      "Sin recomendaciones de política. Los megawatts sin nombre siguen sin nombre. Mapa: Carto / OpenStreetMap.",
    loadFail: "No se pudieron cargar los datos. Regenerar con process/build_site_data.py.",
    popupWaiting: "en espera",
    popupRequests: "solicitud(es)",
    xMw: "MW en espera",
    timeAll: "Centrales + fábricas",
    timeGen: "Centrales en espera",
    timeLoad: "Fábricas en espera",
    langEn: "EN",
    langEs: "ES",
    methodsH2what: "Qué se mide",
    bibH2: "Bibliografía anotada",
    bibLead:
      "Fuentes oficiales, editoriales académicas con nombre para contexto, y medios establecidos para fábricas nombradas. Se genera desde sources/bibliography.yml para que no se desvíe.",
    bibExclude:
      "Quedan fuera: World Population Review, blogs anónimos, textos de abogacía de SOUTHCOM tratados como hallazgo, clips tipo AMP.",
    bibOfficial: "Oficial",
    bibJournalism: "Prensa (cruces de fábrica con nombre)",
    bibAcademic: "Académico / profesional (contexto, no la cola)",
    bibSupports: "Sustenta",
    bibContext: "Sin fila de la tabla de cruces citados. Solo contexto.",
  },
};

function t(key) {
  const lang = document.documentElement.lang === "es" ? "es" : "en";
  return (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
}

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (I18N.en[key] !== undefined) el.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    const key = el.getAttribute("data-i18n-html");
    if (I18N.en[key] !== undefined) el.innerHTML = t(key);
  });
  document.querySelectorAll(".lang-en, .lang-es").forEach((el) => {
    const want = document.documentElement.lang === "es" ? "lang-es" : "lang-en";
    el.hidden = !el.classList.contains(want);
  });
  document.querySelectorAll("[data-lang-btn]").forEach((btn) => {
    btn.setAttribute("aria-pressed", btn.getAttribute("data-lang-btn") === document.documentElement.lang);
  });
  const pageKey = document.body && document.body.getAttribute("data-page-title");
  if (pageKey && I18N.en[pageKey] !== undefined) document.title = t(pageKey);
}

function setLang(lang) {
  document.documentElement.lang = lang === "es" ? "es" : "en";
  try {
    localStorage.setItem("cenace-lang", document.documentElement.lang);
  } catch (e) {}
  applyI18n();
  if (typeof window.onLangChange === "function") window.onLangChange();
}

function initLang() {
  let lang = "en";
  try {
    lang = localStorage.getItem("cenace-lang") || "en";
  } catch (e) {}
  document.documentElement.lang = lang === "es" ? "es" : "en";
  document.querySelectorAll("[data-lang-btn]").forEach((btn) => {
    btn.addEventListener("click", () => setLang(btn.getAttribute("data-lang-btn")));
  });
  applyI18n();
}
