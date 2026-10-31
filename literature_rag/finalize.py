"""Prepare an identified corpus, freeze annotations, and save a reproducible comparison."""

import argparse
import json
import re
from pathlib import Path

from .chunking import ChunkConfig
from .cli import build
from .context import create_packet
from .evaluation import evaluate, freeze_benchmark, load_benchmark
from .files import file_hash, read_json, utc_now, write_json
from .retrieval import search
from .store import metadata, open_index, source_record


def check_absence(connection, questions: list[dict]) -> dict:
    all_ids = [row[0] for row in connection.execute("SELECT source_id FROM sources")]
    records = [source_record(connection, source_id) for source_id in all_ids]
    patterns = {
        "q11": r"\b(?:joules?|watts?|kwh)\b|joules?\s*/\s*token|j\s*/\s*token",
        "q12": r"131[ ,]?072|\b128\s*k\b|batch(?:\s+size)?\s*(?:=|of)?\s*64\b",
    }
    output = {}
    for question in questions:
        if question["answerable"]:
            continue
        pattern = patterns.get(question["question_id"])
        if pattern is None:
            raise ValueError("Nowe pytanie bez danych wymaga osobnej kontroli zakresu.")
        targets = set(question["target_paper_ids"])
        matched, target_sources = [], []
        for source in records:
            if source["paper_id"] in targets:
                target_sources.append(source["source_id"])
            for field, text in source["sections"].items():
                matches = [match.group() for match in re.finditer(pattern, text, re.IGNORECASE)]
                if matches:
                    matched.append({"source_id": source["source_id"], "field": field,
                                    "target_paper": source["paper_id"] in targets,
                                    "matched_text": matches})
        output[question["question_id"]] = {
            "pattern": pattern, "all_sources_scanned": len(records),
            "target_source_ids": sorted(target_sources), "matches": matched,
            "target_matches": [item for item in matched if item["target_paper"]],
            "interpretation": "Kontrola słów/jednostek wspiera lekturę źródeł; "
                              "sama nie dowodzi braku odpowiedzi. Zakres nie obejmuje PDF-ów.",
        }
    return output


