# mcp_server_gsuite_sse.py
"""
GSuite MCP Server (SSE transport)

Exposes three tools to the agent via MCP:
  - create_gsheet(title: str) -> {sheet_id, url}
  - append_gsheet_rows(sheet_id: str, values: list[list[str]]) -> {ok: bool}
  - send_gmail(to: str, subject: str, body_html: str) -> {ok: bool}

Transport: SSE (Server-Sent Events), mounted at:
  - GET  /sse          → SSE stream
  - POST /messages/... → client → server messages

"""

import uvicorn
from typing import List, Dict

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request

from google_sheets import create_sheet, append_rows
from gmail_smtp import send_email

# ---------- Define MCP tools ----------

mcp = FastMCP("GSuiteSSEServer")


@mcp.tool()
def create_gsheet(title: str) -> Dict[str, str]:
    """
    Create a Google Sheet and return its id + url.

    Example return:
      {"sheet_id": "...", "url": "https://docs.google.com/spreadsheets/..."}
    """
    return create_sheet(title)


@mcp.tool()
def append_gsheet_rows(sheet_id: str, values: List[List[str]]) -> Dict[str, bool]:
    """
    Append one or more rows to an existing Google Sheet.

    values must be a list of rows: each row is a list of strings.
    """
    ok = append_rows(sheet_id, values)
    return {"ok": bool(ok)}


@mcp.tool()
def send_gmail(to: str, subject: str, body_html: str) -> Dict[str, bool]:
    """
    Send an email via Gmail with HTML body.

    For this assignment, the body_html will typically contain the Google Sheet link.
    """
    ok = send_email(to, subject, body_html)
    return {"ok": bool(ok)}


# ---------- SSE transport + Starlette app ----------


def create_sse_app(debug: bool = False) -> Starlette:
    """
    Create a Starlette application that serves the MCP server via SSE.

    Pattern follows the official MCP SSE example:

      - GET  /sse       → SSE event stream (server → client)
      - POST /messages/ → HTTP POST channel (client → server)
    """
    # SseServerTransport takes the POST base path where clients will send messages.
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        """
        Handle the SSE GET endpoint and run the MCP server over it.
        """
        # connect_sse wires Starlette's ASGI interfaces into the transport
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # Starlette's private send, used by transport
        ) as (read_stream, write_stream):
            # Run the underlying MCP server (FastMCP wraps this for us)
            await mcp._mcp_server.run(
                read_stream,
                write_stream,
                mcp._mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            # SSE stream endpoint
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            # HTTP POST endpoint for messages from client to server
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    app = create_sse_app(debug=True)
    uvicorn.run(app, host="0.0.0.0", port=8088)
