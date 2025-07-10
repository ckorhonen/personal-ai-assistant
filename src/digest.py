"""Utilities for gathering and formatting email digests."""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Dict, List

from bs4 import BeautifulSoup

from .email_utils import classify_importance
from .utils import get_llm_by_provider
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

# Gmail service is injected from ``src.app`` when running the program
gmail_service = None


def _decode_html(msg: dict) -> str:
    """Return the HTML body from a Gmail message."""
    payload = msg.get("payload", {})
    parts = payload.get("parts", [])
    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data", "")
    else:
        data = ""
        for part in parts:
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                break
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    html = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", "ignore")
    return html


def _extract_links(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [a.get("href") for a in soup.find_all("a", href=True)][:3]


def llm_summarise(html_body: str, sentences: int) -> str:
    """Summarise HTML content using an LLM."""
    llm = get_llm_by_provider("openai/gpt-4o-mini", temperature=0.1)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=f"Summarise the newsletter in {sentences} sentences."),
            HumanMessage(content=html_body),
        ]
    )
    chain = prompt | llm
    return chain.invoke({}).content.strip()


def collect_digest(start_ts: int, end_ts: int) -> Dict[str, List[dict]]:
    """Collect non-VIP Gmail messages in the given time range."""
    query = f"after:{start_ts} before:{end_ts}"
    page_token = None
    msg_refs: List[dict] = []

    while True:
        kwargs = {"userId": "me", "q": query}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = gmail_service.users().messages().list(**kwargs).execute()
        msg_refs.extend(resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    buckets = {"promo": [], "newsletter": [], "other": []}
    for ref in msg_refs:
        msg = (
            gmail_service.users()
            .messages()
            .get(userId="me", id=ref["id"], format="full")
            .execute()
        )
        kind = classify_importance(msg)
        if kind == "vip":
            continue
        if kind not in buckets:
            kind = "other"
        buckets[kind].append(msg)
    return buckets


def format_digest(buckets: Dict[str, List[dict]]) -> str:
    """Format collected messages into a markdown digest."""
    sections = []

    promos = buckets.get("promo", [])
    if promos:
        lines = ["⚡ Time-Sensitive Deals"]
        for m in promos:
            headers = {
                h.get("name"): h.get("value")
                for h in m.get("payload", {}).get("headers", [])
                if isinstance(h, dict)
            }
            brand = headers.get("From", "").split("<")[0].strip()
            subject = headers.get("Subject", "(no subject)")
            exp = datetime.fromtimestamp(int(m.get("internalDate", "0")) / 1000).strftime("%Y-%m-%d")
            lines.append(f"- {brand} — {subject} — Expires {exp}")
        sections.append("\n".join(lines))

    newsletters = buckets.get("newsletter", [])
    if newsletters:
        lines = ["📰 Newsletters"]
        for m in newsletters:
            html = _decode_html(m)
            summary = llm_summarise(html, 3)
            links = _extract_links(html)
            bullet = f"- {summary}"
            for link in links:
                bullet += f"\n  - {link}"
            lines.append(bullet)
        sections.append("\n".join(lines))

    others = buckets.get("other", [])
    if others:
        lines = ["📬 Other Mail"]
        for m in others:
            headers = {
                h.get("name"): h.get("value")
                for h in m.get("payload", {}).get("headers", [])
                if isinstance(h, dict)
            }
            subject = headers.get("Subject", "(no subject)")
            lines.append(f"- {subject}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