def comparison_markdown(results: dict, questions: list[dict], review_status: str) -> str:
    lines = ["# Porównanie retrieval", "", f"Status oznaczeń: `{review_status}`.", "",
             "Jednostka: różne notatki źródłowe. Obie metody używają identycznego indeksu,",
             "pytań, tokenizacji i filtrów. Dwóch pytań bez danych nie ma w mianowniku.", "",
             "| Metoda | Trafienia / pytania z odpowiedzią | Hit@5 |",
             "| --- | --- | --- |"]
    for method, result in results.items():
        metric = result["hit_at_5"]
        lines.append(f"| {method} | {metric['numerator']}/{metric['denominator']} | "
                     f"{metric['value']:.0%} |")
    lines += ["", "| Pytanie | BM25 | Wspólne słowa |", "| --- | --- | --- |"]
    for left, right in zip(results["bm25"]["questions"], results["overlap"]["questions"]):
        def label(row):
            if row["hit_at_5"] is None:
                return "poza metryką"
            return "tak" if row["hit_at_5"] else "nie"
        lines.append(f"| {left['question_id']} | {label(left)} | {label(right)} |")
    lines += ["", "## Przypadki nietrafienia", ""]
    failures = 0
    for method, result in results.items():
        for row in result["questions"]:
            if row["hit_at_5"] is not False:
                continue
            failures += 1
            ids = [hit["source_id"] for hit in row["retrieval"]["hits"]]
            lines += [f"- {method}, {row['question_id']}: top-5 `{', '.join(ids)}`;",
                      f"  oznaczone źródła: `{', '.join(row['relevant_source_ids'])}`."]
    if not failures:
        lines += ["Nie wystąpiło nietrafienie według Hit@5. Ograniczenia ujawniła kontrola",
                  "kompletności poniżej: jedno trafne źródło nie wystarcza do porównania prac."]
    lines += ["", "## Kompletność porównań dwóch prac", "",
              "Hit@5 wystarcza jedno trafne źródło, więc osobno sprawdzono pokrycie prac.", ""]
    for question in questions:
        if len(question.get("target_paper_ids", [])) < 2:
            continue
        targets = set(question["target_paper_ids"])
        for method, result in results.items():
            row = next(q for q in result["questions"]
                       if q["question_id"] == question["question_id"])
            present = {hit["paper_id"] for hit in row["retrieval"]["hits"]}
            relevant_papers = {hit["paper_id"] for hit in row["retrieval"]["hits"]
                               if hit["source_id"] in row["relevant_source_ids"]}
            lines.append(f"- {question['question_id']}, {method}: dowolne źródło właściwej pracy "
                         f"{len(targets & present)}/{len(targets)}, oznaczone trafne źródło "
                         f"{len(targets & relevant_papers)}/{len(targets)} prac.")
            if targets - present:
                lines.append(f"  Brakujące prace: `{', '.join(sorted(targets - present))}`. "
                             "Ranking skupia wyniki na jednej pracy. Prawdopodobna przyczyna: "
                             "dopasowanie słów OR bez zapewnienia pokrycia obu nazwanych prac.")
    lines += ["", "## Pytania bez danych", ""]
    for question in questions:
        if question["answerable"]:
            continue
        lines += [f"- {question['question_id']}: {question['absence_reason']}"]
        for method, result in results.items():
            row = next(q for q in result["questions"]
                       if q["question_id"] == question["question_id"])
            lines.append(f"  {method}: {len(row['retrieval']['hits'])} wyników leksykalnych; "
                         "obecność wyników nie dowodzi wystarczających danych.")
    lines += ["", "## Interpretacja i ograniczenia", "",
              "Dziesięć pytań i niepełne oznaczenia nie uzasadniają wniosków o istotności",
              "statystycznej ani o ogólnej przewadze metody. Wynik zależy od słów w pytaniu.",
              "Nazwy metod i słownictwo ze źródeł w pytaniach ułatwiają dopasowanie leksykalne.",
              "Nie dostrajano retrieval po obejrzeniu tego porównania. Powtarzane chunki",
              "jednej recenzji nie są osobnymi trafieniami. Opinie innych recenzentów tej",
              "samej pracy nie zastępują oznaczonych source ID.", "",
              "Jakość odpowiedzi: **nie oceniano — brak generacji**.", ""]
    if review_status != "human_reviewed":
        lines += ["**Wyniki wstępne:** oznaczenia wymagają dodatkowej weryfikacji.",
                  "Nie są końcowym, niezależnie zweryfikowanym benchmarkiem.", ""]
    return "\n".join(lines)


