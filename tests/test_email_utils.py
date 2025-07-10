import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.email_utils import classify_importance


VIP_MSG = {
    "labelIds": [],
    "payload": {
        "headers": [
            {"name": "From", "value": "boss@example.com"},
        ]
    },
}

STARRED_MSG = {
    "labelIds": ["\\Starred"],
    "payload": {"headers": []},
}

PROMO_MSG = {
    "labelIds": ["CATEGORY_PROMOTIONS"],
    "payload": {"headers": []},
}

NEWSLETTER_MSG = {
    "labelIds": [],
    "payload": {
        "headers": [
            {"name": "From", "value": "news@example.com"},
            {"name": "List-Id", "value": "<news.list.example.com>"},
        ]
    },
}

OTHER_MSG = {
    "labelIds": [],
    "payload": {"headers": []},
}


def test_classify_vip_sender():
    assert classify_importance(VIP_MSG) == "vip"


def test_classify_vip_starred():
    assert classify_importance(STARRED_MSG) == "vip"


def test_classify_promo():
    assert classify_importance(PROMO_MSG) == "promo"


def test_classify_newsletter():
    assert classify_importance(NEWSLETTER_MSG) == "newsletter"


def test_classify_other():
    assert classify_importance(OTHER_MSG) == "other"
