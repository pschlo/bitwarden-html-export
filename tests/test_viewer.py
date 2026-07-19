import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from bitwarden_html_export.viewer import view_temporary_export


def test_temporary_export_exists_only_while_viewing() -> None:
    opened_path: Path | None = None

    def open_browser(uri: str) -> bool:
        nonlocal opened_path
        opened_path = Path(url2pathname(urlparse(uri).path))
        assert opened_path.exists()
        if os.name != "nt":
            assert opened_path.stat().st_mode & 0o077 == 0
        assert "Synthetic login" in opened_path.read_text(encoding="utf-8")
        assert opened_path.with_name("style.css").exists()
        return True

    view_temporary_export(
        [{"name": "Synthetic login"}],
        delete_after=60,
        open_browser=open_browser,
        wait_for_enter=lambda _: "",
    )

    assert opened_path is not None
    assert not opened_path.exists()
    assert not opened_path.parent.exists()
