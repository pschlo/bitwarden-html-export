from bitwarden_html_export.cli import build_parser


def test_parser_defaults() -> None:
    args = build_parser().parse_args(["export.json"])

    assert args.export.name == "export.json"
    assert args.delete_after == 10