def finalize(snapshot: Path, *, replace_index: bool = False) -> dict:
    database = Path("data/index/real.sqlite")
    manifest_path = Path("data/manifests/corpus.json")
    questions_path = Path("evaluation/questions.jsonl")
    judgments_path = Path("evaluation/judgments.jsonl")
    frozen_path = Path("evaluation/frozen.json")
    build(snapshot, database, ChunkConfig(), replace=replace_index, manifest_path=manifest_path)
    with open_index(database) as connection:
        info = metadata(connection)
        if info["dataset_type"] != "openreview":
            raise ValueError("Raport wymaga rzeczywistych danych OpenReview.")
        questions, _ = load_benchmark(connection, questions_path, judgments_path)
        if not frozen_path.exists():
            freeze_benchmark(connection, questions_path, judgments_path, frozen_path)
        frozen = read_json(frozen_path)
        results, result_paths = {}, {}
        for method in ("bm25", "overlap"):
            result = evaluate(connection, frozen_path, method)
            path = Path("reports") / f"{method}.json"
            write_json(path, result)
            results[method], result_paths[method] = result, str(path)
        write_json(Path("reports/absence-checks.json"), check_absence(connection, questions))
        examples = {}
        for question in questions:
            packet = create_packet(connection, search(
                connection, question["question"], conference=question["conference"],
                kind=question.get("kind"), method="bm25", top_k=5,
            ), Path("runs/examples"))
            examples[question["question_id"]] = str(packet)
        failure_query = "interstellar neutrino detector calibration constant2026"
        failure_retrieval = search(connection, failure_query)
        failure_packet = create_packet(connection, failure_retrieval, Path("runs/examples"))
        examples["out_of_topic"] = str(failure_packet)
        write_json(Path("reports/observed-failure.json"), {
            "query": failure_query, "packet": str(failure_packet),
            "source_ids": [hit["source_id"] for hit in failure_retrieval["hits"]],
            "not_part_of_final_benchmark": True,
            "cause": "Dopasowanie OR po słowie calibration zwraca recenzje kwantyzacji "
                     "bez danych o detektorze neutrin.",
        })
        requested = read_json(Path("data/curation/topic-selection.json"))
        actual = {venue: [] for venue in requested["venues"]}
        for row in connection.execute("SELECT paper_id, conference FROM papers ORDER BY paper_id"):
            actual[row["conference"]].append(row["paper_id"])
        missing = {venue: sorted(set(ids) - set(actual[venue]))
                   for venue, ids in requested["venues"].items()}
    write_json(Path("data/curation/submission-selection.json"), {
        "selected_paper_ids": actual, "not_collected_from_candidate_list": missing,
        "counts": info["counts"], "papers_per_conference": info["papers_per_conference"],
        "reviews_per_conference": info["reviews_per_conference"],
        "snapshot_sha256": file_hash(snapshot),
        "selection_basis": "Dostępne publiczne wątki z listy tematycznej; dobór niezależny "
                           "od ocen recenzji i wyników benchmarku.",
        "limitation": "Próba jest mniejsza od zakładanych 30+30 z powodu ograniczeń dostępu API.",
    })
    comparison = Path("reports/comparison.md")
    comparison.write_text(comparison_markdown(results, questions, frozen["annotation_review"]),
                          encoding="utf-8")
    evaluation_info = read_json(Path("evaluation/metadata.json"))
    evaluation_info.update(
        questions_sha256=file_hash(questions_path), judgments_sha256=file_hash(judgments_path),
        corpus_fingerprint=info["corpus_fingerprint"], index_fingerprint=info["index_fingerprint"],
    )
    write_json(Path("evaluation/metadata.json"), evaluation_info)
    artifacts = [str(snapshot), str(database), str(manifest_path),
                 "data/curation/submission-selection.json", "data/curation/topic-selection.json",
                 "data/curation/topic-audit.jsonl", "reports/raport.md", "reports/topic-audit.md",
                 "reports/corpus-audit.json", "reports/rating-scales.json", str(comparison),
                 "reports/absence-checks.json", "reports/observed-failure.json",
                 "reports/access-check.json", *result_paths.values(),
                 "data/raw/openreview-v3-830dc090e225.json"]
    release = {
        "schema_version": 1, "created_at": utc_now(), "status": "final",
        "database": str(database), "manifest": str(manifest_path), "snapshot": str(snapshot),
        "frozen": str(frozen_path), "counts": info["counts"],
        "papers_per_conference": info["papers_per_conference"],
        "reviews_per_conference": info["reviews_per_conference"],
        "index_fingerprint": info["index_fingerprint"], "snapshot_sha256": file_hash(snapshot),
        "evaluation_results": result_paths,
        "hit_at_5": {method: result["hit_at_5"] for method, result in results.items()},
        "comparison": str(comparison), "example_runs": examples,
        "generation_status": "not_run", "artifacts": artifacts,
        "limitations": ["Mała próba dobrana według dostępności publicznych danych.",
                        "Niepełne oznaczenia trafności; brak pomiaru jakości generacji."],
    }
    write_json(Path("reports/submission.json"), release)
    return {"status": release["status"], "counts": info["counts"],
            "hit_at_5": release["hit_at_5"], "report": "reports/submission.json"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Odtwórz indeks, porównanie i przykłady promptów.")
    parser.add_argument("--snapshot", type=Path, default=Path("data/raw/corpus.json"))
    parser.add_argument("--replace-index", action="store_true")
    args = parser.parse_args()
    try:
        result = finalize(args.snapshot, replace_index=args.replace_index)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"Błąd: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
