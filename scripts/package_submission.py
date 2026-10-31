"""Build a small, explicit hand-in archive without secrets or unrelated local files."""

import argparse
import hashlib
import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

SOURCE_FOLDERS = ("literature_rag", "tests", "scripts", "docs", "evaluation")
SOURCE_FILES = ("README.md", "zadanie.md", "pyproject.toml",
                ".gitignore", ".env.example", "ODDANIE.md")
SOURCE_SUFFIXES = {".py", ".js", ".cjs", ".md", ".json", ".jsonl", ".toml"}
RUN_FILES = {"prompt.txt", "context.json", "sources.json", "retrieval.json", "metadata.json"}
PREFIX = "literature-rag"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Niepoprawna ścieżka pakietu: {relative}.")
    if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
        raise ValueError(f"Niedozwolony artefakt: {relative}.")
    if any(part == ".env" or (part.startswith(".env.") and part != ".env.example")
           for part in path.parts):
        raise ValueError("Sekrety nie mogą trafić do pakietu.")
    for parent in [root / path, *(root / path).parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Pakiet nie przyjmuje dowiązań: {relative}.")
    result = root / path
    if not result.is_file():
        raise ValueError(f"Brak pliku pakietu: {relative}.")
    return result


def package(root: Path, release_file: str, output: Path) -> dict:
    root = root.resolve()
    release = json.loads(safe_file(root, release_file).read_text(encoding="utf-8"))
    selected = {name for name in SOURCE_FILES if (root / name).is_file()}
    for folder in SOURCE_FOLDERS:
        for path in (root / folder).rglob("*"):
            if (path.is_file() and path.suffix in SOURCE_SUFFIXES
                    and "__pycache__" not in path.parts):
                selected.add(path.relative_to(root).as_posix())
    selected.add(release_file)
    selected.update(release["artifacts"])
    for run_dir in release["example_runs"].values():
        for filename in RUN_FILES:
            selected.add((Path(run_dir) / filename).as_posix())
    output = output.resolve()
    contents = {}
    for name in sorted(selected):
        path = safe_file(root, name)
        if path.resolve() == output:
            raise ValueError("Archiwum nie może nadpisać pliku wejściowego.")
        contents[name] = path.read_bytes()
    inventory = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "release_report": release_file,
        "files": {name: {"sha256": sha256(data), "bytes": len(data)}
                  for name, data in contents.items()},
    }
    contents["BUNDLE.json"] = (json.dumps(inventory, ensure_ascii=False, indent=2) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Preserve earlier hand-ins; a new revision needs a new output name.
    with output.open("xb") as destination:
        with tarfile.open(fileobj=destination, mode="w:gz") as archive:
            for name, data in contents.items():
                info = tarfile.TarInfo(f"{PREFIX}/{name}")
                info.size = len(data)
                info.mode = 0o644
                archive.addfile(info, io.BytesIO(data))
    return {"archive": str(output), "sha256": sha256(output.read_bytes()),
            "files": len(contents), "bytes": output.stat().st_size}


def extract_verified(archive_path: Path, destination: Path) -> tuple[Path, dict]:
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(not member.isfile() for member in members):
            raise ValueError("Archiwum zawiera powtórzenia lub pliki innego typu.")
        for name in names:
            path = Path(name)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != PREFIX:
                raise ValueError("Niedozwolona ścieżka w archiwum.")
        bundle_file = archive.extractfile(f"{PREFIX}/BUNDLE.json")
        if bundle_file is None:
            raise ValueError("Brak inwentarza pakietu.")
        with bundle_file:
            inventory = json.load(bundle_file)
        expected = {f"{PREFIX}/{name}" for name in inventory["files"]}
        if set(names) != expected | {f"{PREFIX}/BUNDLE.json"}:
            raise ValueError("Lista plików różni się od inwentarza.")
        for name, record in inventory["files"].items():
            with archive.extractfile(f"{PREFIX}/{name}") as stream:
                data = stream.read()
            if sha256(data) != record["sha256"] or len(data) != record["bytes"]:
                raise ValueError(f"Niezgodna suma kontrolna: {name}.")
        archive.extractall(destination, filter="data")
    return destination / PREFIX, inventory


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Przygotuj pakiet do oddania z jawną listą danych.",
    )
    parser.add_argument("--release", default="reports/submission.json")
    parser.add_argument("--output", type=Path,
                        default=Path("dist/literature-rag-submission.tar.gz"))
    args = parser.parse_args()
    try:
        result = package(Path(__file__).resolve().parent.parent, args.release, args.output)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"Błąd: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
