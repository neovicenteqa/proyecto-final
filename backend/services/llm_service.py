import os
import json
import re
import google.generativeai as genai

_client_ready = False


def _get_client():
    global _client_ready
    if not _client_ready:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        genai.configure(api_key=api_key)
        _client_ready = True
    return genai.GenerativeModel("gemini-1.5-flash")


def enrich_brief(company: str, snippets: str, news_titles: list, industry: str) -> dict:
    """
    Llama a Gemini con el contexto scrapeado y devuelve:
      - executive_summary
      - key_questions (lista de 5)
      - value_hypothesis (lista de 3)

    Si falla, devuelve None para que el caller use los valores por defecto.
    """
    model = _get_client()

    news_text = " | ".join(news_titles[:3]) if news_titles else "Sin noticias recientes."

    prompt = f"""Eres un asistente comercial de Neo Consulting, una consultora tecnológica peruana.
Tienes esta información pública sobre la empresa "{company}":

INDUSTRIA DETECTADA: {industry}
NOTICIAS RECIENTES: {news_text}
CONTEXTO WEB:
{snippets[:2000]}

Con esa información genera un brief comercial ejecutivo en español. Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:

{{
  "executive_summary": "Párrafo de 3-4 oraciones describiendo qué hace la empresa, su posición en el mercado y contexto relevante para una reunión comercial.",
  "key_questions": [
    {{"tag": "estrategia",  "question": "Pregunta 1 específica para {company}", "detail": "Por qué hacerla y qué información aporta."}},
    {{"tag": "claridad",    "question": "Pregunta 2 específica para {company}", "detail": "Por qué hacerla y qué información aporta."}},
    {{"tag": "contractual", "question": "Pregunta 3 específica para {company}", "detail": "Por qué hacerla y qué información aporta."}},
    {{"tag": "relacion",    "question": "Pregunta 4 específica para {company}", "detail": "Por qué hacerla y qué información aporta."}},
    {{"tag": "estrategia",  "question": "Pregunta 5 específica para {company}", "detail": "Por qué hacerla y qué información aporta."}}
  ],
  "value_hypothesis": [
    "Propuesta de valor 1 específica para {company} y su industria.",
    "Propuesta de valor 2 específica para {company} y su industria.",
    "Propuesta de valor 3 específica para {company} y su industria."
  ]
}}

Las preguntas y propuestas deben ser específicas para {company}, no genéricas. Usa el contexto de la industria y las noticias recientes."""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Extraer JSON aunque Gemini agregue markdown
        match = re.search(r"\{[\s\S]+\}", raw)
        if not match:
            raise ValueError("No se encontró JSON en la respuesta de Gemini")
        return json.loads(match.group())
    except Exception as e:
        print(f"[llm] Error generando brief con Gemini: {e}")
        return None
