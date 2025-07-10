import asyncio
import time
from apscheduler.schedulers.background import BackgroundScheduler
from googleapiclient.discovery import build

from .db import SqliteKV
from .channels.telegram import TelegramChannel
from .email_utils import classify_importance
from .tools.email import fetch_new_messages
from .utils import get_credentials
from . import digest

# Globals initialised in ``main``
gmail_service = None
db = SqliteKV()
scheduler = BackgroundScheduler()


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


async def handle_commands():
    """Handle Telegram commands like ``/catchup``."""
    last_ts = int(time.time())
    try:
        while True:
            msgs = TelegramChannel().receive_messages(last_ts)
            for msg in msgs:
                if msg.get("text") == "/catchup":
                    run_digest()
            last_ts = int(time.time())
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass


def run_digest() -> None:
    """Collect messages since the last digest and send a summary."""
    now = int(time.time())
    last = int(db.get("last_digest_ts", "0"))
    digest.gmail_service = gmail_service
    buckets = digest.collect_digest(last, now)
    message = digest.format_digest(buckets)
    TelegramChannel().send_message(message)
    db.set("last_digest_ts", str(now))


def main() -> None:
    """Entry point for the polling service."""
    global gmail_service
    creds = get_credentials()
    gmail_service = build("gmail", "v1", credentials=creds)

    loop = asyncio.get_event_loop()
    poll_task = loop.create_task(poll_gmail())
    cmd_task = loop.create_task(handle_commands())

    scheduler.add_job(
        run_digest,
        id="digest_morning",
        trigger="cron",
        hour=6,
        minute=0,
        timezone="America/New_York",
    )
    scheduler.add_job(
        run_digest,
        id="digest_evening",
        trigger="cron",
        hour=18,
        minute=0,
        timezone="America/New_York",
    )

    scheduler.start()

    try:
        loop.run_until_complete(asyncio.gather(poll_task, cmd_task))
    except KeyboardInterrupt:
        poll_task.cancel()
        cmd_task.cancel()
        loop.run_until_complete(
            asyncio.gather(poll_task, cmd_task, return_exceptions=True)
        )
    finally:
        scheduler.shutdown()
        loop.close()
        db.close()


if __name__ == "__main__":
    main()
