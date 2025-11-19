import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
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
    print("mcp_server_telegram.py starting (stdio)")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # dev mode
    else:
        mcp.run(transport="stdio")
        print("\nShutting down...")
