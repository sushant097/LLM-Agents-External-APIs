# mcp_server_gsuite.py
import sys
from typing import List

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from gsuite_clients import create_or_replace_sheet, send_email_with_sheet_link

# === Pydantic models ===

class CreateSheetInput(BaseModel):
    """
    Generic sheet creation for F1 standings:
    - title: Spreadsheet title in Google Drive
    - header: list of column names
    - rows: list of row values (strings only)
    """
    title: str
    header: List[str]
    rows: List[List[str]]


class CreateSheetOutput(BaseModel):
    spreadsheet_id: str
    spreadsheet_url: str


class SendEmailInput(BaseModel):
    """
    Send an email that contains a Google Sheet link.
    """
    to_email: str
    subject: str
    sheet_url: str
    message: str


class SendEmailOutput(BaseModel):
    status: str


# === MCP server ===

mcp = FastMCP("gsuite-tools")


@mcp.tool()
def create_sheet(input: CreateSheetInput) -> CreateSheetOutput:
    """
    Create a Google Sheet and populate it with header + rows.

    Typical F1 usage:
    - Use this after you have parsed current F1 driver standings
      into rows like:
      [["Max Verstappen", "Red Bull", "255"],
       ["Lando Norris", "McLaren", "210"],
       ...]
    """
    result = create_or_replace_sheet(
        title=input.title, header=input.header, rows=input.rows
    )
    return CreateSheetOutput(
        spreadsheet_id=result["spreadsheetId"],
        spreadsheet_url=result["spreadsheetUrl"],
    )


@mcp.tool()
def send_sheet_link_email(input: SendEmailInput) -> SendEmailOutput:
    """
    Send yourself an email containing the given Google Sheet link.

    The agent should:
    - call create_sheet() first
    - then call this tool with the returned spreadsheet_url.
    """
    status = send_email_with_sheet_link(
        to_email=input.to_email,
        subject=input.subject,
        sheet_url=input.sheet_url,
        message=input.message,
    )
    return SendEmailOutput(status=status)


# === Entry point: stdio vs SSE ===

if __name__ == "__main__":
    # Default: stdio (used by your Python agent)
    if len(sys.argv) == 1:
        print("mcp_server_gsuite.py starting in stdio mode")
        mcp.run(transport="stdio")

    # Optional: SSE mode (used by HTTP MCP host)
    else:
        mode = sys.argv[1]
        if mode == "sse":
            # Lazy import so the stdio path doesn’t require these deps
            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.routing import Route
            from starlette.requests import Request
            from starlette.responses import JSONResponse
            import uvicorn

            transport = SseServerTransport("/messages/")

            async def handle_post_message(request: Request):
                payload = await request.json()
                async with transport.connect_sse(payload) as stream:
                    async for _ in stream:
                        # We don't need to aggregate the stream here – the host does that.
                        pass
                return JSONResponse({"status": "ok"})

            app = Starlette(
                routes=[
                    Route("/messages/", transport.asgi_app),
                    Route("/messages", handle_post_message, methods=["POST"]),
                ]
            )

            async def lifespan(app):
                await mcp.run(transport=transport)
                yield

            app.router.lifespan_context = lifespan

            print("mcp_server_gsuite.py starting in SSE mode on http://127.0.0.1:8001")
            uvicorn.run(app, host="127.0.0.1", port=8001)
        else:
            raise SystemExit(f"Unknown mode: {mode}. Use no argument (stdio) or 'sse'.")
