from __future__ import annotations

import os
import tempfile
import threading
import webbrowser
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path

from .model import Entry
from .render import render_document


@contextmanager
def temporary_document(entries: list[Entry]) -> Iterator[Path]:
    """Create a private temporary HTML document and remove it afterward."""
    with tempfile.TemporaryDirectory(prefix="bitwarden-html-export-") as directory:
        directory_path = Path(directory)
        html_path = directory_path / "export.html"
        css_path = directory_path / "style.css"

        html_path.write_text(render_document(entries), encoding="utf-8")
        css_path.write_text(
            files("bitwarden_html_export").joinpath("style.css").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        os.chmod(html_path, 0o600)
        os.chmod(css_path, 0o600)
        yield html_path


def view_temporary_export(
    entries: list[Entry],
    *,
    delete_after: float = 10,
    open_browser: Callable[[str], bool] = webbrowser.open,
    wait_for_enter: Callable[[str], str] = input,
) -> None:
    """Open a private temporary export and delete it on Enter or after a timeout."""
    with temporary_document(entries) as html_path:
        lock = threading.Lock()
        deleted = False

        def delete_files() -> None:
            nonlocal deleted
            with lock:
                if deleted:
                    return
                for path in html_path.parent.iterdir():
                    path.unlink(missing_ok=True)
                deleted = True
                print("Temporary HTML export deleted.")

        timer = threading.Timer(delete_after, delete_files)
        timer.daemon = True
        timer.start()
        try:
            if not open_browser(html_path.as_uri()):
                print("The browser could not be opened automatically.")
            try:
                wait_for_enter("Press Enter to delete the temporary HTML export.\n")
            except EOFError:
                pass
        finally:
            delete_files()
            timer.cancel()
            timer.join()
