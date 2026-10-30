"""Inventory numeric score scales without changing original review values."""

import argparse
import math
import re
from collections import defaultdict
from pathlib import Path

from .files import file_hash, read_json, utc_now, write_json


def numeric_scale_values(field: dict) -> list[int | float] | None:
    param = field.get("value", {}).get("param") or field.get("param", {})
    options = param.get("enum", [])
    if not isinstance(options, list) or not options:
        return None
    numbers = []
    for option in options:
        raw = option.get("value") if isinstance(option, dict) else option
        if isinstance(raw, bool):
            return None
        if isinstance(raw, (int, float)):
            number = float(raw)
        elif isinstance(raw, str):
            match = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)(?=\s|[:.)-]|$)", raw)
            if not match:
                return None
            number = float(match.group(1))
        else:
            return None
        if not math.isfinite(number):
            return None
        numbers.append(int(number) if number.is_integer() else number)
    return sorted(set(numbers))


def rating_scale_inventory(snapshot: dict) -> tuple[dict, list[dict]]:
    schemas = {schema["id"]: schema for schema in snapshot.get("raw_invitations", [])}
    inventory, unresolved = {}, []
    for venue in snapshot["venues"]:
        variants = defaultdict(set)
        for invitation_id in venue["review_invitations"]:
            if invitation_id not in schemas:
                raise ValueError(f"Brak oryginalnego schematu: {invitation_id}.")
            fields = schemas[invitation_id].get("edit", {}).get("note", {}).get("content", {})
            for name in venue["rating_fields"]:
                if name not in fields:
                    continue
                values = numeric_scale_values(fields[name])
                if values is None:
                    unresolved.append({"invitation_id": invitation_id, "field": name})
                else:
                    variants[name].add(tuple(values))
        inventory[venue["id"]] = {
            name: [list(values) for values in sorted(scales)]
            for name, scales in sorted(variants.items())
        }
    return inventory, unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Zapisz oryginalne skale ocen z raw invitations.")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        inventory, unresolved = rating_scale_inventory(read_json(args.snapshot))
        write_json(args.output, {
            "checked_at": utc_now(), "snapshot": str(args.snapshot),
            "snapshot_sha256": file_hash(args.snapshot),
            "original_rating_scales": inventory, "unresolved": unresolved,
            "note": "Inwentarz skal. Oryginalne pola i wartości recenzji pozostają niezmienione.",
        })
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Błąd: {exc}\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
