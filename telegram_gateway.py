# telegram_gateway.py
"""
Telegram → Agent gateway.

Flow:
  - User sends a message in Telegram, e.g.:
      "Find the Current Point Standings of F1 Racers"

  - This script receives the message, sets AGENT_INITIAL_PROMPT
    to that text (plus any extra instructions), and runs `python agent.py`.

  - The agent will:
      * fetch F1 standings via websearch MCP
      * create a Google Sheet via gsuite MCP
      * email the sheet link via Gmail

  - We optionally reply in Telegram that the job has been started.
"""

import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_EMAIL = os.getenv("YOUR_F1_EMAIL", "")  # optional, or hardcode your Gmail

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN env var is not set.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey! Send me:\n"
        "\"Find the Current Point Standings of F1 Racers\" \n"
        "and I will create a Google Sheet and email you the link."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return

    user_text = update.message.text.strip()

    # Optional: you can check text content and modify instructions
    # Here we just attach explicit instructions for the agent
    email_to = YOUR_EMAIL or "<YOUR_GMAIL_HERE>@gmail.com"

    agent_prompt = (
        f"{user_text}\n\n"
        f"Then create a Google Sheet named 'F1 Standings from Telegram', "
        f"fill it with the positions, drivers, teams, and points, and send "
        f"me the sheet link at {email_to} using your Gmail tools."
    )

    await update.message.reply_text(
        "Got it! Running the agent now. "
        "I'll email you the Google Sheet link when it's done."
    )

    # Prepare environment with AGENT_INITIAL_PROMPT
    env = os.environ.copy()
    env["AGENT_INITIAL_PROMPT"] = agent_prompt

    # Run the agent as a subprocess
    try:
        result = subprocess.run(
            ["uv", "run", "agent.py"],
            env=env,
            check=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        await update.message.reply_text(
            "Agent finished running. If everything went well, you should now have a "
            "new Google Sheet in Drive and an email with the link. 🚀"
        )
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(
            f"Oops, the agent failed with error code {e.returncode}. "
            "Check your logs for details."
        )


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram gateway running...")
    app.run_polling()


if __name__ == "__main__":
    main()
