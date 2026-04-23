ACME_BRIEF = {
    "company": "ACME Corp",
    "status": "high_priority",
    "meeting_type": "virtual",
    "objective": "Renovación de contrato y presentación de propuesta IA",
    "duration": "1 hora",
    "kam": "Vicente Quijandria",
    "alert": {
        "level": "warning",
        "message": "Contrato de renovación vence en 30 días. Riesgo de churn detectado.",
        "score": 72,
    },
    "executive_summary": (
        "ACME Corp es un cliente enterprise de 3 años con ARR de S/ 240,000. "
        "El equipo de tecnología está evaluando alternativas de la competencia tras "
        "incidentes de soporte en Q4. La reunión es crítica para retener la cuenta "
        "y presentar la hoja de ruta del producto 2026 antes del cierre de Q2."
    ),
    "client_context": {
        "industry": "Manufactura Industrial",
        "employees": "1,200+",
        "arr": "S/ 240,000",
        "since": "2023",
        "last_interaction": "Queja de soporte — 8 días atrás",
        "nps_score": 6.2,
        "ranking": "#3",
        "ranking_var": "+12% vs año anterior",
        "tier": "A",
        "tier_label": "Marca consolidada",
        "active_proposals": [
            {"name": "Agente de Consulta IA", "start": "03/2025", "amount": "S/ 45,000"},
            {"name": "Dashboard Analytics", "start": "01/2025", "amount": "S/ 28,000"},
        ],
        "renewal_proposals": [
            {"name": "Soporte & Mantenimiento", "due": "30/05/2025", "amount": "S/ 12,000"},
            {"name": "Licencias Power BI", "due": "15/06/2025", "amount": "S/ 8,500"},
        ],
        "key_contacts": [
            {"name": "Laura Gómez",  "role": "CTO",              "email": "lgomez@acme.com",  "type": "decision",   "in_meeting": True},
            {"name": "Mario Ruiz",   "role": "Procurement Lead",  "email": "mruiz@acme.com",   "type": "influencer", "in_meeting": True},
            {"name": "Ana Torres",   "role": "IT Manager",        "email": "atorres@acme.com", "type": "usuario",    "in_meeting": False},
        ],
        "health": {
            "nps":      {"value": 6.2, "status": "yellow"},
            "contacts": {"value": 3,   "status": "yellow"},
            "projects": {"value": 2,   "status": "yellow"},
        },
    },
    "key_questions": [
        {"tag": "contractual", "question": "¿Cuál fue el impacto real del incidente de soporte en las operaciones de ACME?",          "detail": "Cuantificar pérdidas o fricciones generadas para dimensionar compensación o gesto comercial."},
        {"tag": "claridad",    "question": "¿Están evaluando activamente a un competidor? ¿Cuál es su timeline de decisión?",         "detail": "Identificar urgencia real y si hay un proceso de licitación en curso."},
        {"tag": "estrategia",  "question": "¿Esta propuesta de IA responde al objetivo de negocio principal de ACME para 2025?",      "detail": "Confirmar alineación con OKRs y presupuesto aprobado por el board."},
        {"tag": "relacion",    "question": "¿Laura Gómez tiene presupuesto aprobado para la renovación o debe pasar por comité?",     "detail": "Definir quiénes son los aprobadores finales y el proceso interno de validación."},
        {"tag": "contractual", "question": "¿Estarían dispuestos a un piloto del módulo de integración como parte del acuerdo?",      "detail": "Explorar si un entregable rápido (30 días) puede destrabar la decisión de renovación."},
    ],
    "value_hypothesis": [
        "Reducir el tiempo de onboarding de nuevos proveedores en un 40% con el módulo de integración automatizada.",
        "Ahorrar ~$60K/año en costos operativos al eliminar reconciliaciones manuales.",
        "Mitigar el riesgo regulatorio: cumplimiento ISO 9001 integrado en el flujo de aprobaciones.",
    ],
}


def get_mock_brief(company: str) -> dict:
    """Return mock brief. Returns ACME Corp data for any input (demo mode)."""
    normalized = company.strip().upper()
    if "ACME" in normalized or normalized == "":
        return ACME_BRIEF

    return {
        "company": company,
        "status": "normal",
        "meeting_type": "virtual",
        "objective": "Reunión de seguimiento",
        "duration": "45 min",
        "kam": "KAM Responsable",
        "alert": {
            "level": "info",
            "message": "Sin alertas críticas detectadas.",
            "score": 85,
        },
        "executive_summary": (
            f"Datos simulados para {company}. "
            "En producción este resumen sería generado por el LLM a partir de CRM, emails y notas previas."
        ),
        "client_context": {
            "industry": "—",
            "employees": "—",
            "arr": "—",
            "since": "—",
            "last_interaction": "—",
            "nps_score": 0,
            "ranking": "—",
            "ranking_var": "—",
            "tier": "—",
            "tier_label": "—",
            "active_proposals": [],
            "renewal_proposals": [],
            "key_contacts": [],
            "health": {
                "nps":      {"value": 0, "status": "green"},
                "contacts": {"value": 0, "status": "red"},
                "projects": {"value": 0, "status": "red"},
            },
        },
        "key_questions": [
            {"tag": "estrategia", "question": "¿Cuál es el objetivo principal de esta reunión?",  "detail": ""},
            {"tag": "claridad",   "question": "¿Qué problema crítico buscan resolver?",           "detail": ""},
        ],
        "value_hypothesis": [],
    }
