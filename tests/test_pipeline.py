"""Behavior checks on fictional fixtures; never evidence of research quality."""

import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from dataclasses import replace
from pathlib import Path

from literature_rag.chunking import ChunkConfig, chunk_source
from literature_rag.context import build_context, create_packet, unknown_citations
from literature_rag.evaluation import evaluate, freeze_benchmark, hit_at_k
from literature_rag.files import read_json
from literature_rag.generation import generate_packet
from literature_rag.retrieval import search
from literature_rag.snapshot import normalize_snapshot
from literature_rag.store import build_index, metadata, open_index, source_record

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests/fixtures"


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.raw = read_json(FIXTURES / "synthetic_snapshot.json")

    def test_only_official_reviews_and_abstracts_are_imported(self):
        corpus = normalize_snapshot(self.raw)
        self.assertEqual(len(corpus.papers), 3)
        self.assertEqual(len(corpus.sources), 7)
        self.assertEqual(corpus.import_report["ignored_other_replies"], 3)
        self.assertNotIn("fixture-comment", {source.source_id for source in corpus.sources})
        self.assertTrue(all(
            source.url.startswith("https://example.invalid/") for source in corpus.sources
        ))

    def test_invitation_suffix_alone_does_not_make_a_review(self):
        note = next(
            note for note in self.raw["notes"] if note["id"] == "fixture-review-quant-positive"
        )
        note["invitations"] = ["OtherVenue/Submission1/-/Official_Review"]
        corpus = normalize_snapshot(self.raw)
        self.assertNotIn(note["id"], {source.source_id for source in corpus.sources})

    def test_cross_paper_review_relation_is_rejected(self):
        note = next(note for note in self.raw["notes"] if note["id"] == "fixture-review-cache")
        note["forum"] = "fixture-iclr-quant"
        with self.assertRaisesRegex(ValueError, "relację"):
            normalize_snapshot(self.raw)

    def test_verified_invitation_cannot_point_at_another_paper(self):
        mapping = self.raw["venues"][0]["review_invitations"]
        invitation = next(iter(mapping))
        mapping[invitation] = "fixture-iclr-decode"
        with self.assertRaisesRegex(ValueError, "relację"):
            normalize_snapshot(self.raw)

    def test_unverified_schema_and_duplicate_ids_are_rejected(self):
        self.raw["venues"][0]["verified"] = False
        with self.assertRaisesRegex(ValueError, "verified"):
            normalize_snapshot(self.raw)
        self.raw["venues"][0]["verified"] = True
        self.raw["notes"].append(self.raw["notes"][0])
        with self.assertRaisesRegex(ValueError, "Powtórzony note ID"):
            normalize_snapshot(self.raw)

    def test_private_review_is_not_imported_as_public(self):
        self.raw["notes"][3]["readers"] = ["private-group"]
        with self.assertRaisesRegex(ValueError, "publiczna"):
            normalize_snapshot(self.raw)

    def test_public_readers_must_be_a_list_and_fetch_date_has_timezone(self):
        self.raw["notes"][0]["readers"] = "everyone"
        with self.assertRaisesRegex(ValueError, "readers musi być listą"):
            normalize_snapshot(self.raw)
        self.raw["notes"][0]["readers"] = ["everyone"]
        self.raw["provenance"]["fetched_at"] = "2026-10-30T12:00:00"
        with self.assertRaisesRegex(ValueError, "strefę czasową"):
            normalize_snapshot(self.raw)

    def test_original_rating_scales_unknown_fields_and_missing_values_survive(self):
        corpus = normalize_snapshot(self.raw)
        by_id = {source.source_id: source for source in corpus.sources}
        critical = by_id["fixture-review-quant-critical"]
        self.assertNotIn("confidence", critical.ratings)
        self.assertEqual(critical.ratings["rating"], {"value": "4: reject in this fictional scale"})
        cache = by_id["fixture-review-cache"]
        self.assertIn("overall", cache.ratings)
        self.assertNotIn("rating", cache.ratings)
        self.assertEqual(
            by_id["fixture-review-decode"].sections["unexpected_text_field"],
            "Energy consumption measurements are absent.",
        )


class IndexCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.db = self.base / "corpus.sqlite"
        self.corpus = normalize_snapshot(read_json(FIXTURES / "synthetic_snapshot.json"))
        self.config = ChunkConfig(words=8, overlap=2)
        self.info = build_index(self.corpus, self.db, self.config)


