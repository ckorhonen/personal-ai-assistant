"""Utilities for email-related features."""

from __future__ import annotations

import sqlite3
from typing import Dict, Any

from openai import OpenAI


def generate_reply(msg: Dict[str, Any]) -> str:
    """Generate a reply draft for a Gmail message and save it.

    Parameters
    ----------
    msg : dict
        Gmail message object which must include ``id`` and ``snippet`` keys.

    Returns
    -------
    str
        The generated reply text.
    """

    body = msg.get("snippet", "")
    prompt = (
        "Write a concise, friendly reply to the below email:\n---\n"
        f"{body}\n---"
    )

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    draft_text = response.choices[0].message.content.strip()

    conn = sqlite3.connect("assistant.db")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS drafts(gmail_id TEXT PRIMARY KEY, text TEXT)"
    )
    conn.execute(
        "REPLACE INTO drafts(gmail_id, text) VALUES (?, ?)",
        (msg.get("id"), draft_text),
    )
    conn.commit()
    conn.close()

    return draft_text
