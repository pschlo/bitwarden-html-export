from datetime import datetime, timezone
from importlib.resources import files

from bitwarden_html_export import render_document


def test_render_is_local_and_escapes_vault_values() -> None:
    document = render_document(
        [{"name": "<script>alert('no')</script>", "password": "a&b"}],
        generated_at=datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc),
    )

    assert "<script>alert" not in document
    assert "&lt;script&gt;alert" in document
    assert "a&amp;b" in document
    assert "default-src 'none'" in document
    assert '<link rel="stylesheet" href="style.css">' in document
    assert "19 Jul 2026, 12:00:00 UTC+0000" in document


def test_stylesheet_has_no_remote_dependencies() -> None:
    stylesheet = files("bitwarden_html_export").joinpath("style.css").read_text(encoding="utf-8")

    assert "http://" not in stylesheet
    assert "https://" not in stylesheet
    assert "@import" not in stylesheet
