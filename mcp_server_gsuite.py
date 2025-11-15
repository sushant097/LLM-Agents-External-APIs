import sys
from typing import List

from mcp.server.fastmcp import FastMCP

from gsuite_clients import create_or_replace_sheet, send_email_with_sheet_link
from models import (
    CreateSheetInput,
    CreateSheetOutput,
    SendEmailInput,
    SendEmailOutput,
)

# === MCP server ===

mcp = FastMCP("gsuite-tools")


@mcp.tool()
def create_sheet(input: CreateSheetInput) -> CreateSheetOutput:
    """
    Create a Google Sheet and populate it with header + rows.

    Typical F1 usage:
    - title: "F1 Standings 2025"
    - header: ["Position", "Driver", "Team", "Points"]
    - rows:  [["1", "Max Verstappen", "Red Bull", "255"], ...]
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
    Send an email with the Google Sheet link.

    The agent should:
    1) call create_sheet()
    2) then call send_sheet_link_email() with the returned spreadsheet_url.
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
    # Default: stdio (used by Python agent)
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
