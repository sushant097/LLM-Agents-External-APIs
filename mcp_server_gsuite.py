"""
MCP server exposing Google Sheets + Gmail tools using USER OAuth.

Tools:
  - create_sheet(title, header, rows) -> CreateSheetOutput
  - send_sheet_link_email(to_email, subject, sheet_url, message) -> SendEmailOutput

These internally call gsuite_clients.create_or_replace_sheet and
gsuite_clients.send_email_with_sheet_link.
"""

import sys
from typing import List

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from gsuite_clients import create_or_replace_sheet, send_email_with_sheet_link


# ======== Pydantic models for outputs only ========

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
    to_email: str,
    subject: str,
    sheet_url: str,
    message: str,
) -> SendEmailOutput:
    """
    Send an email with the Google Sheet link.
    """
    status = send_email_with_sheet_link(
        to_email=to_email,
        subject=subject,
        sheet_url=sheet_url,
        message=message,
    )
    return SendEmailOutput(status=status)


if __name__ == "__main__":
    # Don't print to stdout – MCP uses stdout for JSON-RPC
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()
    else:
        mcp.run(transport="stdio")
