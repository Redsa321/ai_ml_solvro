"""Embed a versioned topic selection into the browser exporter, without dependencies."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Przygotuj eksporter dla sprawdzonej listy prac.")
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("runs/export-topic-reviewed.js"))
    args = parser.parse_args()
    source = Path(__file__).with_name("export-openreview.js")
    try:
        selection = json.loads(args.selection.read_text(encoding="utf-8"))
        if not isinstance(selection, dict) or selection.get("schema_version") != 1:
            raise ValueError("Nieobsługiwany format listy tematycznej.")
        if not isinstance(selection.get("venues"), dict):
            raise ValueError("Brak list identyfikatorów konferencji.")
        if args.output.resolve() in (source.resolve(), args.selection.resolve()):
            raise ValueError("Plik wyjściowy nie może nadpisać kodu ani listy prac.")
        prefix = "globalThis.__openreviewTopicSelection = " + json.dumps(
            selection, ensure_ascii=False, sort_keys=True, indent=2,
        ) + ";\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            prefix + source.read_text(encoding="utf-8"), encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Błąd: {exc}\n")
    print(args.output)


if __name__ == "__main__":
    main()
