import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.digest as digest


def make_service(message_ids, message_map):
    service = Mock()
    users = service.users.return_value

    messages = users.messages.return_value
    list_call = messages.list.return_value
    list_call.execute.return_value = {
        'messages': [{'id': m} for m in message_ids]
    }

    def get_side_effect(userId, id, format):
        call = Mock()
        call.execute.return_value = message_map[id]
        return call

    messages.get.side_effect = get_side_effect
    return service


def test_collect_digest_groups(monkeypatch):
    msgs = {
        '1': {'id': '1'},
        '2': {'id': '2'},
        '3': {'id': '3'},
    }

    service = make_service(['1', '2', '3'], msgs)
    monkeypatch.setattr(digest, 'gmail_service', service)

    def classify(msg):
        return {'1': 'promo', '2': 'vip', '3': 'other'}[msg['id']]

    monkeypatch.setattr(digest, 'classify_importance', classify)

    buckets = digest.collect_digest(0, 100)

    assert buckets['promo'] == [msgs['1']]
    assert buckets['newsletter'] == []
    assert buckets['other'] == [msgs['3']]
