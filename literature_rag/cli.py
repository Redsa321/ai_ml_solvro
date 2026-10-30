"""Polish CLI; all commands except an explicit Gemini generation work offline."""

import argparse
import json
import os
import sqlite3
import sys
import uuid
from contextlib import closing
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .chunking import ChunkConfig
from .context import create_packet
from .domain import SOURCE_KINDS
from .evaluation import evaluate, freeze_benchmark
from .files import file_hash, read_json, write_json
from .generation import generate_packet, settings
from .retrieval import search
from .snapshot import load_snapshot
from .store import build_index, metadata, open_index

DEFAULT_DB = Path("data/index/corpus.sqlite")
FIXTURE = Path(__file__).resolve().parent.parent / "tests/fixtures/synthetic_snapshot.json"


def emit(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build(
    snapshot_path: Path, database: Path, config: ChunkConfig, *, replace: bool = False,
    manifest_path: Path | None = None,
) -> dict:
    corpus, raw_hash = load_snapshot(snapshot_path)
    info = build_index(corpus, database, config, replace=replace)
    if manifest_path is None:
        name = raw_hash[:12] + "-" + info["index_fingerprint"][:12] + ".json"
        manifest_path = Path("data/manifests") / name
    manifest = {
        "schema_version": 1, "dataset_type": corpus.dataset_type,
        "snapshot_file": os.path.relpath(snapshot_path.resolve(), manifest_path.parent.resolve()),
        "snapshot_sha256": raw_hash, "corpus_fingerprint": corpus.fingerprint,
        "index_fingerprint": info["index_fingerprint"], "chunk_config": asdict(config),
        "paper_ids": [paper.paper_id for paper in corpus.papers],
        "review_ids": [source.source_id for source in corpus.sources
                       if source.kind == "official_review"],
        "provenance": corpus.provenance, "import_report": corpus.import_report,
    }
    if manifest_path.exists():
        if read_json(manifest_path) != manifest:
            raise ValueError(
                "Manifest już istnieje z inną treścią; wybierz nowy --manifest-output."
            )
    else:
        write_json(manifest_path, manifest, exclusive=True)
    return {"database": str(database), "manifest": str(manifest_path), **info}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Asystent literatury: lokalne źródła i audytowalny RAG."
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Sprawdź lokalne środowisko, bez żądań sieciowych.")
    doctor.add_argument("--db", type=Path, default=DEFAULT_DB)

    builder = commands.add_parser(
        "build", help="Odtwórz indeks z lokalnego snapshotu lub manifestu."
    )
    inputs = builder.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--snapshot", type=Path)
    inputs.add_argument("--manifest", type=Path)
    builder.add_argument("--db", type=Path, default=DEFAULT_DB)
    builder.add_argument("--manifest-output", type=Path)
    builder.add_argument("--chunk-words", type=int, default=180)
    builder.add_argument("--chunk-overlap", type=int, default=30)
    builder.add_argument("--replace", action="store_true", help="Jawnie zastąp indeks inną wersją.")

    for command, help_text in (
        ("search", "Wyszukaj różne źródła metodą BM25 lub wspólnych słów."),
        ("ask", "Zapisz prompt i kontekst; opcjonalnie wywołaj Gemini."),
    ):
        search_parser = commands.add_parser(command, help=help_text)
        search_parser.add_argument("query", help="Pytanie lub temat po angielsku.")
        search_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
        search_parser.add_argument("--method", choices=("bm25", "overlap"), default="bm25")
        search_parser.add_argument(
            "--conference", help="iclr2024, neurips2024 albo pełny venue ID."
        )
        search_parser.add_argument("--kind", choices=SOURCE_KINDS)
        search_parser.add_argument("--top-k", type=int, default=5)
        if command == "search":
            search_parser.add_argument("--json", action="store_true")
        else:
            search_parser.add_argument("--provider", choices=("none", "gemini"))
            search_parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
            search_parser.add_argument("--max-chars", type=int, default=12000)

    freezer = commands.add_parser("freeze", help="Sprawdź i zamroź ręczne oznaczenia benchmarku.")
    freezer.add_argument("--db", type=Path, default=DEFAULT_DB)
    freezer.add_argument("--questions", type=Path, required=True)
    freezer.add_argument("--judgments", type=Path, required=True)
    freezer.add_argument("--output", type=Path, default=Path("evaluation/frozen.json"))
    freezer.add_argument("--allow-synthetic", action="store_true")
    freezer.add_argument("--development", action="store_true")

    evaluator = commands.add_parser("evaluate", help="Policz Hit@5 na zamrożonym benchmarku.")
    evaluator.add_argument("--db", type=Path, default=DEFAULT_DB)
    evaluator.add_argument("--frozen", type=Path, required=True)
    evaluator.add_argument("--method", choices=("bm25", "overlap"), required=True)
    evaluator.add_argument("--allow-synthetic", action="store_true")
    evaluator.add_argument("--output", type=Path)

    demo = commands.add_parser("demo", help="Uruchom demonstrację na jawnie fikcyjnych danych.")
    demo.add_argument("--db", type=Path, default=DEFAULT_DB)
    demo.add_argument("--runs-dir", type=Path, default=Path("runs"))
    demo.add_argument("--manifest-output", type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return dispatch(args)
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"Błąd: {exc}", file=sys.stderr)
        return 2


def dispatch(args) -> int:
    if args.command == "doctor":
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.execute("CREATE VIRTUAL TABLE probe USING fts5(text)")
        config = settings()
        result = {
            "python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version,
            "fts5_available": True, "runtime_dependencies": [], "network_used": False,
            "database_exists": args.db.is_file(),
            "gemini_key_present": bool(config["GEMINI_API_KEY"]),
            "gemini_model_configured": bool(config["GEMINI_MODEL"]),
        }
        if args.db.is_file():
            with open_index(args.db) as connection:
                result["index"] = metadata(connection)
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                result["integrity_check"] = integrity
                result["foreign_key_errors"] = len(
                    connection.execute("PRAGMA foreign_key_check").fetchall()
                )
        emit(result)
        return 0
    if args.command == "build":
        config = ChunkConfig(args.chunk_words, args.chunk_overlap)
        snapshot_path = args.snapshot
        manifest = None
        if args.manifest:
            manifest = read_json(args.manifest)
            if (
                manifest.get("schema_version") != 1
                or not isinstance(manifest.get("snapshot_file"), str)
                or not isinstance(manifest.get("chunk_config"), dict)
                or set(manifest["chunk_config"]) != {"words", "overlap"}
                or not all(isinstance(manifest.get(key), str) for key in (
                    "snapshot_sha256", "corpus_fingerprint", "index_fingerprint",
                ))
            ):
                raise ValueError("Nieobsługiwana wersja manifestu.")
            snapshot_path = args.manifest.parent / manifest["snapshot_file"]
            if file_hash(snapshot_path) != manifest["snapshot_sha256"]:
                raise ValueError("Snapshot nie zgadza się z hashem manifestu.")
            config = ChunkConfig(**manifest["chunk_config"])
            corpus, _ = load_snapshot(snapshot_path)
            if corpus.fingerprint != manifest["corpus_fingerprint"]:
                raise ValueError("Korpus nie zgadza się z manifestem.")
        result = build(
            snapshot_path, args.db, config, replace=args.replace,
            manifest_path=args.manifest_output or args.manifest,
        )
        emit(result)
        return 0
    if args.command == "demo":
        result = build(FIXTURE, args.db, ChunkConfig(), manifest_path=args.manifest_output)
        with open_index(args.db) as connection:
            retrieval = search(
                connection, "quantization quality limitations", kind="official_review",
            )
            packet = create_packet(connection, retrieval, args.runs_dir)
        emit({
            "warning": "DANE SYNTETYCZNE: fikcyjne publikacje; demonstracja kodu, nie wynik badań.",
            "database": str(args.db), "manifest": result["manifest"],
            "counts": result["counts"], "prompt_packet": str(packet),
            "generation_status": "not_run", "network_used": False,
        })
        return 0
    if args.command in ("search", "ask"):
        with open_index(args.db) as connection:
            retrieval = search(
                connection, args.query, method=args.method, conference=args.conference,
                kind=args.kind, top_k=args.top_k,
            )
            if args.command == "ask":
                directory = create_packet(
                    connection, retrieval, args.runs_dir, max_chars=args.max_chars,
                )
        if args.command == "search":
            if args.json:
                emit(retrieval)
            else:
                if retrieval["dataset_type"] == "synthetic":
                    print("DANE SYNTETYCZNE — fikcyjne fixtures, nie publikacje naukowe.")
                for hit in retrieval["hits"]:
                    print(f"{hit['rank']}. {hit['title']} ({hit['conference']})")
                    print(f"   {hit['kind']} | {hit['source_id']} | score={hit['score']:.6g}")
                    print(f"   {hit['field']}: {hit['text']}")
                    print(f"   {hit['url']}")
                if not retrieval["hits"]:
                    print(
                        "Brak pasujących źródeł. "
                        "Nie jest to dowód braku odpowiedzi w całym korpusie."
                    )
            return 0
        config = settings()
        provider = args.provider
        if provider is None:
            provider = config["GENERATION_PROVIDER"] or "none"
        if provider not in ("none", "gemini"):
            raise ValueError("GENERATION_PROVIDER musi mieć wartość none albo gemini.")
        if provider == "gemini":
            result = generate_packet(directory, config)
        else:
            result = read_json(directory / "metadata.json")
        emit({
            "packet": str(directory), "dataset_type": retrieval["dataset_type"],
            "generation_status": result["generation_status"],
            "message": "Prompt i kontekst zapisane; status generacji podano powyżej.",
        })
        return 2 if result["generation_status"] == "invalid_citations" else 0
    if args.command == "freeze":
        with open_index(args.db) as connection:
            result = freeze_benchmark(
                connection, args.questions, args.judgments, args.output,
                allow_synthetic=args.allow_synthetic, development=args.development,
            )
        emit({"frozen": str(args.output), **result})
        return 0
    if args.command == "evaluate":
        with open_index(args.db) as connection:
            result = evaluate(
                connection, args.frozen, args.method, allow_synthetic=args.allow_synthetic,
            )
        output = args.output or Path("runs") / ("eval-" + uuid.uuid4().hex) / "results.json"
        write_json(output, result, exclusive=True)
        emit({"output": str(output), "evaluation_type": result["evaluation_type"],
              "hit_at_5": result["hit_at_5"], "generation_quality": result["generation_quality"]})
        return 0
    raise ValueError("Nieobsługiwana komenda.")
