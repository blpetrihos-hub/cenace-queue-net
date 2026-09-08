"""Shared text and geography helpers."""
from __future__ import annotations

import re
import unicodedata
from datetime import date

MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

IN_QUEUE_STATUS = {
    "recepcion y revision",
    "aceptada",
    "observada",
    "revision",
    "en estudio",
    "pendiente",
    "en proceso",
}

STATE_ALIASES = {
    "aguascalientes": "Aguascalientes",
    "agauscalientes": "Aguascalientes",
    "baja california": "Baja California",
    "baja california norte": "Baja California",
    "baja california.": "Baja California",
    "baja california4": "Baja California",
    "b.c.": "Baja California",
    "baja california s": "Baja California Sur",
    "baja california sur": "Baja California Sur",
    "campeche": "Campeche",
    "chiapas": "Chiapas",
    "chihuahua": "Chihuahua",
    "chihuhua": "Chihuahua",
    "ciudad de mexico": "Ciudad de México",
    "ciudad de mexico df": "Ciudad de México",
    "ciudad de mexicociudad de mexico": "Ciudad de México",
    "cdmx": "Ciudad de México",
    "d.f": "Ciudad de México",
    "d.f.": "Ciudad de México",
    "distrito federal": "Ciudad de México",
    "mexico df": "Ciudad de México",
    "mexico, d.f.": "Ciudad de México",
    "coahuila": "Coahuila",
    "coahuila de zaragoza": "Coahuila",
    "cohauila": "Coahuila",
    "colima": "Colima",
    "durango": "Durango",
    "guanajuato": "Guanajuato",
    "estado de guanajuato": "Guanajuato",
    "guerrero": "Guerrero",
    "hidalgo": "Hidalgo",
    "jalisco": "Jalisco",
    "estado de jalisco": "Jalisco",
    "mexico": "México",
    "mex": "México",
    "edo de mexico": "México",
    "edo mex": "México",
    "edo. de mex.": "México",
    "edo. de mexico": "México",
    "estado de mexico": "México",
    "michoacan": "Michoacán",
    "michoacan de ocampo": "Michoacán",
    "morelos": "Morelos",
    "estado de morelos": "Morelos",
    "nayarit": "Nayarit",
    "nuevo leon": "Nuevo León",
    "nuevo leon2700": "Nuevo León",
    "oaxaca": "Oaxaca",
    "oaxaca.": "Oaxaca",
    "puebla": "Puebla",
    "queretaro": "Querétaro",
    "quererato": "Querétaro",
    "qro": "Querétaro",
    "quintana roo": "Quintana Roo",
    "san luis potosi": "San Luis Potosí",
    "san luis posoti": "San Luis Potosí",
    "san luis posot": "San Luis Potosí",
    "sinaloa": "Sinaloa",
    "sianaloa": "Sinaloa",
    "sonora": "Sonora",
    "sonora.": "Sonora",
    "son": "Sonora",
    "tabasco": "Tabasco",
    "tamaulipas": "Tamaulipas",
    "tamulipas": "Tamaulipas",
    "tlaxcala": "Tlaxcala",
    "veracruz": "Veracruz",
    "veracruz de ignacio de la llave": "Veracruz",
    "yucatan": "Yucatán",
    "zacatecas": "Zacatecas",
}

STATE_COORDS = {
    "Aguascalientes": (21.8853, -102.2916),
    "Baja California": (30.8406, -115.2838),
    "Baja California Sur": (26.0444, -111.6661),
    "Campeche": (19.8301, -90.5349),
    "Chiapas": (16.7569, -93.1292),
    "Chihuahua": (28.6330, -106.0691),
    "Ciudad de México": (19.4326, -99.1332),
    "Coahuila": (27.0587, -101.7068),
    "Colima": (19.2452, -103.7242),
    "Durango": (24.0277, -104.6532),
    "Guanajuato": (21.0190, -101.2574),
    "Guerrero": (17.4392, -99.5451),
    "Hidalgo": (20.0911, -98.7624),
    "Jalisco": (20.6595, -103.3494),
    "México": (19.4969, -99.7233),
    "Michoacán": (19.5665, -101.7068),
    "Morelos": (18.6813, -99.1013),
    "Nayarit": (21.7514, -104.8455),
    "Nuevo León": (25.5922, -99.9962),
    "Oaxaca": (17.0732, -96.7266),
    "Puebla": (19.0414, -98.2063),
    "Querétaro": (20.5888, -100.3899),
    "Quintana Roo": (19.1817, -88.4791),
    "San Luis Potosí": (22.1565, -100.9855),
    "Sinaloa": (25.1721, -107.4795),
    "Sonora": (29.2972, -110.3309),
    "Tabasco": (17.8409, -92.6189),
    "Tamaulipas": (24.2669, -98.8363),
    "Tlaxcala": (19.3182, -98.2375),
    "Veracruz": (19.1738, -96.1342),
    "Yucatán": (20.7099, -89.0943),
    "Zacatecas": (22.7709, -102.5832),
}