class StorageAndRetrievalTests(IndexCase):
    def test_repeated_import_is_idempotent_and_rebuild_is_reproducible(self):
        again = build_index(self.corpus, self.db, self.config)
        rebuilt = build_index(self.corpus, self.base / "rebuilt.sqlite", self.config)
        self.assertTrue(again["reused"])
        self.assertEqual(again["counts"], self.info["counts"])
        self.assertEqual(rebuilt["index_fingerprint"], self.info["index_fingerprint"])
        with open_index(self.db) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM sources").fetchone()[0], 7)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertIsInstance(
                source_record(connection, "fixture-review-cache")["ratings"], dict,
            )

    def test_existing_snapshot_is_preserved_without_explicit_replace(self):
        changed = replace(self.corpus, papers=[
            replace(paper, title="Changed title") if index == 0 else paper
            for index, paper in enumerate(self.corpus.papers)
        ])
        with self.assertRaisesRegex(ValueError, "inny snapshot"):
            build_index(changed, self.db, self.config)
        with open_index(self.db) as connection:
            self.assertEqual(
                metadata(connection)["index_fingerprint"], self.info["index_fingerprint"],
            )

    def test_failed_replacement_does_not_destroy_existing_index(self):
        broken = replace(self.corpus, sources=[
            replace(source, kind="invalid-source-kind") if index == 0 else source
            for index, source in enumerate(self.corpus.sources)
        ])
        # The dataclass was deliberately corrupted after validation to exercise DB atomicity.
        with self.assertRaises(sqlite3.IntegrityError):
            build_index(broken, self.db, self.config, replace=True)
        with open_index(self.db) as connection:
            self.assertEqual(
                metadata(connection)["index_fingerprint"], self.info["index_fingerprint"],
            )

    def test_chunk_offsets_and_content_ids_track_actual_evidence(self):
        source = next(source for source in self.corpus.sources if source.kind == "official_review")
        chunks = chunk_source(source, self.config)
        for chunk in chunks:
            self.assertEqual(
                chunk.text, source.sections[chunk.field][chunk.char_start:chunk.char_end],
            )
            self.assertLessEqual(len(chunk.text.split()), self.config.words)
        changed = replace(source, sections={
            field: "CHANGED " + text for field, text in source.sections.items()
        })
        self.assertNotEqual(chunks[0].chunk_id, chunk_source(changed, self.config)[0].chunk_id)

    def test_filters_apply_before_top_k_for_both_methods(self):
        with open_index(self.db) as connection:
            for method in ("bm25", "overlap"):
                hits = search(connection, "quantization", method=method,
                              conference="neurips2024", top_k=1)["hits"]
                self.assertEqual(len(hits), 1)
                self.assertEqual(hits[0]["source_id"], "fixture-review-cache")

    def test_many_chunks_of_one_review_count_as_one_source(self):
        with open_index(self.db) as connection:
            for method in ("bm25", "overlap"):
                result = search(connection, "quantization quality", method=method,
                                conference="iclr2024", kind="official_review", top_k=5)
                ids = [hit["source_id"] for hit in result["hits"]]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(set(ids), {
                    "fixture-review-quant-critical", "fixture-review-quant-positive",
                })
                if method == "bm25":
                    scores = [hit["score"] for hit in result["hits"]]
                    self.assertEqual(scores, sorted(scores))

    def test_queries_cannot_execute_fts_operators_or_sql_and_empty_query_returns_nothing(self):
        with open_index(self.db) as connection:
            for query in ('" OR * NEAR(quantization)', "quantization'); DROP TABLE papers; --"):
                for method in ("bm25", "overlap"):
                    self.assertTrue(search(connection, query, method=method)["hits"])
            for method in ("bm25", "overlap"):
                self.assertEqual(search(connection, "the and of", method=method)["hits"], [])
                self.assertEqual(search(connection, "AUTHORCOMMENTONLY", method=method)["hits"], [])
            self.assertEqual(connection.execute("SELECT count(*) FROM papers").fetchone()[0], 3)


