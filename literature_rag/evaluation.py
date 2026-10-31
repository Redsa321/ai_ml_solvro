"""Freeze manual judgments before comparing retrieval methods."""

import os
import sqlite3
from pathlib import Path

from .domain import SOURCE_KINDS, conference_id
from .files import file_hash, read_json, read_jsonl, utc_now, write_json
from .retrieval import search
from .store import metadata, source_record


def hit_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int = 5) -> bool:
    if k < 1:
        raise ValueError("k musi być dodatnie.")
    unique = list(dict.fromkeys(ranked_ids))[:k]
    return bool(set(unique) & relevant_ids)


def load_benchmark(connection: sqlite3.Connection, questions_path: Path, judgments_path: Path):
    questions = read_jsonl(questions_path)
    if not questions:
        raise ValueError("Zestaw pytań jest pusty.")
    by_id = {}
    for question in questions:
        question_id = question.get("question_id")
        if not isinstance(question_id, str) or not question_id or question_id in by_id:
            raise ValueError("Każde pytanie musi mieć unikalny question_id.")
        if not isinstance(question.get("question"), str) or not question["question"].strip():
            raise ValueError(f"Brak tekstu pytania: {question_id}.")
        if type(question.get("answerable")) is not bool:
            raise ValueError(f"answerable musi być bool: {question_id}.")
        question["conference"] = conference_id(question.get("conference"))
        if question.get("kind") is not None and question["kind"] not in SOURCE_KINDS:
            raise ValueError(f"Nieznany rodzaj źródła w pytaniu: {question_id}.")
        if not question["answerable"]:
            for key in ("absence_reason", "absence_check"):
                if not isinstance(question.get(key), str) or not question[key].strip():
                    raise ValueError(f"Pytanie bez danych wymaga {key}: {question_id}.")
        by_id[question_id] = question
    judgments = {question_id: set() for question_id in by_id}
    for judgment in read_jsonl(judgments_path):
        question_id, source_id = judgment.get("question_id"), judgment.get("source_id")
        if question_id not in by_id or not by_id[question_id]["answerable"]:
            raise ValueError("Oznaczenie nie wskazuje pytania z odpowiedzią.")
        if not isinstance(source_id, str):
            raise ValueError("Oznaczenie wymaga source_id.")
        if source_id in judgments[question_id]:
            raise ValueError(f"Powtórzone oznaczenie: {question_id}, {source_id}.")
        source = source_record(connection, source_id)
        if source is None:
            raise ValueError(f"Oznaczone źródło nie istnieje: {source_id}.")
        question = by_id[question_id]
        if question["conference"] and source["conference"] != question["conference"]:
            raise ValueError(f"Oznaczone źródło nie spełnia filtra konferencji: {source_id}.")
        if question.get("kind") and source["kind"] != question["kind"]:
            raise ValueError(f"Oznaczone źródło ma niewłaściwy typ: {source_id}.")
        evidence, reason = judgment.get("evidence"), judgment.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"Brak ręcznego uzasadnienia: {source_id}.")
        if not isinstance(evidence, str) or not evidence.strip() or not any(
            evidence in text for text in source["sections"].values()
        ):
            raise ValueError(f"Fragment oznaczenia nie występuje w źródle: {source_id}.")
        judgments[question_id].add(source_id)
    for question in questions:
        if question["answerable"] and not judgments[question["question_id"]]:
            raise ValueError(f"Brak trafnych źródeł dla: {question['question_id']}.")
    return questions, judgments


