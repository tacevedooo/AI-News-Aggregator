"""Send digest email via SMTP (stdlib smtplib)."""

from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Iterable

from app.models import ArticleSummary


def build_plain_body(summaries: Iterable[ArticleSummary], subject_line: str) -> str:
    lines = [subject_line, "=" * len(subject_line), ""]
    for s in summaries:
        lines.append(s.name)
        lines.append(s.link)
        if s.error:
            lines.append(f"[LLM error] {s.error}")
        lines.append("")
        lines.append(s.summary or "(no summary)")
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
    return "\n".join(lines).strip()


def build_html_body(summaries: Iterable[ArticleSummary], subject_line: str) -> str:
    parts = [
        "<html><body>",
        f"<h1>{escape(subject_line)}</h1>",
    ]
    for s in summaries:
        parts.append("<hr/>")
        parts.append(f"<h2>{escape(s.name)}</h2>")
        parts.append(f'<p><a href="{escape(s.link)}">{escape(s.link)}</a></p>')
        if s.timestamp:
            parts.append(f"<p><small>{escape(s.timestamp)}</small></p>")
        if s.source:
            parts.append(f"<p><small>Source: {escape(s.source)}</small></p>")
        if s.error:
            parts.append(f"<p><strong>Error:</strong> {escape(s.error)}</p>")
        # summary may contain markdown-ish text; keep as preformatted for safety
        parts.append(f"<pre style='white-space:pre-wrap;font-family:sans-serif'>{escape(s.summary or '')}</pre>")
    parts.append("</body></html>")
    return "\n".join(parts)


def send_digest_email(
    summaries: list[ArticleSummary],
    *,
    subject: str | None = None,
) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    mail_from = os.getenv("EMAIL_FROM", user).strip()
    to_raw = os.getenv("EMAIL_TO", "").strip()
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
    # Gmail: 587 + STARTTLS (default), or 465 + implicit SSL (set SMTP_USE_SSL=true).
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")

    if not host or not mail_from or not to_raw:
        raise RuntimeError(
            "Email not configured: set SMTP_HOST, EMAIL_FROM, EMAIL_TO (and usually SMTP_USER/SMTP_PASSWORD)."
        )

    recipients = [e.strip() for e in to_raw.split(",") if e.strip()]
    subj = subject or os.getenv("EMAIL_SUBJECT", "AI News digest")

    plain = build_plain_body(summaries, subj)
    html = build_html_body(summaries, subj)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subj
    msg["From"] = mail_from
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    context = ssl.create_default_context()
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as server:
            if user and password:
                server.login(user, password)
            server.sendmail(mail_from, recipients, msg.as_string())
    else:
        with smtplib.SMTP(host, port, timeout=30) as server:
            if use_tls:
                server.starttls(context=context)
            if user and password:
                server.login(user, password)
            server.sendmail(mail_from, recipients, msg.as_string())
