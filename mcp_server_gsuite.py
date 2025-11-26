"""
MCP server exposing Google Sheets + Gmail tools using USER OAuth.

Tools:
  - create_sheet(title, header, rows) -> CreateSheetOutput
  - send_sheet_link_email(...) -> SendEmailOutput

These internally call gsuite_clients.create_or_replace_sheet and
gsuite_clients.send_email_with_sheet_link.
"""

import sys
import re
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from gsuite_clients import create_or_replace_sheet, send_email_with_sheet_link


# ======== Pydantic models for outputs ========

class CreateSheetOutput(BaseModel):
    spreadsheet_id: str
    spreadsheet_url: str


class SendEmailOutput(BaseModel):
    status: str


mcp = FastMCP("gsuite-tools")


@mcp.tool()
def create_sheet(
    title: str,
    header: List[str],
    rows: List[List[str]],
) -> CreateSheetOutput:
    """
    Create a Google Sheet and populate it with header + rows.

    Example usage:
      title: "MCP GSuite Test"
      header: ["Pos", "Driver", "Team", "Points"]
      rows: [["1", "Test Driver", "Test Team", "123"]]
    """
    result = create_or_replace_sheet(
        title=title,
        header=header,
        rows=rows,
    )
    return CreateSheetOutput(
        spreadsheet_id=result["spreadsheetId"],
        spreadsheet_url=result["spreadsheetUrl"],
    )


@mcp.tool()
def send_sheet_link_email(
    # LLM sometimes uses `recipient_email`, sometimes `to_email`
    to_email: Optional[str] = None,
    recipient_email: Optional[str] = None,
    # It sometimes omits sheet_url and just embeds it in message
    sheet_url: Optional[str] = None,
    subject: str = "F1 Standings Google Sheet Link",
    message: str = "Here is the link to the F1 Standings Google Sheet.",
) -> SendEmailOutput:
    """
    Send an email with the Google Sheet link.

    This signature is intentionally forgiving:

    - The model may call:
        send_sheet_link_email|recipient_email="..."|sheet_url="..."
      OR:
        send_sheet_link_email|to_email="..."|subject="..."|message="...<url>..."
      Both patterns are supported.

    - We resolve the actual recipient from `to_email` or `recipient_email`.
    - If sheet_url is missing, we try to extract it from the message text.
    """
    # 1) Resolve recipient email
    email = to_email or recipient_email
    if not email:
        raise ValueError("send_sheet_link_email: to_email or recipient_email is required.")

    # 2) Resolve sheet URL
    url = sheet_url
    if not url:
        # Try to find Google Sheets URL inside the message
        match = re.search(r"https://docs\\.google\\.com/spreadsheets/[^\\s)]+", message)
        if match:
            url = match.group(0)

    if not url:
        raise ValueError(
            "send_sheet_link_email: sheet_url is missing and could not be parsed from message."
        )

    # 3) Delegate to shared helper (we know this works from debug_gsuite_direct.py)
    status = send_email_with_sheet_link(
        to_email=email,
        subject=subject,
        sheet_url=url,
        message=message,
    )
    return SendEmailOutput(status=status)


if __name__ == "__main__":
    # Don't print to stdout – MCP uses stdout for JSON-RPC
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()
    else:
        mcp.run(transport="stdio")