def freeze_benchmark(
    connection: sqlite3.Connection, questions_path: Path, judgments_path: Path, output: Path,
    *, allow_synthetic: bool = False, development: bool = False,
) -> dict:
    info = metadata(connection)
    synthetic = info["dataset_type"] == "synthetic"
    if synthetic and not allow_synthetic:
        raise ValueError("Fixtures nie mierzą jakości. Do testu narzędzi użyj --allow-synthetic.")
    questions, _ = load_benchmark(connection, questions_path, judgments_path)
    annotations = [*questions, *read_jsonl(judgments_path)]
    explicitly_unreviewed = any(row.get("human_reviewed") is False for row in annotations)
    human_reviewed = all(row.get("human_reviewed") is True for row in annotations)
    if not synthetic and not development and explicitly_unreviewed:
        raise ValueError(
            "Oznaczenia są propozycją bez przeglądu człowieka. "
            "Do wyników wstępnych użyj --development; nie oznaczaj ich jako końcowe."
        )
    answerable = sum(question["answerable"] for question in questions)
    unanswerable = len(questions) - answerable
    if not synthetic and not development and (answerable < 10 or unanswerable < 2):
        raise ValueError("Benchmark końcowy wymaga minimum 10 pytań z odpowiedzią i 2 bez danych.")
    frozen = {
        "schema_version": 1, "created_at": utc_now(), "dataset_type": info["dataset_type"],
        "evaluation_type": "synthetic_test_only" if synthetic else (
            "development" if development else "final"
        ),
        "annotation_review": ("human_reviewed" if human_reviewed else
                              "unreviewed" if explicitly_unreviewed else "not_recorded"),
        "corpus_fingerprint": info["corpus_fingerprint"],
        "index_fingerprint": info["index_fingerprint"],
        "unit": "unique_source_note", "k": 5,
        "question_counts": {"answerable": answerable, "unanswerable": unanswerable},
        "files": {
            "questions": {"path": os.path.relpath(
                questions_path.resolve(), output.parent.resolve()),
                          "sha256": file_hash(questions_path)},
            "judgments": {"path": os.path.relpath(
                judgments_path.resolve(), output.parent.resolve()),
                          "sha256": file_hash(judgments_path)},
        },
    }
    write_json(output, frozen, exclusive=True)
    return frozen


def evaluate(
    connection: sqlite3.Connection, frozen_path: Path, method: str,
    *, allow_synthetic: bool = False,
) -> dict:
    frozen = read_json(frozen_path)
    info = metadata(connection)
    if frozen.get("schema_version") != 1 or frozen.get("k") != 5:
        raise ValueError("Nieobsługiwany protokół zamrożonego benchmarku.")
    if frozen.get("index_fingerprint") != info["index_fingerprint"]:
        raise ValueError("Korpus lub konfiguracja indeksu zmieniły się po zamrożeniu benchmarku.")
    if info["dataset_type"] == "synthetic" and not allow_synthetic:
        raise ValueError("To fixtures. --allow-synthetic dopuszcza wyłącznie test narzędzi.")
    paths = {}
    for key in ("questions", "judgments"):
        reference = frozen.get("files", {}).get(key, {})
        if not isinstance(reference.get("path"), str):
            raise ValueError("Niekompletny plik zamrożenia.")
        path = frozen_path.parent / reference["path"]
        if file_hash(path) != reference.get("sha256"):
            raise ValueError(f"Zmieniono {key} po zamrożeniu. Utwórz nową wersję benchmarku.")
        paths[key] = path
    questions, judgments = load_benchmark(connection, paths["questions"], paths["judgments"])
    rows, numerator, denominator = [], 0, 0
    for question in questions:
        retrieval = search(
            connection, question["question"], method=method,
            conference=question["conference"], kind=question.get("kind"), top_k=5,
        )
        relevant = judgments[question["question_id"]]
        ranked_ids = [hit["source_id"] for hit in retrieval["hits"]]
        hit = hit_at_k(ranked_ids, relevant) if question["answerable"] else None
        if question["answerable"]:
            denominator += 1
            numerator += int(hit)
        rows.append({
            "question_id": question["question_id"], "answerable": question["answerable"],
            "relevant_source_ids": sorted(relevant), "hit_at_5": hit,
            "matched_source_ids": sorted(set(ranked_ids) & relevant), "retrieval": retrieval,
            "absence_reason": question.get("absence_reason"),
        })
    return {
        "created_at": utc_now(), "dataset_type": info["dataset_type"],
        "evaluation_type": frozen["evaluation_type"], "method": method,
        "annotation_review": frozen.get("annotation_review", "not_recorded"),
        "benchmark_sha256": file_hash(frozen_path),
        "corpus_fingerprint": info["corpus_fingerprint"],
        "index_fingerprint": info["index_fingerprint"], "unit": "unique_source_note",
        "hit_at_5": {"numerator": numerator, "denominator": denominator,
                     "value": numerator / denominator if denominator else None},
        "unanswerable_questions": len(questions) - denominator,
        "generation_quality": "nie oceniano — brak generacji",
        "questions": rows,
        "limitations": ["Oznaczenia mogą nie obejmować wszystkich trafnych źródeł."] + (
            ["Oznaczenia nie zostały zweryfikowane; wynik wstępny."]
            if frozen.get("annotation_review") == "unreviewed" else []
        ) + (
            ["Dane syntetyczne: wynik testuje kod, nie jakość na publikacjach."]
            if info["dataset_type"] == "synthetic" else []
        ),
    }
