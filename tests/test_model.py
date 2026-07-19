import json
from pathlib import Path

import pytest

from bitwarden_html_export import VaultFormatError, load_entries, normalize_entry, parse_entries


def test_normalizes_login_without_mutating_source() -> None:
    item = {
        "id": "synthetic-id",
        "type": 1,
        "name": "Example login",
        "notes": None,
        "login": {
            "username": "alice",
            "password": "synthetic-password",
            "uris": [{"uri": "https://example.com"}, {"uri": None}],
        },
        "fields": [
            {"name": "PIN", "value": "1234", "type": 1},
            {"name": "Empty", "value": None, "type": 0},
        ],
    }
    original = json.loads(json.dumps(item))

    entry = normalize_entry(item)

    assert item == original
    assert entry == {
        "name": "Example login",
        "username": "alice",
        "password": "synthetic-password",
        "uris": "https://example.com",
        "PIN": "1234",
        "Empty": "",
    }


def test_supports_ssh_key_items() -> None:
    entry = normalize_entry(
        {
            "type": 5,
            "name": "Synthetic key",
            "sshKey": {
                "privateKey": "not-a-real-private-key",
                "publicKey": "not-a-real-public-key",
                "keyFingerprint": "SHA256:synthetic",
            },
        }
    )

    assert entry["privateKey"] == "not-a-real-private-key"
    assert entry["keyFingerprint"] == "SHA256:synthetic"


@pytest.mark.parametrize(
    "data",
    [
        {"encrypted": True, "items": []},
        {},
        {"items": ["not an object"]},
        {"items": [{"type": 999}]},
    ],
)
def test_rejects_unsupported_exports(data: dict[str, object]) -> None:
    with pytest.raises(VaultFormatError):
        parse_entries(data)


def test_load_entries_reports_invalid_json(tmp_path: Path) -> None:
    export = tmp_path / "export.json"
    export.write_text("not json", encoding="utf-8")

    with pytest.raises(VaultFormatError, match="Invalid JSON"):
        load_entries(export)
