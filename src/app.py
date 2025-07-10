import asyncio
from googleapiclient.discovery import build

from .db import SqliteKV
from .channels.telegram import TelegramChannel
from .email_utils import classify_importance
from .tools.email import fetch_new_messages
from .utils import get_credentials

# Globals initialised in ``main``
gmail_service = None
db = SqliteKV()


async def poll_gmail():
    """Continuously poll Gmail for new messages."""
    try:
        while True:
            last = db.get("last_history_id")
            msgs = fetch_new_messages(gmail_service, last)
            for m in msgs:
                kind = classify_importance(m)
                if kind == "vip":
                    TelegramChannel.push_email(m, kind)
            if msgs:
                db.set("last_history_id", msgs[-1]["historyId"])
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass


def main() -> None:
    """Entry point for the polling service."""
    global gmail_service
    creds = get_credentials()
    gmail_service = build("gmail", "v1", credentials=creds)

    loop = asyncio.get_event_loop()
    task = loop.create_task(poll_gmail())
    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        task.cancel()
        loop.run_until_complete(task)
    finally:
        loop.close()
        db.close()


if __name__ == "__main__":
    main()
