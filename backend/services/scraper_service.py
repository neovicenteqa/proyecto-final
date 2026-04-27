import re
import requests
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 8

# Dominios que suelen bloquear scraping — los saltamos
BLOCKED_DOMAINS = [
    "datosperu.org", "linkedin.com", "facebook.com",
    "instagram.com", "twitter.com", "x.com",
    "academia.edu", "scribd.com", "slideshare.net",
    "researchgate.net", "issuu.com", "docsity.com",
    "monografias.com", "gestiopolis.com", "buenastareas.com",
    "youtube.com", "youtu.be", "tiktok.com",
    "wikipedia.org",
]


# ── Helpers ────────────────────────────────────────────────────────────────

def _ddg_search(query: str, max_results: int = 6) -> list:
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        print(f"[scraper] DDG search error: {e}")
        return []


def _ddg_news(query: str, max_results: int = 5) -> list:
    try:
        with DDGS() as ddgs:
            return list(ddgs.news(query, max_results=max_results))
    except Exception as e:
        print(f"[scraper] DDG news error: {e}")
        return []


def _is_blocked(url: str) -> bool:
    return any(d in url for d in BLOCKED_DOMAINS)


def _scrape_page(url: str, max_chars: int = 4000) -> str:
    """Extrae texto limpio de una URL."""
    if _is_blocked(url):
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text[:max_chars]
    except Exception as e:
        print(f"[scraper] Error scraping {url}: {e}")
        return ""


_NOISE_PATTERNS = re.compile(
    r"(Log In|Sign Up|Sign In|Cookie|Privacy Policy|Terms of Service"
    r"|Subscribe|Newsletter|Download PDF|Download Free|keyboard_arrow"
    r"|visibility \d+|description \d+)",
    re.IGNORECASE,
)


def _is_useful(text: str) -> bool:
    if len(text) < 200:
        return False
    noise_hits = len(_NOISE_PATTERNS.findall(text[:500]))
    return noise_hits < 3


def _scrape_best(results: list) -> tuple[str, str]:
    """
    Prioriza URLs que parezcan el sitio oficial (sin subdirectorios largos),
    descarta sitios de documentos/redes sociales y verifica que el texto sea útil.
    """
    def _priority(url: str) -> int:
        path = url.split("/", 3)[-1] if url.count("/") >= 3 else ""
        # URLs cortas = más probable que sea la home del sitio oficial
        if len(path) < 20:
            return 0
        if len(path) < 60:
            return 1
        return 2

    candidates = [
        r for r in results
        if r.get("href") and not _is_blocked(r.get("href", ""))
    ]
    candidates.sort(key=lambda r: _priority(r.get("href", "")))

    for r in candidates:
        url = r.get("href", "")
        text = _scrape_page(url)
        if _is_useful(text):
            return text, url
    return "", ""


def _detect_industry(text: str) -> str:
    keywords = {
        "Banca / Finanzas":         ["banco", "bank", "finanzas", "financiero", "crédito", "seguros", "inversión", "bursátil", "afp", "caja"],
        "Tecnología / Software":    ["software", "tecnología", "tech", "saas", "cloud", "digital", "ia", "ai", "datos", "aplicación", "plataforma"],
        "Salud / Farmacéutico":     ["salud", "médico", "clínica", "hospital", "farmacéutico", "health", "laboratorio", "medicina"],
        "Retail / Consumo masivo":  ["retail", "tienda", "supermercado", "comercio", "venta", "e-commerce", "consumidor"],
        "Manufactura / Industria":  ["manufactura", "fabricación", "producción", "planta", "industrial", "minería", "construcción"],
        "Educación":                ["educación", "universidad", "escuela", "académico", "formación", "instituto"],
        "Energía / Recursos":       ["energía", "petróleo", "gas", "eléctrica", "renovable", "solar", "minería"],
        "Logística / Transporte":   ["logística", "transporte", "supply chain", "distribución", "almacén", "courier"],
        "Telecomunicaciones":       ["telecomunicaciones", "telecom", "internet", "móvil", "red", "fibra"],
        "Consultoría / Servicios":  ["consultoría", "consulting", "asesoría", "advisory", "servicios profesionales"],
        "Alimentos / Bebidas":      ["alimentos", "bebidas", "food", "restaurante", "agro", "agroindustria"],
        "Inmobiliario":             ["inmobiliario", "real estate", "construcción", "vivienda", "edificio"],
    }
    text_lower = text.lower()
    scores = {}
    for industry, terms in keywords.items():
        score = sum(1 for t in terms if t in text_lower)
        if score > 0:
            scores[industry] = score
    if scores:
        return max(scores, key=scores.get)
    return "Servicios Empresariales"


