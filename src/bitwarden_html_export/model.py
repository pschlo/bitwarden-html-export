from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


Entry = dict[str, str]

ITEM_SECTIONS = {
    1: "login",
    2: "secureNote",
    3: "card",
    4: "identity",
    5: "sshKey",
}

IGNORED_FIELDS = {
    "collectionIds",
    "favorite",
    "folderId",
    "id",
    "organizationId",
    "passwordHistory",
    "reprompt",
    "revisionDate",
    "type",
}


class VaultFormatError(ValueError):
    """Raised when an input file is not a supported plaintext Bitwarden export."""


def _stringify(value: Any) -> str:
    if isinstance(value, (Mapping, list, tuple)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def normalize_entry(item: Mapping[str, Any]) -> Entry:
    """Flatten one Bitwarden item into displayable name/value fields."""
    item_type = item.get("type")
    if (
        isinstance(item_type, bool)
        or not isinstance(item_type, int)
        or item_type not in ITEM_SECTIONS
    ):
        raise VaultFormatError(f"Unsupported Bitwarden item type: {item_type!r}")

    values = dict(item)
    section_name = ITEM_SECTIONS[item_type]
    section = values.pop(section_name, None)
    if section is not None:
        if not isinstance(section, Mapping):
            raise VaultFormatError(f"The {section_name!r} section must be an object")
        values.update(section)

    custom_fields = values.pop("fields", []) or []
    if not isinstance(custom_fields, list):
        raise VaultFormatError("The 'fields' value must be a list")

    entry: Entry = {}
    for name, value in values.items():
        if name in IGNORED_FIELDS or _is_empty(value):
            continue
        if name == "uris":
            if not isinstance(value, list):
                raise VaultFormatError("The 'uris' value must be a list")
            uris = [uri.get("uri") for uri in value if isinstance(uri, Mapping)]
            value = "\n".join(uri for uri in uris if isinstance(uri, str) and uri)
            if not value:
                continue
        entry[str(name)] = _stringify(value)

    for field in custom_fields:
        if not isinstance(field, Mapping):
            raise VaultFormatError("Each custom field must be an object")
        name = field.get("name")
        value = field.get("value")
        if name is None and value is None:
            continue
        entry["" if name is None else str(name)] = "" if value is None else _stringify(value)

    return entry


def parse_entries(data: Mapping[str, Any]) -> list[Entry]:
    """Parse all items from a plaintext Bitwarden JSON export."""
    if data.get("encrypted") is True:
        raise VaultFormatError("Encrypted Bitwarden exports are not supported")
    items = data.get("items")
    if not isinstance(items, list):
        raise VaultFormatError("The export must contain an 'items' list")

    entries: list[Entry] = []
    for item in items:
        if not isinstance(item, Mapping):
            raise VaultFormatError("Each vault item must be an object")
        entries.append(normalize_entry(item))
    return entries


def load_entries(path: Path) -> list[Entry]:
    """Load and parse a plaintext Bitwarden JSON export."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise VaultFormatError(f"Invalid JSON: {error.msg}") from error
    if not isinstance(data, Mapping):
        raise VaultFormatError("The export root must be an object")
    return parse_entries(data)
