"""Extract to a fresh directory, rebuild the index, and reproduce the recorded results."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from package_submission import extract_verified, sha256


def verify(archive: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="literature-rag-check-") as temporary:
        root, inventory = extract_verified(archive, Path(temporary))
        release = json.loads((root / inventory["release_report"]).read_text())
        environment = {key: value for key, value in os.environ.items()
                       if key not in {"PYTHONPATH", "GEMINI_API_KEY", "GEMINI_MODEL",
                                      "GENERATION_PROVIDER"}}

        def run(*args):
            result = subprocess.run(
                [sys.executable, "-m", "literature_rag", *map(str, args)],
                cwd=root, env=environment, text=True, capture_output=True, timeout=30,
            )
            if result.returncode:
                raise ValueError(f"Nie udało się odtworzyć komendy {args[0]}: {result.stderr}")
            return json.loads(result.stdout)

        database = root / release["database"]
        database.unlink()  # The check must rebuild, not reuse the bundled database.
        built = run("build", "--manifest", release["manifest"], "--db", release["database"])
        if built["index_fingerprint"] != release["index_fingerprint"]:
            raise ValueError("Odbudowany indeks ma inny fingerprint.")
        repeated = run("build", "--manifest", release["manifest"], "--db", release["database"])
        if not repeated["reused"] or repeated["counts"] != built["counts"]:
            raise ValueError("Ponowny import nie jest idempotentny.")
        checks = {}
        for method, expected_file in release["evaluation_results"].items():
            output = f"runs/reproduction-{method}.json"
            run("evaluate", "--frozen", release["frozen"], "--method", method, "--output", output)
            actual = json.loads((root / output).read_text())
            expected = json.loads((root / expected_file).read_text())
            expected_ids = [[hit["source_id"] for hit in q["retrieval"]["hits"]]
                            for q in expected["questions"]]
            actual_ids = [[hit["source_id"] for hit in q["retrieval"]["hits"]]
                          for q in actual["questions"]]
            if actual["hit_at_5"] != expected["hit_at_5"] or actual_ids != expected_ids:
                raise ValueError(f"Wyniki {method} nie zostały odtworzone.")
            checks[method] = {"same_metric": True, "same_source_rankings": True}
        packet = run("ask", "Compare OmniQuant and QLLM quantization limitations",
                     "--provider", "none", "--runs-dir", "runs/reproduction-prompt")
        if packet["generation_status"] != "not_run":
            raise ValueError("Weryfikacja nie powinna uruchamiać generacji.")
        directory = root / packet["packet"]
        for filename in ("prompt.txt", "context.json", "sources.json", "metadata.json"):
            if not (directory / filename).is_file():
                raise ValueError("Brak artefaktu promptu po odbudowie.")
        doctor = run("doctor")
        if doctor["integrity_check"] != "ok" or doctor["foreign_key_errors"]:
            raise ValueError("Odbudowana baza nie przeszła kontroli spójności.")
        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "archive": str(archive), "archive_sha256": sha256(archive.read_bytes()),
            "fresh_directory": True, "bundled_database_removed_before_rebuild": True,
            "file_checksums_verified": True, "offline_rebuild": True,
            "index_fingerprint_matches": True, "idempotent_import": True,
            "counts": built["counts"], "evaluation_reproduced": checks,
            "prompt_created_without_generation": True,
            "integrity_check": "ok", "foreign_key_errors": 0,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprawdź pakiet w świeżym folderze bez API.")
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, default=Path("reports/package-verification.json"))
    args = parser.parse_args()
    try:
        result = verify(args.archive)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f"Błąd: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
