from typing import Optional


ACME_BRIEF = {
    "company": "ACME Corp",
    "status": "high_priority",
    "alert": {
        "level": "warning",
        "message": "Contrato de renovación vence en 30 días. Riesgo de churn detectado.",
        "score": 72,
    },
    "executive_summary": (
        "ACME Corp es un cliente enterprise de 3 años con ARR de $240K. "
        "El equipo de tecnología está evaluando alternativas de la competencia tras "
        "incidentes de soporte en Q4. La reunión de mañana es crítica para retener "
        "la cuenta y presentar la hoja de ruta del producto 2026."
    ),
    "client_context": {
        "industry": "Manufactura Industrial",
        "employees": "1,200+",
        "arr": "$240,000",
        "since": "2023",
        "last_interaction": "Queja de soporte — 8 días atrás",
        "nps_score": 34,
        "key_contacts": [
            {"name": "Laura Gómez", "role": "CTO", "sentiment": "neutral"},
            {"name": "Mario Ruiz", "role": "Procurement Lead", "sentiment": "negative"},
            {"name": "Ana Torres", "role": "IT Manager", "sentiment": "positive"},
        ],
    },
    "value_hypothesis": [
        "Reducir el tiempo de onboarding de nuevos proveedores en un 40% con el módulo de integración automatizada.",
        "Ahorrar ~$60K/año en costos operativos al eliminar reconciliaciones manuales.",
        "Mitigar el riesgo regulatorio: cumplimiento ISO 9001 integrado en el flujo de aprobaciones.",
    ],
    "key_questions": [
        "¿Cuál fue el impacto real del incidente de soporte en las operaciones diarias de ACME?",
        "¿Están evaluando activamente a un competidor? ¿Cuál es su timeline de decisión?",
        "¿Qué funcionalidad consideran crítica para renovar y cuál les falta actualmente?",
        "¿Laura Gómez tiene presupuesto aprobado para la renovación o debe pasar por comité?",
        "¿Estarían dispuestos a un piloto del nuevo módulo de integración como parte del acuerdo?",
    ],
}


def get_mock_brief(company: str) -> dict:
    """Return mock brief data. Returns ACME Corp data for any input (demo mode)."""
    normalized = company.strip().upper()
    if "ACME" in normalized or normalized == "":
        return ACME_BRIEF

    # Generic fallback for other companies
    return {
        "company": company,
        "status": "normal",
        "alert": {
            "level": "info",
            "message": "Sin alertas críticas detectadas para esta empresa.",
            "score": 85,
        },
        "executive_summary": f"Datos simulados para {company}. En producción este resumen sería generado por el LLM a partir de CRM, emails y notas previas.",
        "client_context": {
            "industry": "N/A",
            "employees": "N/A",
            "arr": "N/A",
            "since": "N/A",
            "last_interaction": "N/A",
            "nps_score": 0,
            "key_contacts": [],
        },
        "value_hypothesis": [
            "Hipótesis de valor 1: pendiente de datos reales.",
            "Hipótesis de valor 2: pendiente de datos reales.",
        ],
        "key_questions": [
            "¿Cuál es el objetivo principal de esta reunión?",
            "¿Qué problema crítico buscan resolver?",
        ],
    }