def _extract_employees(text: str) -> str:
    patterns = [
        r"(\d[\d,\.]+)\s*(empleados|trabajadores|colaboradores|employees|personas)",
        r"más de (\d[\d,\.]+)\s*(empleados|personas|trabajadores)",
        r"(\d[\d,\.]+)\+?\s*(empleados|employees|staff)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            num = m.group(1).replace(",", "").replace(".", "")
            return f"{int(num):,}+"
    return "—"


_JUNK_SENTENCE = re.compile(
    r"(cookie|privacy|terms|copyright|all rights reserved|log in|sign up"
    r"|newsletter|suscri|download|keyboard_arrow|visibility \d|description \d"
    r"|©|\bjavascript\b|\bcss\b)",
    re.IGNORECASE,
)


def _clean_summary(text: str, company: str, max_sentences: int = 4) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    clean = [
        s.strip() for s in sentences
        if len(s) > 50
        and not re.search(r"[<>{}\[\]\\|]", s)
        and not s.strip().startswith("http")
        and not _JUNK_SENTENCE.search(s)
    ]
    if not clean:
        return f"{company} es una empresa con presencia en el mercado. Información disponible en fuentes públicas."
    return " ".join(clean[:max_sentences])


# ── Builder principal ──────────────────────────────────────────────────────

def get_company_brief(company: str) -> dict:
    """
    Construye un brief a partir de información pública scrapeada.
    Fallback automático si alguna fuente falla.
    """
    print(f"[scraper] Iniciando búsqueda: {company}")

    # Búsquedas paralelas
    general = _ddg_search(f"{company} empresa quiénes somos historia", max_results=6)
    news    = _ddg_news(company, max_results=5)

    # Scrapeo del mejor resultado disponible
    scraped_text, website_url = _scrape_best(general)

    # Texto combinado para análisis
    search_snippets = " ".join(r.get("body", "") for r in general[:4])
    full_text = f"{scraped_text} {search_snippets}"

    industry  = _detect_industry(full_text)
    employees = _extract_employees(full_text)

    # Resumen: preferir texto scrapeado, fallback a snippets de búsqueda
    summary_source = scraped_text if len(scraped_text) > 200 else search_snippets
    summary = _clean_summary(summary_source, company)

    # Noticias
    news_titles = [n.get("title", "") for n in news if n.get("title")]
    news_context = " | ".join(news_titles[:3]) if news_titles else "Sin noticias recientes detectadas."

    sources = [r.get("href", "") for r in general[:3] if r.get("href") and not _is_blocked(r.get("href", ""))]

    print(f"[scraper] OK — Industria: {industry} | Empleados: {employees} | Noticias: {len(news_titles)}")

    return {
        "company": company,
        "status": "scraped",
        "meeting_type": "virtual",
        "objective": "Reunión de negocio",
        "duration": "1 hora",
        "kam": "KAM Responsable",
        "alert": {
            "level": "info",
            "message": f"Datos obtenidos de fuentes públicas. Noticias recientes: {news_context}",
            "score": 80,
        },
        "executive_summary": summary,
        "client_context": {
            "industry": industry,
            "employees": employees,
            "arr": "—",
            "since": "—",
            "last_interaction": "—",
            "nps_score": "—",
            "ranking": "—",
            "ranking_var": "",
            "tier": "—",
            "tier_label": "Datos internos no disponibles",
            "active_proposals": [],
            "renewal_proposals": [],
            "key_contacts": [],
            "health": {
                "nps":      {"value": "—", "status": "yellow"},
                "contacts": {"value": "—", "status": "yellow"},
                "projects": {"value": "—", "status": "yellow"},
            },
            "website": website_url,
            "sources": sources,
        },
        "key_questions": [
            {"tag": "estrategia",  "question": f"¿Cuáles son los objetivos estratégicos de {company} para este año?",    "detail": "Alinear la propuesta de Neo con sus prioridades de negocio y OKRs."},
            {"tag": "claridad",    "question": "¿Tienen claridad sobre el alcance técnico y entregables esperados?",      "detail": "Resolver dudas sobre metodología, herramientas e integraciones necesarias."},
            {"tag": "contractual", "question": "¿Quiénes son los aprobadores finales y cuál es el proceso de compra?",   "detail": "Identificar si hay comité, legal o finanzas que deba validar la propuesta."},
            {"tag": "relacion",    "question": "¿Han trabajado antes con proveedores de consultoría o tecnología?",       "detail": "Entender su experiencia previa para calibrar expectativas y metodología."},
            {"tag": "estrategia",  "question": f"¿Cómo mide {company} el éxito de este tipo de iniciativa?",            "detail": "Definir métricas de éxito desde el inicio para gestionar expectativas."},
        ],
        "value_hypothesis": [
            f"Acelerar los objetivos de negocio de {company} con soluciones tecnológicas a medida.",
            "Reducir costos operativos mediante automatización e inteligencia de datos.",
            "Mejorar la toma de decisiones con analítica avanzada y visibilidad en tiempo real.",
        ],
        "news": news_titles,
        "sources": sources,
    }
