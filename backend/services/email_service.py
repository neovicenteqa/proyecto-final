import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def _build_html(meeting: dict, brief: dict) -> str:
    company = brief.get("company", meeting.get("company", ""))
    summary = brief.get("executive_summary", "")
    alert = brief.get("alert", {})
    ctx = brief.get("client_context", {})
    hypotheses = brief.get("value_hypothesis", [])
    questions = brief.get("key_questions", [])

    # Participants
    participants_html = "".join(
        f'<span style="display:inline-block;background:#1e293b;color:#94a3b8;'
        f'border-radius:4px;padding:2px 8px;margin:2px;font-size:12px;">{p}</span>'
        for p in meeting.get("participants", [])
    )

    # Alert block
    alert_color = "#f59e0b" if alert.get("level") == "warning" else "#3b82f6"
    alert_html = f"""
    <div style="background:#1a1a2e;border-left:4px solid {alert_color};
                border-radius:6px;padding:14px 16px;margin-bottom:20px;">
      <div style="color:{alert_color};font-size:11px;font-weight:700;
                  letter-spacing:1px;margin-bottom:6px;">
        ⚠ ALERTA — HEALTH SCORE: {alert.get("score", "—")}
      </div>
      <div style="color:#e2e8f0;font-size:14px;">{alert.get("message","")}</div>
    </div>
    """

    # Value hypotheses
    hyp_rows = "".join(
        f'<tr><td style="padding:8px 12px;border-bottom:1px solid #1e293b;color:#e2e8f0;font-size:13px;">'
        f'<span style="color:#3b82f6;font-weight:700;margin-right:8px;">H{i+1}</span>{h}</td></tr>'
        for i, h in enumerate(hypotheses)
    )

    # Key questions
    q_rows = "".join(
        f'<tr><td style="padding:8px 12px;border-bottom:1px solid #1e293b;color:#e2e8f0;font-size:13px;">'
        f'<span style="color:#64748b;font-weight:700;margin-right:8px;">{i+1}.</span>{q}</td></tr>'
        for i, q in enumerate(questions)
    )

    # Context items
    ctx_items = [
        ("Industria", ctx.get("industry", "—")),
        ("ARR", ctx.get("arr", "—")),
        ("Cliente desde", ctx.get("since", "—")),
        ("NPS Score", str(ctx.get("nps_score", "—"))),
        ("Último contacto", ctx.get("last_interaction", "—")),
    ]
    ctx_html = "".join(
        f'<td style="padding:8px;text-align:center;width:20%;">'
        f'<div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.5px;'
        f'margin-bottom:4px;">{label}</div>'
        f'<div style="color:#f1f5f9;font-size:13px;font-weight:600;">{value}</div></td>'
        for label, value in ctx_items
    )

    meeting_dt = meeting.get("datetime", "")
    try:
        formatted_dt = datetime.fromisoformat(meeting_dt).strftime("%d %b %Y, %H:%M")
    except Exception:
        formatted_dt = meeting_dt

    return f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;padding:32px 16px;">
<tr><td>
<table width="620" cellpadding="0" cellspacing="0" align="center"
       style="background:#1e293b;border-radius:12px;overflow:hidden;border:1px solid #334155;">

  <!-- Header -->
  <tr>
    <td style="background:linear-gradient(135deg,#1e293b,#0f2444);padding:28px 32px;
               border-bottom:1px solid #334155;">
      <div style="display:flex;align-items:center;">
        <div style="background:#3b82f6;border-radius:8px;width:36px;height:36px;
                    display:inline-block;text-align:center;line-height:36px;
                    font-size:18px;margin-right:12px;">⚡</div>
        <div style="display:inline-block;vertical-align:middle;">
          <div style="color:#f1f5f9;font-size:16px;font-weight:700;">AI Brief</div>
          <div style="color:#64748b;font-size:12px;">Smart Meeting Prep</div>
        </div>
        <div style="float:right;background:rgba(59,130,246,.15);border:1px solid #3b82f6;
                    color:#3b82f6;font-size:11px;font-weight:700;padding:4px 12px;
                    border-radius:20px;letter-spacing:.5px;">24H ANTES</div>
      </div>
    </td>
  </tr>

  <!-- Meeting info -->
  <tr>
    <td style="padding:24px 32px 0;">
      <div style="color:#3b82f6;font-size:11px;font-weight:700;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:8px;">Reunión programada</div>
      <div style="color:#f1f5f9;font-size:22px;font-weight:700;margin-bottom:12px;">
        {company}
      </div>
      <div style="margin-bottom:8px;">
        <span style="color:#64748b;font-size:12px;">📅 </span>
        <span style="color:#94a3b8;font-size:13px;">{formatted_dt}</span>
      </div>
      <div style="margin-bottom:20px;">
        <span style="color:#64748b;font-size:12px;">👥 </span>
        {participants_html}
      </div>
    </td>
  </tr>

  <!-- Alert -->
  <tr><td style="padding:0 32px;">{alert_html}</td></tr>

  <!-- Executive Summary -->
  <tr>
    <td style="padding:0 32px 20px;">
      <div style="color:#3b82f6;font-size:11px;font-weight:700;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:10px;padding-bottom:6px;
                  border-bottom:1px solid #334155;">Resumen Ejecutivo</div>
      <div style="color:#cbd5e1;font-size:14px;line-height:1.7;">{summary}</div>
    </td>
  </tr>

  <!-- Context -->
  <tr>
    <td style="padding:0 32px 20px;">
      <div style="color:#3b82f6;font-size:11px;font-weight:700;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:10px;padding-bottom:6px;
                  border-bottom:1px solid #334155;">Contexto del Cliente</div>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#0f172a;border-radius:8px;border:1px solid #334155;">
        <tr>{ctx_html}</tr>
      </table>
    </td>
  </tr>

  <!-- Value Hypothesis -->
  <tr>
    <td style="padding:0 32px 20px;">
      <div style="color:#3b82f6;font-size:11px;font-weight:700;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:10px;padding-bottom:6px;
                  border-bottom:1px solid #334155;">Hipótesis de Valor</div>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#0f172a;border-radius:8px;border:1px solid #334155;">
        {hyp_rows}
      </table>
    </td>
  </tr>

  <!-- Key Questions -->
  <tr>
    <td style="padding:0 32px 28px;">
      <div style="color:#3b82f6;font-size:11px;font-weight:700;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:10px;padding-bottom:6px;
                  border-bottom:1px solid #334155;">Preguntas Clave</div>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#0f172a;border-radius:8px;border:1px solid #334155;">
        {q_rows}
      </table>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#0f172a;padding:16px 32px;border-top:1px solid #334155;
               text-align:center;color:#475569;font-size:11px;">
      Generado automáticamente por AI Brief · Smart Meeting Prep
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>
"""


def send_brief_email(to_email: str, meeting: dict, brief: dict) -> None:
    """Send the AI brief HTML email via SMTP."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    company = brief.get("company", meeting.get("company", "Reunión"))
    subject = f"⚡ AI Brief: Reunión con {company} — mañana"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI Brief <{smtp_user}>"
    msg["To"] = to_email

    html_body = _build_html(meeting, brief)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())

    print(f"[email] Brief enviado a {to_email} para reunión con {company}")
