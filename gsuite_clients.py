# gsuite_clients.py
"""
Helpers for Google Sheets + Gmail using USER OAuth for Sheets and SMTP for Gmail.

Sheets:
  - Uses OAuth "installed app" flow once in browser.
  - Stores a token in token_sheets.json in the project root.

Gmail:
  - Uses SMTP with an App Password.

Required env vars:

  GOOGLE_OAUTH_CLIENT_SECRET_FILE=/absolute/path/to/oauth_client_secret.json
  GMAIL_SENDER_EMAIL=you@gmail.com
  GMAIL_APP_PASSWORD=16_char_app_password
"""

import os
from typing import Any, Dict, List

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# -------------------- Sheets via USER OAuth --------------------

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
OAUTH_CLIENT_SECRET_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE", "")
TOKEN_FILE = "token_sheets.json"


def _get_sheets_credentials() -> Credentials:
    """
    Get user credentials for Google Sheets:
    - If token_sheets.json exists, load it.
    - Else run browser OAuth flow once and save token_sheets.json.
    """
    creds: Credentials | None = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SHEETS_SCOPES)

    # If there are no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Try to refresh silently
            creds.refresh(Request())
        else:
            if not OAUTH_CLIENT_SECRET_FILE or not os.path.exists(OAUTH_CLIENT_SECRET_FILE):
                raise RuntimeError(
                    "OAuth client secret file not found. "
                    "Set GOOGLE_OAUTH_CLIENT_SECRET_FILE to your OAuth client JSON."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CLIENT_SECRET_FILE, SHEETS_SCOPES
            )
            # This will open a browser the first time
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


def get_sheets_service():
    creds = _get_sheets_credentials()
    return build("sheets", "v4", credentials=creds)


def create_or_replace_sheet(
    title: str, header: List[str], rows: List[List[str]]
) -> Dict[str, Any]:
    """
    Create a new spreadsheet named `title` and fill it with header + rows.
    Returns {spreadsheetId, spreadsheetUrl}.
    """
    print(f"DEBUG: creating spreadsheet with title: {title}")
    service = get_sheets_service()

    spreadsheet_body = {"properties": {"title": title}}

    sheet = (
        service.spreadsheets()
        .create(body=spreadsheet_body, fields="spreadsheetId,spreadsheetUrl")
        .execute()
    )

    values = [header] + rows
    data = {"range": "Sheet1!A1", "values": values}
    body = {"valueInputOption": "RAW", "data": [data]}

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet["spreadsheetId"],
        body=body,
    ).execute()

    return {
        "spreadsheetId": sheet["spreadsheetId"],
        "spreadsheetUrl": sheet["spreadsheetUrl"],
    }


# -------------------- Gmail via SMTP + App Password --------------------

import smtplib
from email.mime.text import MIMEText

GMAIL_SENDER = os.getenv("GMAIL_SENDER_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email_with_sheet_link(
    to_email: str, subject: str, sheet_url: str, message: str
) -> str:
    """
    Send an email that contains the given sheet URL using Gmail SMTP.
    """
    if not (GMAIL_SENDER and GMAIL_APP_PASSWORD):
        raise RuntimeError(
            "GMAIL_SENDER_EMAIL and/or GMAIL_APP_PASSWORD not set in environment."
        )

    body_text = f"{message}\n\nGoogle Sheet link: {sheet_url}"
    msg = MIMEText(body_text, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    return f"Email sent to {to_email} with link {sheet_url}"