NL_FOCUS = {"Nuevo León"}
BAJIO_FOCUS = {
    "Guanajuato",
    "Querétaro",
    "Aguascalientes",
    "San Luis Potosí",
    "Jalisco",
}

# Hand-checked municipal seats / industrial centroids (WGS84).
# Used when the public cola gives municipio + estado, not a CENACE bus name.
MUNI_COORDS = {
    ("mexicali", "Baja California"): (32.6245, -115.4523),
    ("tijuana", "Baja California"): (32.5149, -117.0382),
    ("ensenada", "Baja California"): (31.8667, -116.5967),
    ("playas de rosarito", "Baja California"): (32.3649, -117.0553),
    ("tecate", "Baja California"): (32.5656, -116.6325),
    ("la paz", "Baja California Sur"): (24.1426, -110.3128),
    ("los cabos", "Baja California Sur"): (23.0636, -109.7020),
    ("carmen", "Campeche"): (18.6517, -91.8070),
    ("campeche", "Campeche"): (19.8301, -90.5349),
    ("tuxtla gutierrez", "Chiapas"): (16.7516, -93.1026),
    ("tapachula", "Chiapas"): (14.9056, -92.2634),
    ("chicoasen", "Chiapas"): (16.9650, -93.1030),
    ("juarez", "Chihuahua"): (31.6904, -106.4245),
    ("chihuahua", "Chihuahua"): (28.6350, -106.0890),
    ("delicias", "Chihuahua"): (28.1900, -105.4700),
    ("saltillo", "Coahuila"): (25.4232, -101.0053),
    ("ramos arizpe", "Coahuila"): (25.5392, -100.9475),
    ("torreon", "Coahuila"): (25.5428, -103.4068),
    ("monclova", "Coahuila"): (26.9103, -101.4290),
    ("acuna", "Coahuila"): (29.3232, -100.9522),
    ("piedras negras", "Coahuila"): (28.7000, -100.5230),
    ("manzanillo", "Colima"): (19.1136, -104.3421),
    ("colima", "Colima"): (19.2433, -103.7250),
    ("durango", "Durango"): (24.0277, -104.6532),
    ("lerdo", "Durango"): (25.5360, -103.5250),
    ("leon", "Guanajuato"): (21.1250, -101.6860),
    ("silao", "Guanajuato"): (20.9437, -101.4270),
    ("irapuato", "Guanajuato"): (20.6767, -101.3563),
    ("celaya", "Guanajuato"): (20.5280, -100.8150),
    ("salamanca", "Guanajuato"): (20.5714, -101.1917),
    ("san luis de la paz", "Guanajuato"): (21.2978, -100.5170),
    ("guanajuato", "Guanajuato"): (21.0190, -101.2574),
    ("acapulco de juarez", "Guerrero"): (16.8531, -99.8237),
    ("pachuca de soto", "Hidalgo"): (20.1011, -98.7591),
    ("tula de allende", "Hidalgo"): (20.0514, -99.3431),
    ("tulancingo de bravo", "Hidalgo"): (20.0833, -98.3667),
    ("guadalajara", "Jalisco"): (20.6597, -103.3496),
    ("zapopan", "Jalisco"): (20.7214, -103.3918),
    ("el salto", "Jalisco"): (20.5197, -103.1794),
    ("puerto vallarta", "Jalisco"): (20.6534, -105.2253),
    ("toluca", "México"): (19.2826, -99.6557),
    ("tultitlan", "México"): (19.6450, -99.1681),
    ("cuautitlan izcalli", "México"): (19.6469, -99.2119),
    ("ecatepec de morelos", "México"): (19.6019, -99.0506),
    ("naucalpan de juarez", "México"): (19.4785, -99.2327),
    ("morelia", "Michoacán"): (19.7060, -101.1950),
    ("lazaro cardenas", "Michoacán"): (17.9583, -102.1920),
    ("cuernavaca", "Morelos"): (18.9242, -99.2216),
    ("tepic", "Nayarit"): (21.5039, -104.8946),
    ("monterrey", "Nuevo León"): (25.6866, -100.3161),
    ("san nicolas de los garza", "Nuevo León"): (25.7417, -100.3020),
    ("guadalupe", "Nuevo León"): (25.6767, -100.2560),
    ("apodaca", "Nuevo León"): (25.7817, -100.1883),
    ("santa catarina", "Nuevo León"): (25.6732, -100.4580),
    ("garcia", "Nuevo León"): (25.7966, -100.5840),
    ("pesqueria", "Nuevo León"): (25.7850, -100.0510),
    ("salinas victoria", "Nuevo León"): (26.0744, -100.2960),
    ("general escobedo", "Nuevo León"): (25.7953, -100.3144),
    ("el carmen", "Nuevo León"): (25.9360, -100.3630),
    ("cienega de flores", "Nuevo León"): (25.9550, -100.1850),
    ("cadereyta jimenez", "Nuevo León"): (25.5890, -100.0010),
    ("marin", "Nuevo León"): (25.8790, -100.0300),
    ("mina", "Nuevo León"): (26.0010, -100.5300),
    ("zuazua", "Nuevo León"): (25.9000, -100.1100),
    ("san pedro garza garcia", "Nuevo León"): (25.6570, -100.4020),
    ("oaxaca de juarez", "Oaxaca"): (17.0732, -96.7266),
    ("puebla", "Puebla"): (19.0414, -98.2063),
    ("cuyoaco", "Puebla"): (19.6010, -97.6200),
    ("tepeyahualco", "Puebla"): (19.4880, -97.4960),
    ("queretaro", "Querétaro"): (20.5888, -100.3899),
    ("el marques", "Querétaro"): (20.6240, -100.2700),
    ("colon", "Querétaro"): (20.7830, -100.0450),
    ("pedro escobedo", "Querétaro"): (20.4990, -100.1400),
    ("huimilpan", "Querétaro"): (20.3700, -100.2700),
    ("cancun", "Quintana Roo"): (21.1619, -86.8515),
    ("benito juarez", "Quintana Roo"): (21.1619, -86.8515),
    ("san luis potosi", "San Luis Potosí"): (22.1565, -100.9855),
    ("villa de reyes", "San Luis Potosí"): (21.8030, -100.9340),
    ("villa reyes", "San Luis Potosí"): (21.8030, -100.9340),
    ("tamazunchale", "San Luis Potosí"): (21.2600, -98.7900),
    ("culiacan", "Sinaloa"): (24.8091, -107.3940),
    ("mazatlan", "Sinaloa"): (23.2494, -106.4111),
    ("hermosillo", "Sonora"): (29.0729, -110.9559),
    ("nogales", "Sonora"): (31.3086, -110.9422),
    ("cajeme", "Sonora"): (27.4860, -109.9310),
    ("empalme", "Sonora"): (27.9610, -110.8140),
    ("puerto penasco", "Sonora"): (31.3170, -113.5330),
    ("san luis rio colorado", "Sonora"): (32.4540, -114.7720),
    ("agua prieta", "Sonora"): (31.3300, -109.5480),
    ("villahermosa", "Tabasco"): (17.9892, -92.9281),
    ("centro", "Tabasco"): (17.9892, -92.9281),
    ("altamira", "Tamaulipas"): (22.3930, -97.9380),
    ("tampico", "Tamaulipas"): (22.2330, -97.8610),
    ("ciudad victoria", "Tamaulipas"): (23.7369, -99.1411),
    ("reynosa", "Tamaulipas"): (26.0508, -98.2975),
    ("matamoros", "Tamaulipas"): (25.8690, -97.5020),
    ("nuevo laredo", "Tamaulipas"): (27.4860, -99.5070),
    ("tuxpan", "Tamaulipas"): (22.5080, -99.0820),
    ("tlaxcala", "Tlaxcala"): (19.3182, -98.2375),
    ("hueyotlipan", "Tlaxcala"): (19.4700, -98.3500),
    ("veracruz", "Veracruz"): (19.1738, -96.1342),
    ("xalapa", "Veracruz"): (19.5438, -96.9102),
    ("coatzacoalcos", "Veracruz"): (18.1342, -94.4589),
    ("tuxpan", "Veracruz"): (20.9570, -97.4070),
    ("tuxpan de rodriguez cano", "Veracruz"): (20.9570, -97.4070),
    ("rio blanco", "Veracruz"): (18.8300, -97.1560),
    ("merida", "Yucatán"): (20.9674, -89.5926),
    ("valladolid", "Yucatán"): (20.6890, -88.2020),
    ("progreso", "Yucatán"): (21.2830, -89.6620),
    ("zacatecas", "Zacatecas"): (22.7709, -102.5832),
    ("fresnillo", "Zacatecas"): (23.1750, -102.8670),
    ("aguascalientes", "Aguascalientes"): (21.8853, -102.2916),
    ("jocotitlan", "México"): (19.7070, -99.7880),
    ("cabo san lucas", "Baja California Sur"): (22.8909, -109.9124),
    ("frontera", "Coahuila"): (26.9280, -101.4520),
    ("frontera", "Tabasco"): (18.5330, -92.6450),
    ("mendez", "Tamaulipas"): (25.1170, -98.5870),
}


