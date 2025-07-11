import os
import asyncio
import base64
import sqlite3
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError

from .. import config
from ..utils import get_credentials
from ..tools import email as email_utils


class TelegramChannel:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("CHAT_ID")
        self.bot = Bot(token=self.token)

    def send_message(self, text):
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
            )
            return "Message sent successfully on Telegram"
        except TelegramError as e:
            return f"Failed to send message: {str(e)}"

    def receive_messages(self, after_timestamp):
        try:
            loop = asyncio.get_event_loop()
            updates = loop.run_until_complete(self.bot.get_updates())
            new_messages = []
            for update in updates:
                if isinstance(update, Update) and update.message:
                    message = update.message
                    if message.date.timestamp() > after_timestamp:
                        new_messages.append({
                            "text": message.text,
                            "date": message.date.strftime("%Y-%m-%d %H:%M"),
                        })
            return new_messages
        except TelegramError as e:
            return f"Failed to retrieve messages: {str(e)}"

    @staticmethod
    def push_email(msg, kind):
        """Push a Gmail message to the configured Telegram user.

        Parameters
        ----------
        msg : dict
            Message object returned by the Gmail API.
        kind : str
            Classification of the email (unused).
        """

        headers = {
            h.get("name"): h.get("value")
            for h in msg.get("payload", {}).get("headers", [])
            if isinstance(h, dict)
        }
        subject = headers.get("Subject", "(no subject)")
        from_addr = headers.get("From", "(unknown)")

        body = msg.get("snippet", "")[:200]
        md = f"*{subject}* \u00b7 _{from_addr}_ \u00b7 {body}"

        buttons = [
            [InlineKeyboardButton("Draft Reply", callback_data=f"draft:{msg.get('id')}")]
        ]

        parts = msg.get("payload", {}).get("parts", [])
        if any(p.get("mimeType") == "text/calendar" for p in parts):
            buttons.append([
                InlineKeyboardButton("Yes", callback_data=f"rsvp:{msg.get('id')}:yes"),
                InlineKeyboardButton("No", callback_data=f"rsvp:{msg.get('id')}:no"),
                InlineKeyboardButton("Maybe", callback_data=f"rsvp:{msg.get('id')}:maybe"),
            ])

        ikb = InlineKeyboardMarkup(buttons)
        bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
        bot.send_message(chat_id=config.USER_ID, text=md, reply_markup=ikb)



def handle_draft(update: Update, context) -> None:
    """Handle a "draft" callback query from Telegram."""

    update.callback_query.answer()
    msg_id = update.callback_query.data.split(":", 1)[1]

    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=msg_id, format="full")
        .execute()
    )
    draft_text = email_utils.generate_reply(msg)

    orig_text = update.callback_query.message.text or ""
    new_text = f"{orig_text}\n--- Draft ---\n{draft_text}"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Send ✅", callback_data=f"send:{msg_id}"),
                InlineKeyboardButton(
                    "Discard ❌", callback_data=f"discard:{msg_id}"
                ),
            ]
        ]
    )

    update.callback_query.message.edit_text(new_text, reply_markup=keyboard)


def handle_send(update: Update, context) -> None:
    """Handle a "send" callback query from Telegram."""

    update.callback_query.answer()
    msg_id = update.callback_query.data.split(":", 1)[1]

    conn = sqlite3.connect("assistant.db")
    cur = conn.execute(
        "SELECT text FROM drafts WHERE gmail_id=?", (msg_id,)
    )
    row = cur.fetchone()
    cur.close()
    draft_text = row[0] if row else ""

    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=msg_id, format="full")
        .execute()
    )

    headers = {
        h.get("name"): h.get("value")
        for h in msg.get("payload", {}).get("headers", [])
        if isinstance(h, dict)
    }
    to_addr = headers.get("From", "")
    subject = "Re: " + headers.get("Subject", "")
    thread_id = msg.get("threadId")

    mime = MIMEText(draft_text)
    mime["To"] = to_addr
    mime["Subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()

    service.users().messages().send(
        userId="me", body={"raw": raw, "threadId": thread_id}
    ).execute()

    conn.execute("DELETE FROM drafts WHERE gmail_id=?", (msg_id,))
    conn.commit()
    conn.close()

    update.callback_query.message.edit_text("Sent ✅")


def handle_discard(update: Update, context) -> None:
    """Handle a "discard" callback query from Telegram."""

    update.callback_query.answer()
    msg_id = update.callback_query.data.split(":", 1)[1]

    conn = sqlite3.connect("assistant.db")
    conn.execute("DELETE FROM drafts WHERE gmail_id=?", (msg_id,))
    conn.commit()
    conn.close()

    update.callback_query.message.edit_text("Draft discarded.")


def handle_rsvp(update: Update, context) -> None:
    """Handle an RSVP callback query from Telegram."""

    update.callback_query.answer()
    parts = update.callback_query.data.split(":", 2)
    if len(parts) == 3:
        _, msg_id, response = parts
    else:
        msg_id, response = "", ""

    status = {
        "yes": "accepted",
        "no": "declined",
        "maybe": "tentative",
    }.get(response, "tentative")

    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    service.events().patch(
        calendarId="primary",
        eventId=msg_id,
        body={"responseStatus": status},
    ).execute()

    update.callback_query.message.edit_text(
        f"Responded: {response.capitalize()}"
    )


def handle_callback(update: Update, context) -> None:
    """Dispatch callback queries to their respective handlers."""

    if not update.callback_query:
        return

    data = update.callback_query.data or ""

    if data.startswith("draft:"):
        handle_draft(update, context)
    elif data.startswith("send:"):
        handle_send(update, context)
    elif data.startswith("discard:"):
        handle_discard(update, context)
    elif data.startswith("rsvp:"):
        handle_rsvp(update, context)
