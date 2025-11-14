# gmail_smtp.py
"""
Very small Gmail sender using SMTP.

You must configure:
  GMAIL_SENDER        = your full Gmail address
  GMAIL_APP_PASSWORD  = app-specific password (NOT your real login)

SMTP is usedinstead of Gmail API to keep dependencies simple.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to: str, subject: str, body_html: str) -> bool:
    sender = os.environ.get("GMAIL_SENDER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender or not app_password:
        raise RuntimeError(
            "GMAIL_SENDER and/or GMAIL_APP_PASSWORD are not set. "
            "Create an App Password in your Google Account and set both env vars."
        )

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject

    part = MIMEText(body_html, "html")
    msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, [to], msg.as_string())

    return True