def fold(text) -> str:
    if text is None:
        return ""
    s = str(text).replace("\xa0", " ").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ñ", "n")
    s = re.sub(r"[^a-z0-9.]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def titleish(text) -> str:
    s = str(text or "").replace("\xa0", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_state(raw) -> str | None:
    key = fold(raw)
    if not key or key in {"nan", "none", "texas"}:
        return None
    key = re.sub(r"\d+$", "", key).strip()
    if key in STATE_ALIASES:
        return STATE_ALIASES[key]
    # "Estado De Jalisco" already handled; try last token
    for alias, canon in STATE_ALIASES.items():
        if key.endswith(alias) or alias in key:
            return canon
    return None


def normalize_muni(raw) -> str:
    s = fold(raw)
    s = re.sub(r"\d+$", "", s).strip()
    s = s.replace(".", "")
    return s


def region_tag(state: str | None) -> str:
    if state in NL_FOCUS:
        return "nuevo_leon"
    if state in BAJIO_FOCUS:
        return "bajio"
    return "other"


def parse_spanish_date(text: str) -> date | None:
    m = re.search(
        r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})",
        fold(text),
        flags=re.I,
    )
    if not m:
        return None
    day = int(m.group(1))
    month = MONTHS.get(fold(m.group(2)))
    year = int(m.group(3))
    if not month:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_filename_date(name: str) -> date | None:
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", name)
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def classify_status(raw) -> str:
    k = fold(raw)
    if k in IN_QUEUE_STATUS:
        return "in_queue"
    if k == "atendida":
        return "attended"
    if k == "cancelada":
        return "cancelled"
    return "other"


