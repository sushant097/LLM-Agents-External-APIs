# gsuite_clients.py
"""
Helpers for Google Sheets + Gmail.

Uses a Service Account JSON file pointed to by:
  GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service_account.json

Sheets:
  - create_or_replace_sheet(title, header, rows)

Gmail:
  - send_email_with_sheet_link(to_email, subject, sheet_url, message)
"""

import os
from typing import Any, Dict, List

from google.oauth2 import service_account
from googleapiclient.discovery import build

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
GMAIL_SENDER = os.getenv("GMAIL_SENDER_EMAIL")


def _get_credentials(scopes: List[str]):
    if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise RuntimeError(
            "Service account file not found. "
            "Set GOOGLE_SERVICE_ACCOUNT_FILE to your .json key file."
        )
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes
    )


def get_sheets_service():
    creds = _get_credentials(SHEETS_SCOPES)
    return build("sheets", "v4", credentials=creds)


def get_gmail_service():
    creds = _get_credentials(GMAIL_SCOPES)
    return build("gmail", "v1", credentials=creds)


def create_or_replace_sheet(
    title: str, header: List[str], rows: List[List[str]]
) -> Dict[str, Any]:
    """
    Create a new spreadsheet named `title` and fill it with header + rows.
    Returns {spreadsheetId, spreadsheetUrl}.
    """
    service = get_sheets_service()

    spreadsheet_body = {"properties": {"title": title}}

    sheet = (
        service.spreadsheets()
        .create(body=spreadsheet_body, fields="spreadsheetId,spreadsheetUrl")
        .execute()
    )

    values = [header] + rows
    data = {
        "range": "Sheet1!A1",
        "values": values,
    }

    body = {"valueInputOption": "RAW", "data": [data]}
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet["spreadsheetId"],
        body=body,
    ).execute()

    return {
        "spreadsheetId": sheet["spreadsheetId"],
        "spreadsheetUrl": sheet["spreadsheetUrl"],
    }


def send_email_with_sheet_link(
    to_email: str, subject: str, sheet_url: str, message: str
) -> str:
    """
    Send an email using Gmail API that contains the given sheet URL.
    """
    from email.mime.text import MIMEText
    import base64

    # If sender not set, just send as `me` (the service account / delegated user)
    sender = GMAIL_SENDER or to_email

    body_text = f"{message}\n\nGoogle Sheet link: {sheet_url}"
    mime_msg = MIMEText(body_text)
    mime_msg["to"] = to_email
    mime_msg["from"] = sender
    mime_msg["subject"] = subject

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")

    gmail = get_gmail_service()
    gmail.users().messages().send(userId="me", body={"raw": raw}).execute()

    return f"Email sent to {to_email} with link {sheet_url}"
