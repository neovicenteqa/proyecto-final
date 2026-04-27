import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ── Paleta Neo (inline styles para compatibilidad con clientes de correo) ──
_NAVY   = "#000033"
_BLUE   = "#05058c"
_LAVENDER = "#a5a8d8"
_LIGHT_LAV = "#d0d3ee"
_BG     = "#f5f6fa"
_WHITE  = "#ffffff"
_GRAY   = "#595959"


def _section_title(text: str) -> str:
    return (
        f'<div style="font-family:Arial,sans-serif;font-weight:900;font-size:10px;'
        f'letter-spacing:2px;text-transform:uppercase;color:{_BLUE};'
        f'border-bottom:1px solid {_LIGHT_LAV};padding-bottom:8px;margin-bottom:14px;">'
        f'{text}</div>'
    )


def _data_cell(label: str, value: str) -> str:
    return (
        f'<td style="padding:8px;vertical-align:top;width:33%;">'
        f'<div style="background:{_BG};border:1px solid {_LIGHT_LAV};border-radius:6px;padding:10px 12px;">'
        f'<div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;'
        f'color:{_GRAY};margin-bottom:4px;">{label}</div>'
        f'<div style="font-size:13px;font-weight:700;color:{_NAVY};">{value}</div>'
        f'</div></td>'
    )


def _kpi_color(status: str):
    return {
        "red":    ("#fff5f5", "#feb2b2", "#e53e3e"),
        "yellow": ("#fffff0", "#fefcbf", "#d69e2e"),
        "green":  ("#f0fff4", "#9ae6b4", "#2f855a"),
    }.get(status, ("#f5f6fa", "#d0d3ee", "#000033"))