class EvidenceTests(IndexCase):
    def packet(self, query="quantization", **kwargs):
        with open_index(self.db) as connection:
            result = search(connection, query, conference="iclr2024", kind="official_review")
            return create_packet(connection, result, self.base / "runs", **kwargs)

    def test_related_abstract_has_distinct_origin_and_does_not_change_ranking(self):
        with open_index(self.db) as connection:
            retrieval = search(
                connection, "quantization", conference="iclr2024", kind="official_review",
            )
            before = [hit["source_id"] for hit in retrieval["hits"]]
            context = build_context(connection, retrieval)
            related = [
                entry for entry in context["entries"] if entry["origin"] == "added_by_relation"
            ]
            self.assertEqual(len(related), 1)
            self.assertEqual(related[0]["kind"], "author_abstract")
            self.assertEqual(before, [hit["source_id"] for hit in retrieval["hits"]])
            for entry in context["entries"]:
                source = source_record(connection, entry["source_id"])
                self.assertEqual(
                    source["sections"][entry["field"]][entry["char_start"]:entry["char_end"]],
                    entry["text"],
                )

    def test_context_budget_citations_and_exact_prompt_are_saved_without_model(self):
        packet = self.packet(max_chars=23)
        context = read_json(packet / "context.json")
        sources = read_json(packet / "sources.json")
        self.assertEqual(context["text_chars"], 23)
        self.assertEqual(set(sources), {entry["label"] for entry in context["entries"]})
        prompt = (packet / "prompt.txt").read_text()
        for entry in context["entries"]:
            self.assertIn(entry["text"], prompt)
        self.assertEqual(read_json(packet / "metadata.json")["generation_status"], "not_run")
        self.assertFalse((packet / "answer.md").exists())
        self.assertEqual(unknown_citations("Claim [S1] and [S999]", sources), ["S999"])

    def test_no_matching_sources_prevents_even_attempting_generation(self):
        packet = self.packet("zzzxxyynevermatches")
        def fail_if_called(*args, **kwargs):
            self.fail("No API request should be attempted without evidence")
        info = generate_packet(packet, {}, transport=fail_if_called)
        self.assertEqual(info["generation_status"], "not_run")
        self.assertEqual(info["generation_reason"], "no_matching_sources")

    def test_gemini_receives_exact_saved_prompt_and_unknown_citations_are_preserved(self):
        packet = self.packet()
        prompt = (packet / "prompt.txt").read_text()
        def transport(request, timeout):
            body = json.loads(request.data)
            self.assertEqual(body["contents"][0]["parts"][0]["text"], prompt)
            self.assertNotIn("tools", body)
            return io.BytesIO(json.dumps({
                "candidates": [{"content": {"parts": [{"text": "Fake test output [S999]."}]},
                                "finishReason": "STOP"}], "usageMetadata": {"totalTokenCount": 12},
            }).encode())
        info = generate_packet(
            packet, {"GEMINI_API_KEY": "not-a-real-key", "GEMINI_MODEL": "test-model"},
            transport=transport,
        )
        self.assertEqual(info["generation_status"], "invalid_citations")
        self.assertEqual(info["unknown_citations"], ["S999"])
        self.assertIn("[S999]", (packet / "answer.md").read_text())
        self.assertNotIn("not-a-real-key", (packet / "metadata.json").read_text())

    def test_provider_failure_preserves_prompt_and_does_not_expose_secret(self):
        packet = self.packet()
        def transport(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 429, "rate limited", {},
                                         io.BytesIO(b'not-a-real-key'))
        with self.assertRaisesRegex(ValueError, "429"):
            generate_packet(
                packet, {"GEMINI_API_KEY": "not-a-real-key", "GEMINI_MODEL": "test-model"},
                transport=transport,
            )
        self.assertTrue((packet / "prompt.txt").exists())
        info = read_json(packet / "metadata.json")
        self.assertEqual(info["generation_status"], "failed")
        self.assertNotIn("not-a-real-key", json.dumps(info))


