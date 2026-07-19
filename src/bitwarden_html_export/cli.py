from __future__ import annotations

import argparse
import math
from collections.abc import Sequence
from pathlib import Path

from .model import VaultFormatError, load_entries
from .viewer import view_temporary_export


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open a plaintext Bitwarden JSON export as temporary local HTML.",
    )
    parser.add_argument("export", type=Path, help="path to a plaintext Bitwarden JSON export")
    parser.add_argument(
        "--delete-after",
        type=float,
        default=10,
        metavar="SECONDS",
        help="automatically delete the temporary HTML after this many seconds (default: 10)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not math.isfinite(args.delete_after) or args.delete_after <= 0:
        parser.error("--delete-after must be greater than zero")

    try:
        entries = load_entries(args.export)
    except OSError as error:
        parser.error(f"could not read the export: {error}")
    except VaultFormatError as error:
        parser.error(str(error))

    view_temporary_export(entries, delete_after=args.delete_after)
