# google_sheets.py
"""
Thin wrapper around Google Sheets API for the MCP SSE server.

Uses a Service Account JSON file pointed to by:
  GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service_account.json

Required scopes are:
  - https://www.googleapis.com/auth/spreadsheets
  - https://www.googleapis.com/auth/drive.file
"""

import os
from typing import List, Dict

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def _get_sheets_service():
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS env var is not set. "
            "It must point to a Service Account JSON file."
        )

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service


def create_sheet(title: str) -> Dict[str, str]:
    """
    Create a new Google Sheet and return its id + url.
    """
    service = _get_sheets_service()

    body = {"properties": {"title": title}}
    resp = (
        service.spreadsheets()
        .create(body=body, fields="spreadsheetId,spreadsheetUrl")
        .execute()
    )

    return {
        "sheet_id": resp["spreadsheetId"],
        "url": resp["spreadsheetUrl"],
    }


def append_rows(sheet_id: str, values: List[List[str]]) -> bool:
    """
    Append rows to an existing sheet at A1 range.
    values is a list of rows, each row is a list of cell strings.
    """
    if not values:
        return True  # nothing to do

    service = _get_sheets_service()

    body = {"values": values}

    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()

    return True
