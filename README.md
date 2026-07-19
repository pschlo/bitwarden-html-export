# Bitwarden HTML Export

Open a plaintext Bitwarden JSON export as a readable local HTML document.

## Run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), open a terminal in this directory, and run:

```console
uv run bitwarden-html-export path/to/bitwarden_export.json
```

The document opens in your browser and is deleted automatically after 10 seconds or when you press Enter. The original JSON file is not changed.

The JSON file and generated document contain plaintext passwords and other secrets. Keep them private and delete the plaintext JSON export when you no longer need it. A browser may retain page data in memory or its cache even after the temporary file is deleted. Use Bitwarden's encrypted export format for long-term backups.

## Development

Tests use synthetic vault data only.

```console
uv run pytest
uv build
```
