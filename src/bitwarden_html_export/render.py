from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from html import escape

from .model import Entry


def _render_field(name: str, value: str) -> str:
    return (
        '          <li class="field">\n'
        f'            <p class="fieldname">{escape(name)}</p>\n'
        f'            <p class="fieldvalue">{escape(value)}</p>\n'
        "          </li>"
    )


def _render_entry(entry: Mapping[str, str]) -> str:
    fields = "\n".join(_render_field(name, value) for name, value in entry.items())
    return f'      <li class="entry">\n        <ul>\n{fields}\n        </ul>\n      </li>'


def render_document(entries: Iterable[Entry], *, generated_at: datetime | None = None) -> str:
    """Render entries as a standalone local HTML document."""
    timestamp = (generated_at or datetime.now().astimezone()).strftime("%d %b %Y, %H:%M:%S UTC%z")
    rendered_entries = "\n".join(_render_entry(entry) for entry in entries)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Bitwarden Export</title>
    <link rel="stylesheet" href="style.css">
  </head>
  <body>
    <header>
      <h1>Bitwarden Export</h1>
      <p>{escape(timestamp)}</p>
    </header>
    <ul class="container">
{rendered_entries}
    </ul>
  </body>
</html>
"""
