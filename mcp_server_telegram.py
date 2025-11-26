import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import requests

from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Need to check at runtime to allow for dynamic env var setting
if not TELEGRAM_BOT_TOKEN:
    # IMPORTANT: log to stderr, not stdout
    print("[telegram] WARNING: TELEGRAM_BOT_TOKEN is not set. Tools will fail.", file=sys.stderr)

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else ""


class SendTelegramMessageInput(BaseModel):
    """
    Send a plain-text message to a Telegram chat.

    - chat_id: numeric ID or @channelusername
    - text: message content
    """
    chat_id: str
    text: str
    parse_mode: Optional[str] = None  # e.g. "MarkdownV2" or "HTML"


class SendTelegramMessageOutput(BaseModel):
    status: str
    message_id: Optional[int] = None


mcp = FastMCP("telegram-tools")


@mcp.tool()
def send_telegram_message(input: SendTelegramMessageInput) -> SendTelegramMessageOutput:
    """
    Send a message to Telegram.

    Typical usage in this assignment:
    - After the agent has finished the workflow and sent the Gmail,
      it can send a confirmation message back to your Telegram chat
      saying that the sheet + email are ready.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_API_BASE:
        return SendTelegramMessageOutput(
            status="ERROR: TELEGRAM_BOT_TOKEN not configured.",
            message_id=None,
        )

    payload = {
        "chat_id": input.chat_id,
        "text": input.text,
    }
    if input.parse_mode:
        payload["parse_mode"] = input.parse_mode

    try:
        resp = requests.post(f"{TELEGRAM_API_BASE}/sendMessage", json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        msg_id = data.get("result", {}).get("message_id")
        return SendTelegramMessageOutput(status="sent", message_id=msg_id)
    except Exception as e:
        return SendTelegramMessageOutput(status=f"ERROR: {e}", message_id=None)


if __name__ == "__main__":
    """
    Run modes:
      - python mcp_server_telegram.py            -> stdio MCP server
      - python mcp_server_telegram.py dev        -> dev stdio
      - python mcp_server_telegram.py sse        -> SSE MCP server (HTTP)
    """
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"

    if mode == "sse":
        # SSE mode: run HTTP MCP server with Server-Sent Events
        host = os.getenv("TELEGRAM_MCP_HOST", "127.0.0.1")
        port = int(os.getenv("TELEGRAM_MCP_PORT", "8765"))
        # DO NOT print to stdout here; stdout is used for HTTP responses
        print(f"[telegram] Starting SSE MCP server on {host}:{port}", file=sys.stderr)
        mcp.run(transport="sse", host=host, port=port)
    elif mode == "dev":
        # dev stdio mode (for debugging with MCP inspector etc.)
        mcp.run()
    else:
        # default: stdio MCP for your current agent setup
        mcp.run(transport="stdio")
