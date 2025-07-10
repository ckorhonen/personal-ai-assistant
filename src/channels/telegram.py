import os
import asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError

import config


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