def _build_html(meeting: dict, brief: dict) -> str:
    company  = brief.get("company", meeting.get("company", ""))
    summary  = brief.get("executive_summary", "")
    ctx      = brief.get("client_context", {})
    questions = brief.get("key_questions", [])
    kam      = brief.get("kam", "KAM Responsable")
    objective = brief.get("objective", "—")
    duration  = brief.get("duration", "—")
    mtg_type  = brief.get("meeting_type", "virtual")

    meeting_dt = meeting.get("datetime", "")
    try:
        dt_obj = datetime.fromisoformat(meeting_dt)
        formatted_date = dt_obj.strftime("%A %d de %B %Y")
        formatted_time = dt_obj.strftime("%H:%M")
    except Exception:
        formatted_date = meeting_dt
        formatted_time = ""

    participants = meeting.get("participants", [])
    type_label = "🎥 Virtual" if mtg_type == "virtual" else "📍 Presencial"

    # ── Asistentes ────────────────────────────────────────────────────────
    att_html = (
        f'<span style="font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1px;color:{_GRAY};margin-right:6px;">Neo:</span>'
        f'<span style="background:#eef0fc;border:1px solid {_LIGHT_LAV};border-radius:20px;'
        f'padding:2px 10px;font-size:11px;font-weight:600;color:{_BLUE};margin-right:4px;">'
        f'{kam}</span>'
        f'<span style="font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1px;color:{_GRAY};margin:0 6px;">Cliente:</span>'
    )
    for p in participants:
        att_html += (
            f'<span style="background:#eef0fc;border:1px solid {_LIGHT_LAV};border-radius:20px;'
            f'padding:2px 10px;font-size:11px;font-weight:600;color:{_BLUE};margin-right:4px;">'
            f'{p}</span>'
        )

    # ── Contexto ──────────────────────────────────────────────────────────
    health  = ctx.get("health", {})
    nps_h   = health.get("nps",      {"value": "—", "status": "green"})
    cont_h  = health.get("contacts", {"value": "—", "status": "green"})
    proj_h  = health.get("projects", {"value": "—", "status": "green"})

    def kpi_block(label, h):
        bg, border, color = _kpi_color(h.get("status", "green"))
        return (
            f'<td style="padding:6px;width:33%;vertical-align:top;">'
            f'<div style="background:{bg};border:1px solid {border};border-radius:6px;padding:10px 12px;">'
            f'<div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;'
            f'color:{_GRAY};margin-bottom:6px;">{label}</div>'
            f'<div style="font-size:18px;font-weight:900;color:{color};">{h.get("value","—")}</div>'
            f'</div></td>'
        )

    # ── Propuestas ────────────────────────────────────────────────────────
    active_props = ctx.get("active_proposals", [])
    renewal_props = ctx.get("renewal_proposals", [])

    def proposal_rows(props, badge_bg, badge_color, badge_text):
        if not props:
            return f'<tr><td style="padding:8px 12px;font-size:12px;color:{_GRAY};font-style:italic;">Sin registros</td></tr>'
        rows = ""
        for p in props:
            rows += (
                f'<tr><td style="padding:8px 12px;border-bottom:1px solid {_LIGHT_LAV};">'
                f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td style="font-size:12px;font-weight:700;color:{_NAVY};">{p.get("name","")}</td>'
                f'<td style="font-size:11px;color:{_GRAY};text-align:center;">'
                f'{p.get("start") or p.get("due","")}&nbsp;·&nbsp;{p.get("amount","")}</td>'
                f'<td style="text-align:right;">'
                f'<span style="background:{badge_bg};color:{badge_color};font-size:10px;font-weight:700;'
                f'padding:2px 10px;border-radius:20px;">{badge_text}</span>'
                f'</td></tr></table></td></tr>'
            )
        return rows

    # ── Contactos ─────────────────────────────────────────────────────────
    contacts = ctx.get("key_contacts", [])
    CTAG = {
        "decision":   ("#e8f4ff", "#2b6cb0", "Decisor"),
        "influencer": ("#fef3c7", "#92400e", "Influenciador"),
        "usuario":    ("#f0fff4", "#276749", "Usuario final"),
    }
    contacts_html = ""
    for c in contacts:
        initials = "".join(w[0] for w in c.get("name","").split())[:2].upper()
        ctag = CTAG.get(c.get("type",""), ("#eef0fc", _BLUE, c.get("type","")))
        in_mtg = (
            f'<span style="background:#eef0fc;color:{_BLUE};font-size:10px;font-weight:600;'
            f'padding:1px 8px;border-radius:20px;margin-left:4px;">En reunión</span>'
            if c.get("in_meeting") else ""
        )
        contacts_html += (
            f'<tr><td style="padding:8px 12px;border-bottom:1px solid {_LIGHT_LAV};">'
            f'<table cellpadding="0" cellspacing="0"><tr>'
            f'<td style="width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,{_BLUE},{_LAVENDER});'
            f'color:white;font-weight:900;font-size:13px;text-align:center;vertical-align:middle;'
            f'padding:10px 0;width:38px;">{initials}</td>'
            f'<td style="padding-left:12px;">'
            f'<div style="font-size:13px;font-weight:700;color:{_NAVY};">{c.get("name","")}</div>'
            f'<div style="font-size:11px;color:{_GRAY};">{c.get("role","")} · {c.get("email","")}</div>'
            f'<div style="margin-top:4px;">'
            f'<span style="background:{ctag[0]};color:{ctag[1]};font-size:10px;font-weight:600;'
            f'padding:1px 8px;border-radius:20px;">{ctag[2]}</span>{in_mtg}'
            f'</div></td></tr></table></td></tr>'
        )

    # ── Preguntas ─────────────────────────────────────────────────────────
    PTAG = {
        "contractual": ("#fed7d7", "#c53030", "Contractual"),
        "claridad":    ("#e8f4ff", "#2b6cb0", "Claridad"),
        "estrategia":  ("#f0fff4", "#276749", "Estrategia"),
        "relacion":    ("#fef3c7", "#92400e", "Relación"),
    }
    questions_html = ""
    for i, q in enumerate(questions):
        text = q.get("question", q) if isinstance(q, dict) else q
        detail = q.get("detail", "") if isinstance(q, dict) else ""
        tag_key = q.get("tag", "claridad") if isinstance(q, dict) else "claridad"
        ptag = PTAG.get(tag_key, ("#e8f4ff", "#2b6cb0", tag_key))
        questions_html += (
            f'<tr><td style="padding:10px 12px;border-bottom:1px solid {_LIGHT_LAV};">'
            f'<table cellpadding="0" cellspacing="0"><tr>'
            f'<td style="width:26px;height:26px;border-radius:50%;background:{_BLUE};color:white;'
            f'font-size:11px;font-weight:900;text-align:center;vertical-align:middle;'
            f'padding:6px 0;width:26px;flex-shrink:0;">{i+1}</td>'
            f'<td style="padding-left:12px;">'
            f'<div style="margin-bottom:4px;">'
            f'<span style="background:{ptag[0]};color:{ptag[1]};font-size:9px;font-weight:700;'
            f'letter-spacing:1px;text-transform:uppercase;padding:1px 7px;border-radius:20px;">'
            f'{ptag[2]}</span></div>'
            f'<div style="font-size:12.5px;font-weight:700;color:{_NAVY};margin-bottom:2px;">{text}</div>'
            f'{"<div style=font-size:12px;color:"+_GRAY+";line-height:1.5;>"+detail+"</div>" if detail else ""}'
            f'</td></tr></table></td></tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:{_BG};font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{_BG};padding:24px 16px;">
<tr><td>
<table width="620" cellpadding="0" cellspacing="0" align="center"
       style="background:{_WHITE};border-radius:10px;overflow:hidden;border:1px solid {_LIGHT_LAV};">

  <!-- TOP BAR -->
  <tr>
    <td style="background:{_NAVY};padding:16px 28px;border-bottom:3px solid {_BLUE};">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="color:{_LAVENDER};font-size:18px;font-weight:900;letter-spacing:4px;">NEO</td>
        <td style="text-align:right;color:{_LAVENDER};font-size:10px;font-weight:600;
                   letter-spacing:2px;text-transform:uppercase;">Brief Comercial KAM · Confidencial</td>
      </tr></table>
    </td>
  </tr>

  <!-- CABECERA -->
  <tr>
    <td style="background:linear-gradient(135deg,#f0f2fc,{_WHITE});padding:24px 28px;
               border-bottom:1px solid {_LIGHT_LAV};">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td>
          <div style="font-size:26px;font-weight:700;color:{_BLUE};margin-bottom:8px;">{company}</div>
          <div style="font-size:13px;color:{_NAVY};font-weight:600;margin-bottom:4px;">
            📅 {formatted_date} &nbsp;·&nbsp; 🕐 {formatted_time}
          </div>
        </td>
        <td style="text-align:right;vertical-align:top;">
          <span style="background:#e8f4ff;border:1px solid #7ba3f0;color:{_BLUE};
                       font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
                       padding:4px 12px;border-radius:20px;">{type_label}</span>
          <div style="background:#fffbeb;border:1px solid #f6e05e;border-radius:6px;
                      padding:10px 12px;margin-top:8px;max-width:220px;font-size:11px;color:#744210;">
            <div style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
                        color:#92400e;margin-bottom:6px;">⚠️ Recordatorio antes de entrar</div>
            → Preparar deck / propuesta actualizada<br/>
            → Tener contrato / SOW a mano<br/>
            → Activar grabación (con permiso)<br/>
            → Conexión estable + cámara encendida
          </div>
        </td>
      </tr></table>

      <!-- Asistentes -->
      <div style="margin:16px 0 8px;">
        <div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
                    color:{_BLUE};border-bottom:1px solid {_LIGHT_LAV};padding-bottom:6px;margin-bottom:10px;">
          Asistentes a la reunión
        </div>
        {att_html}
      </div>

      <!-- Meta -->
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-top:1px solid {_LIGHT_LAV};padding-top:14px;margin-top:14px;">
        <tr>
          {_data_cell("Objetivo de la reunión", objective)}
          {_data_cell("KAM Responsable", kam)}
          {_data_cell("Tiempo estimado", duration)}
        </tr>
      </table>
    </td>
  </tr>

  <!-- RESUMEN EJECUTIVO -->
  <tr>
    <td style="padding:20px 28px;border-bottom:1px solid {_LIGHT_LAV};
               border-left:4px solid {_BLUE};">
      {_section_title("Resumen Ejecutivo")}
      <div style="font-size:14px;line-height:1.7;color:{_NAVY};
                  border-left:3px solid {_LAVENDER};padding-left:12px;">
        {summary}
      </div>
    </td>
  </tr>

  <!-- CONTEXTO DEL CLIENTE -->
  <tr>
    <td style="padding:20px 28px;border-bottom:1px solid {_LIGHT_LAV};">
      {_section_title("Contexto de la Empresa")}
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
        <tr>
          {_data_cell("Industria", ctx.get("industry","—"))}
          {_data_cell("NPS Score", str(ctx.get("nps_score","—")))}
          {_data_cell("N° Empleados", ctx.get("employees","—"))}
        </tr>
      </table>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          {_data_cell("Ranking en Cartera", ctx.get("ranking","—") + " " + ctx.get("ranking_var",""))}
          {_data_cell("Tier", "TIER " + ctx.get("tier","—") + " · " + ctx.get("tier_label",""))}
          {_data_cell("ARR", ctx.get("arr","—"))}
        </tr>
      </table>
    </td>
  </tr>

  <!-- SEMÁFORO DE SALUD -->
  <tr>
    <td style="padding:20px 28px;border-bottom:1px solid {_LIGHT_LAV};">
      {_section_title("Indicadores de Salud")}
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          {kpi_block("NPS Score", nps_h)}
          {kpi_block("Contactos Activos", cont_h)}
          {kpi_block("Proyectos Activos", proj_h)}
        </tr>
      </table>
    </td>
  </tr>

  <!-- PROPUESTAS -->
  <tr>
    <td style="padding:20px 28px;border-bottom:1px solid {_LIGHT_LAV};">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="width:50%;padding-right:8px;vertical-align:top;">
          {_section_title("Propuestas Activas")}
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:{_BG};border:1px solid {_LIGHT_LAV};border-radius:6px;">
            {proposal_rows(active_props, "#c6f6d5", "#276749", "Activa")}
          </table>
        </td>
        <td style="width:50%;padding-left:8px;vertical-align:top;">
          {_section_title("Propuestas por Renovar")}
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:{_BG};border:1px solid {_LIGHT_LAV};border-radius:6px;">
            {proposal_rows(renewal_props, "#fefcbf", "#744210", "Por renovar")}
          </table>
        </td>
      </tr></table>
    </td>
  </tr>

  <!-- CONTACTOS CLAVE -->
  <tr>
    <td style="padding:20px 28px;border-bottom:1px solid {_LIGHT_LAV};">
      {_section_title("Contactos Clave del Cliente")}
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:{_BG};border:1px solid {_LIGHT_LAV};border-radius:6px;">
        {contacts_html or f'<tr><td style="padding:12px;font-size:12px;color:{_GRAY};font-style:italic;">Sin contactos registrados</td></tr>'}
      </table>
    </td>
  </tr>

  <!-- PREGUNTAS CLAVE -->
  <tr>
    <td style="padding:20px 28px;border-bottom:1px solid {_LIGHT_LAV};">
      {_section_title("Preguntas Clave para la Reunión")}
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:{_BG};border:1px solid {_LIGHT_LAV};border-radius:6px;">
        {questions_html}
      </table>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:{_NAVY};padding:14px 28px;text-align:center;">
      <span style="color:{_LAVENDER};font-size:10px;font-weight:600;letter-spacing:1px;">
        Brief generado para uso interno · No compartir con el cliente &nbsp;·&nbsp; NEO CONSULTING · AI BRIEF v2.0
      </span>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def send_brief_email(to_email: str, meeting: dict, brief: dict) -> None:
    """Send the AI brief HTML email via SMTP."""
    smtp_host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port     = int(os.getenv("SMTP_PORT", "587"))
    smtp_user     = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    company = brief.get("company", meeting.get("company", "Reunión"))
    subject = f"Brief Comercial KAM — Reunión con {company} · Neo Consulting"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Neo AI Brief <{smtp_user}>"
    msg["To"]      = to_email

    msg.attach(MIMEText(_build_html(meeting, brief), "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())

    print(f"[email] Brief enviado a {to_email} — {company}")
