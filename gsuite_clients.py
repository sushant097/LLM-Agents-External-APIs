# gsuite_clients.py
"""
Helpers for Google Sheets + Gmail using USER OAuth (installed app).

First run:
  - Opens a browser for you to log in and grant access.
  - Saves token_gsuite.json in the project root.

Subsequent runs:
  - Reuse token_gsuite.json (refreshing automatically when needed).

APIs & Scopes:
  - Google Sheets: create + update spreadsheets
  - Gmail: send email (gmail.send)

Required:
  - credentials.json in project root or GOOGLE_OAUTH_CLIENT_SECRET_FILE env var.
  - Sheets API + Gmail API enabled in your Google Cloud project.
"""

import os
import sys
from typing import Any, Dict, List

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import base64
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

# Combined scopes for Sheets + Gmail send
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]

# Where to find the OAuth client secret
OAUTH_CLIENT_SECRET_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE", "gcp-secret.json")
print(f"[gsuite_clients] Using OAuth client file: {OAUTH_CLIENT_SECRET_FILE}", file=sys.stderr)


# Where to store the user token
TOKEN_FILE = "token_gsuite.json"


def _get_credentials() -> Credentials:
    """
    Get user credentials for Sheets + Gmail.
    - If token_gsuite.json exists, load it.
    - Else run browser OAuth flow once and save token_gsuite.json.
    """
    creds: Credentials | None = None

    # 1) Try existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 2) If no valid creds, refresh or run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # refresh silently
            creds.refresh(Request())
        else:
            # run user consent flow
            if not os.path.exists(OAUTH_CLIENT_SECRET_FILE):
                raise FileNotFoundError(
                    f"Missing OAuth client file: {OAUTH_CLIENT_SECRET_FILE}. "
                    "Download it from Google Cloud Console (OAuth Client for Desktop App)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next time
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


# -------------------- Sheets helpers --------------------

def get_sheets_service():
    creds = _get_credentials()
    # cache_discovery=False to avoid noisy warnings
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def create_or_replace_sheet(
    title: str, header: List[str], rows: List[List[str]]
) -> Dict[str, Any]:
    """
    Create a new spreadsheet named `title` and fill it with header + rows.
    Returns {spreadsheetId, spreadsheetUrl}.
    """
    print(f"[gsuite_clients] Creating spreadsheet with title: {title}", file=sys.stderr)

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


# -------------------- Gmail helpers --------------------

def get_gmail_service():
    creds = _get_credentials()
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def send_email_with_sheet_link(
    to_email: str,
    subject: str,
    sheet_url: str,
    message: str,
) -> str:
    """
    Send an email via Gmail API that contains the given sheet URL.
    The 'from' user will be the Gmail account you authorized in the OAuth flow.
    """
    full_body = f"{message}\n\nGoogle Sheet link: {sheet_url}"
    mime_msg = MIMEText(full_body, "plain", "utf-8")
    mime_msg["to"] = to_email
    mime_msg["subject"] = subject

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")

    service = get_gmail_service()
    sent = service.users().messages().send(
        userId="me",
        body={"raw": raw},
    ).execute()

    msg_id = sent.get("id", "")
    return f"Email sent to {to_email} (message id: {msg_id})"
