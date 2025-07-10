from .find_contacts import find_contact_email
from .read_emails import read_emails
from .send_email import send_email

from typing import List, Dict

__all__ = ['find_contact_email', 'read_emails', 'send_email', 'fetch_new_messages']


def fetch_new_messages(service, history_id: str) -> List[Dict]:
    """Fetch Gmail messages newer than a specific history ID."""
    messages = []
    message_ids = set()
    page_token = None

    while True:
        kwargs = {'userId': 'me', 'startHistoryId': history_id}
        if page_token:
            kwargs['pageToken'] = page_token
        response = (
            service.users()
            .history()
            .list(**kwargs)
            .execute()
        )
        for record in response.get('history', []):
            for msg in record.get('messages', []):
                msg_id = msg.get('id')
                if msg_id:
                    message_ids.add(msg_id)
        page_token = response.get('nextPageToken')
        if not page_token:
            break

    for msg_id in message_ids:
        msg = (
            service.users()
            .messages()
            .get(userId='me', id=msg_id, format='full')
            .execute()
        )
        messages.append(msg)

    messages.sort(key=lambda m: int(m.get('internalDate', '0')))
    return messages
