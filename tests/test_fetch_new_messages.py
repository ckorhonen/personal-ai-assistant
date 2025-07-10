import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.tools.email import fetch_new_messages


def make_service(history_responses, message_map):
    service = Mock()
    users = service.users.return_value

    history = users.history.return_value
    list_call = history.list.return_value
    list_call.execute.side_effect = history_responses

    messages = users.messages.return_value

    def get_side_effect(userId, id, format):
        resp = message_map[id]
        call = Mock()
        call.execute.return_value = resp
        return call

    messages.get.side_effect = get_side_effect
    return service


def test_fetch_new_messages_pagination_and_sorting():
    history_responses = [
        {
            'history': [{'messages': [{'id': '1'}, {'id': '2'}]}],
            'nextPageToken': 't1',
        },
        {
            'history': [{'messages': [{'id': '2'}, {'id': '3'}]}]
        },
    ]

    message_map = {
        '1': {'id': '1', 'internalDate': '100'},
        '2': {'id': '2', 'internalDate': '50'},
        '3': {'id': '3', 'internalDate': '150'},
    }

    service = make_service(history_responses, message_map)

    messages = fetch_new_messages(service, '10')
    ids = [m['id'] for m in messages]

    assert ids == ['2', '1', '3']