class EvaluationTests(IndexCase):
    def setUp(self):
        super().setUp()
        self.questions = self.base / "questions.jsonl"
        self.judgments = self.base / "judgments.jsonl"
        self.questions.write_bytes((FIXTURES / "questions.jsonl").read_bytes())
        self.judgments.write_bytes((FIXTURES / "judgments.jsonl").read_bytes())
        self.frozen = self.base / "frozen.json"

    def freeze(self):
        with open_index(self.db) as connection:
            return freeze_benchmark(connection, self.questions, self.judgments, self.frozen,
                                    allow_synthetic=True)

    def test_hit_counts_unique_sources_before_cutoff(self):
        self.assertTrue(hit_at_k(["a"] * 8 + ["b"], {"b"}, k=2))
        self.assertFalse(hit_at_k(["a", "b", "c"], {"c"}, k=2))
        self.assertFalse(hit_at_k([], {"b"}))

    def test_synthetic_evaluation_requires_explicit_flag(self):
        with open_index(self.db) as connection:
            with self.assertRaisesRegex(ValueError, "Fixtures"):
                freeze_benchmark(connection, self.questions, self.judgments, self.frozen)

    def test_both_methods_exclude_unanswerable_question_from_denominator(self):
        frozen = self.freeze()
        self.assertEqual(frozen["evaluation_type"], "synthetic_test_only")
        with open_index(self.db) as connection:
            for method in ("bm25", "overlap"):
                result = evaluate(connection, self.frozen, method, allow_synthetic=True)
                self.assertEqual(result["hit_at_5"]["denominator"], 2)
                self.assertEqual(result["unanswerable_questions"], 1)
                self.assertEqual(result["questions"][-1]["hit_at_5"], None)
                self.assertEqual(result["generation_quality"], "nie oceniano — brak generacji")

    def test_benchmark_changes_after_freeze_are_rejected(self):
        self.freeze()
        self.questions.write_text(self.questions.read_text() + "\n")
        with open_index(self.db) as connection:
            with self.assertRaisesRegex(ValueError, "po zamrożeniu"):
                evaluate(connection, self.frozen, "bm25", allow_synthetic=True)

    def test_chunk_config_change_after_freeze_is_rejected(self):
        self.freeze()
        other = self.base / "changed.sqlite"
        build_index(self.corpus, other, ChunkConfig(12, 2))
        with open_index(other) as connection:
            with self.assertRaisesRegex(ValueError, "konfiguracja"):
                evaluate(connection, self.frozen, "bm25", allow_synthetic=True)

    def test_frozen_annotations_cannot_be_silently_overwritten(self):
        self.freeze()
        with self.assertRaises(FileExistsError):
            self.freeze()

    def test_wrong_conference_and_wrong_evidence_in_judgment_are_rejected(self):
        rows = [json.loads(line) for line in self.judgments.read_text().splitlines()]
        rows[0]["source_id"] = "fixture-review-cache"
        self.judgments.write_text("\n".join(json.dumps(row) for row in rows))
        with self.assertRaisesRegex(ValueError, "filtra konferencji"):
            self.freeze()
        rows[0]["source_id"] = "fixture-review-quant-critical"
        rows[0]["evidence"] = "Invented supporting text."
        self.judgments.write_text("\n".join(json.dumps(row) for row in rows))
        with self.assertRaisesRegex(ValueError, "nie występuje"):
            self.freeze()


class CliTests(unittest.TestCase):
    def test_checkout_cli_runs_offline_from_build_to_evaluation(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            db, manifest = base / "db.sqlite", base / "manifest.json"
            def run(*args):
                result = subprocess.run(
                    [sys.executable, "-m", "literature_rag", *map(str, args)], cwd=ROOT,
                    capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            run("build", "--snapshot", FIXTURES / "synthetic_snapshot.json", "--db", db,
                "--manifest-output", manifest)
            search_result = run(
                "search", "KV cache", "--db", db, "--conference", "neurips2024", "--json",
            )
            self.assertTrue(search_result["hits"])
            packet = run("ask", "quantization", "--db", db, "--provider", "none",
                         "--runs-dir", base / "runs")
            self.assertEqual(packet["generation_status"], "not_run")
            rebuilt = run("build", "--manifest", manifest, "--db", base / "rebuilt.sqlite")
            self.assertEqual(rebuilt["corpus_fingerprint"], search_result["corpus_fingerprint"])
            frozen = base / "frozen.json"
            run("freeze", "--db", db, "--questions", FIXTURES / "questions.jsonl",
                "--judgments", FIXTURES / "judgments.jsonl", "--output", frozen,
                "--allow-synthetic")
            result = run("evaluate", "--db", db, "--frozen", frozen, "--method", "overlap",
                         "--allow-synthetic", "--output", base / "results.json")
            self.assertEqual(result["evaluation_type"], "synthetic_test_only")
            self.assertFalse(run("doctor", "--db", db)["network_used"])


if __name__ == "__main__":
    unittest.main()