def tech_family(raw) -> str:
    k = fold(raw)
    if any(x in k for x in ("fotovolta", "solar", "fv ")):
        return "solar"
    if any(x in k for x in ("eolic", "viento", "wind")):
        return "wind"
    if "ciclo combinado" in k or k in {"cc", "ccc"}:
        return "cc"
    if any(x in k for x in ("hidraul", "hidro")):
        return "hydro"
    if any(x in k for x in ("cogener")):
        return "cogen"
    if any(
        x in k
        for x in (
            "termic",
            "termo",
            "turbogas",
            "combust",
            "vapor",
            "carbo",
            "nucle",
        )
    ):
        return "thermal"
    if k in {"", "nan", "none"}:
        return "unknown"
    return "other"


def classify_pais(raw) -> str:
    k = fold(raw)
    if k in {"estados unidos", "estados unidos de america", "eua", "eu"}:
        return "us"
    if k == "china":
        return "prc"
    if k in {"mexico", "mex"}:
        return "mexico"
    return "other"


def extract_muni_from_address(address, estado: str | None) -> str:
    if not address or str(address) in {"nan", "None"}:
        return ""
    text = str(address).replace("\n", ", ")
    parts = [p.strip() for p in re.split(r"[,;]", text) if p.strip()]
    if not parts:
        return ""
    state_f = fold(estado) if estado else ""
    for part in reversed(parts):
        pf = fold(part)
        if not pf:
            continue
        if state_f and (pf == state_f or pf.endswith(state_f)):
            continue
        if re.fullmatch(r"c\.?p\.?\s*\d+", pf) or re.fullmatch(r"\d{5}", pf):
            continue
        return normalize_muni(part)
    return normalize_muni(parts[-1])


def round_mw(mw, places: int = 1) -> str:
    try:
        return f"{round(float(mw), places):.{places}f}"
    except (TypeError, ValueError):
        return ""
