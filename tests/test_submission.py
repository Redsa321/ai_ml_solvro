"""Hand-in archives retain reproducible inputs and reject secret or corrupt files."""

import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.package_submission import RUN_FILES, extract_verified, package


class SubmissionPackageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.archive = self.base / "submission.tar.gz"
        self.release = {"artifacts": ["data/raw/selected.json"],
                        "example_runs": {"q01": "runs/example"}}
        files = {"README.md": "Test submission", ".env": "SECRET_DO_NOT_PACKAGE",
                 ".env.example": "GEMINI_API_KEY=", "literature_rag/__init__.py": "",
                 "literature_rag/__pycache__/cached.pyc": "cache",
                 "data/raw/selected.json": "{}", "data/raw/unrelated.json": "{}",
                 "runs/unrelated/prompt.txt": "Unrelated", "scripts/local.env": "Not code"}
        for filename in RUN_FILES:
            files[f"runs/example/{filename}"] = "Example evidence"
        for relative, content in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.save_release()

    def save_release(self):
        path = self.root / "reports/submission.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.release))

    def test_selected_data_and_examples_round_trip_without_secrets_or_unrelated_runs(self):
        package(self.root, "reports/submission.json", self.archive)
        root, inventory = extract_verified(self.archive, self.base / "unpacked")
        self.assertTrue((root / "data/raw/selected.json").is_file())
        self.assertTrue((root / "runs/example/prompt.txt").is_file())
        self.assertTrue((root / ".env.example").is_file())
        for relative in (".env", "data/raw/unrelated.json", "runs/unrelated/prompt.txt",
                         "literature_rag/__pycache__/cached.pyc"):
            self.assertFalse((root / relative).exists())
        self.assertNotIn("SECRET_DO_NOT_PACKAGE", json.dumps(inventory))

    def test_manifest_cannot_force_inclusion_of_secrets_or_files_outside_project(self):
        for forbidden in (".env", "../outside.json", "/tmp/absolute.json"):
            self.release["artifacts"] = [forbidden]
            self.save_release()
            with self.subTest(path=forbidden), self.assertRaises(ValueError):
                package(self.root, "reports/submission.json", self.archive)
        self.assertFalse(self.archive.exists())

    def test_modified_file_is_rejected_before_extraction(self):
        package(self.root, "reports/submission.json", self.archive)
        corrupt = self.base / "corrupt.tar.gz"
        with tarfile.open(self.archive, "r:gz") as source, tarfile.open(corrupt, "w:gz") as dest:
            for member in source.getmembers():
                with source.extractfile(member) as stream:
                    data = stream.read()
                if member.name.endswith("README.md"):
                    data = b"Modified content"
                    member.size = len(data)
                dest.addfile(member, io.BytesIO(data))
        with self.assertRaisesRegex(ValueError, "suma kontrolna"):
            extract_verified(corrupt, self.base / "corrupt-output")
        self.assertFalse((self.base / "corrupt-output").exists())
