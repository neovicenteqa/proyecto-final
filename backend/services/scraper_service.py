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

BLOCKED_DOMAINS = [
    "datosperu.org", "linkedin.com", "facebook.com",
    "instagram.com", "twitter.com", "x.com",
    "academia.edu", "scribd.com", "slideshare.net",
    "researchgate.net", "issuu.com", "docsity.com",
    "monografias.com", "gestiopolis.com", "buenastareas.com",
    "youtube.com", "youtu.be", "tiktok.com",
    "wikipedia.org",
    # Comparadores / agregadores
    "comparaenvios.com", "comparabien.com", "rankia.pe", "rankia.com",
    "cuida-tu-dinero.com", "banktrack.com", "helpmycash.com",
    "remitly.com", "wise.com", "sendwave.com",
    "empresite.eleconomista", "infocif.es", "einforma.com",
    "dnb.com", "manta.com", "zoominfo.com", "crunchbase.com",
]

_JUNK_SNIPPET = re.compile(
    r"(▷|【|】|★|☆|✓|Log In|Sign Up|Sign In|Cookie|Privacy Policy"
    r"|Terms of Service|Newsletter|Download PDF|keyboard_arrow"
    r"|©|Compara Comisiones|Mejores Tarifas|Envíos de Dinero)",
    re.IGNORECASE,
)

_JUNK_SENTENCE = re.compile(
    r"(cookie|privacy|terms|copyright|all rights reserved|log in|sign up"
    r"|newsletter|suscri|download|keyboard_arrow|©|\bjavascript\b|\bcss\b"
    r"|▷|【|】|Compara|Mejores Tarifas)",
    re.IGNORECASE,
)


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


def _good_snippets(results: list) -> str:
    """Snippets solo de dominios no bloqueados y sin texto basura."""
    parts = []
    for r in results:
        url  = r.get("href", "")
        body = r.get("body", "").strip()
        if not body or not url:
            continue
        if _is_blocked(url):
            continue
        if _JUNK_SNIPPET.search(body):
            continue
        parts.append(body)
    return " ".join(parts)


def _scrape_page(url: str, max_chars: int = 5000) -> str:
    if _is_blocked(url):
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        # Preferir párrafos de contenido
        paragraphs = soup.find_all("p")
        if paragraphs:
            text = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)
        else:
            text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text[:max_chars]
    except Exception as e:
        print(f"[scraper] Error scraping {url}: {e}")
        return ""


def _scrape_best(results: list) -> tuple[str, str]:
    candidates = [r for r in results if r.get("href") and not _is_blocked(r.get("href", ""))]
    for r in candidates:
        url = r.get("href", "")
        text = _scrape_page(url)
        if len(text) > 200 and not _JUNK_SNIPPET.search(text[:300]):
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
    return max(scores, key=scores.get) if scores else "Servicios Empresariales"


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
            try:
                return f"{int(num):,}+"
            except ValueError:
                continue
    return "—"


def _clean_summary(text: str, company: str, max_sentences: int = 4) -> str:
    # Dividir en oraciones (punto, signo de exclamación/interrogación, o elipsis)
    sentences = re.split(r"(?<=[.!?])\s+|(?<=\.\.\.)\s+", text.strip())
    clean = [
        s.strip() for s in sentences
        if len(s) > 40
        and not re.search(r"[<>{}\[\]\\|▷【】]", s)
        and not s.strip().startswith("http")
        and not _JUNK_SENTENCE.search(s)
    ]
    if not clean:
        return f"{company} es una empresa con presencia en el mercado. Información disponible en fuentes públicas."
    return " ".join(clean[:max_sentences])


# ── Builder principal ──────────────────────────────────────────────────────

def get_company_brief(company: str) -> dict:
    print(f"[scraper] Iniciando búsqueda: {company}")

    general = _ddg_search(f"{company} empresa historia quiénes somos", max_results=8)
    news    = _ddg_news(company, max_results=5)

    # Snippets filtrados (sin dominios basura, sin texto con símbolos raros)
    snippets = _good_snippets(general)

    # Scrapear solo si los snippets no son suficientes
    scraped_text, website_url = "", ""
    if len(snippets) < 300:
        scraped_text, website_url = _scrape_best(general)

    # Si no hay website_url del scraping, tomar el primer dominio no bloqueado
    if not website_url:
        for r in general:
            href = r.get("href", "")
            if href and not _is_blocked(href):
                website_url = href
                break

    full_text = f"{snippets} {scraped_text}"
    industry  = _detect_industry(full_text)
    employees = _extract_employees(full_text)

    # Resumen desde snippets filtrados
    summary_source = snippets if len(snippets) > 100 else scraped_text
    summary = _clean_summary(summary_source, company)

    news_titles  = [n.get("title", "") for n in news if n.get("title")]
    news_context = " | ".join(news_titles[:3]) if news_titles else "Sin noticias recientes detectadas."
    sources      = [r.get("href", "") for r in general[:4] if r.get("href") and not _is_blocked(r.get("href", ""))]

    # Enriquecer con LLM (Gemini) — fallback a valores scrapeados si falla
    llm_data = None
    try:
        from services.llm_service import enrich_brief
        llm_data = enrich_brief(company, snippets, news_titles, industry)
    except Exception as e:
        print(f"[llm] No disponible, usando datos scrapeados: {e}")

    executive_summary = llm_data.get("executive_summary", summary)   if llm_data else summary
    key_questions     = llm_data.get("key_questions",     [])        if llm_data else None
    value_hypothesis  = llm_data.get("value_hypothesis",  [])        if llm_data else None

    print(f"[scraper] OK — Industria: {industry} | Empleados: {employees} | LLM: {'sí' if llm_data else 'no'}")

    default_questions = [
        {"tag": "estrategia",  "question": f"¿Cuáles son los objetivos estratégicos de {company} para este año?",   "detail": "Alinear la propuesta de Neo con sus prioridades de negocio y OKRs."},
        {"tag": "claridad",    "question": "¿Tienen claridad sobre el alcance técnico y entregables esperados?",     "detail": "Resolver dudas sobre metodología, herramientas e integraciones necesarias."},
        {"tag": "contractual", "question": "¿Quiénes son los aprobadores finales y cuál es el proceso de compra?",  "detail": "Identificar si hay comité, legal o finanzas que deba validar la propuesta."},
        {"tag": "relacion",    "question": "¿Han trabajado antes con proveedores de consultoría o tecnología?",      "detail": "Entender su experiencia previa para calibrar expectativas y metodología."},
        {"tag": "estrategia",  "question": f"¿Cómo mide {company} el éxito de este tipo de iniciativa?",           "detail": "Definir métricas de éxito desde el inicio para gestionar expectativas."},
    ]
    default_hypothesis = [
        f"Acelerar los objetivos de negocio de {company} con soluciones tecnológicas a medida.",
        "Reducir costos operativos mediante automatización e inteligencia de datos.",
        "Mejorar la toma de decisiones con analítica avanzada y visibilidad en tiempo real.",
    ]

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
        "executive_summary": executive_summary,
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
        "key_questions":  key_questions  or default_questions,
        "value_hypothesis": value_hypothesis or default_hypothesis,
        "news": news_titles,
        "sources": sources,
    }
