"""The browser export contract must round-trip through the production importer."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from literature_rag.snapshot import normalize_snapshot

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(
    shutil.which("node"), "Node is only needed to test the optional browser exporter",
)
class BrowserExportTests(unittest.TestCase):
    def test_prepared_export_preserves_selection_data_as_javascript_without_running_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            selection = {
                "schema_version": 1, "scope_rule": 'Cytat "test" i polskie znaki: ąę\nDrugi wiersz',
                "venues": {"ICLR.cc/2024/Conference": ["fixture-iclr"],
                           "NeurIPS.cc/2024/Conference": ["fixture-neurips"]},
            }
            config = base / "selection.json"
            output = base / "export.js"
            config.write_text(json.dumps(selection, ensure_ascii=False))
            prepared = subprocess.run(
                [sys.executable, "scripts/prepare_browser_export.py", "--selection", str(config),
                 "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            code = "require(process.argv[1]); " + (
                "process.stdout.write(JSON.stringify(globalThis.__openreviewTopicSelection));"
            )
            loaded = subprocess.run(
                ["node", "-e", code, str(output)], capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(loaded.returncode, 0, loaded.stderr)
            self.assertEqual(json.loads(loaded.stdout), selection)

    def test_mock_browser_export_round_trips_through_normalizer(self):
        code = """
        const {webcrypto} = require('node:crypto');
        const {createExporter} = require('./scripts/export-openreview.js');
        const {fixtureApi} = require('./tests/helpers/openreview_api.cjs');
        const fake = fixtureApi();
        createExporter({fetch: fake.fetch, crypto: webcrypto, targetPerVenue: 1,
          pageSize: 1, sleep: async () => {}, progress: () => {}}).run().then(snapshot => {
          snapshot.dataset_type = 'synthetic';
          snapshot.provenance.selection_method = 'Mock API for software compatibility test only';
          process.stdout.write(JSON.stringify(snapshot));
        }).catch(error => {console.error(error.message); process.exitCode = 1;});
        """
        result = subprocess.run(
            ["node", "-e", code], cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        corpus = normalize_snapshot(json.loads(result.stdout))
        self.assertEqual(len(corpus.papers), 2)
        self.assertEqual(len({paper.conference for paper in corpus.papers}), 2)
        self.assertTrue(all(source.kind in ("official_review", "author_abstract")
                            for source in corpus.sources))
        self.assertTrue(all(source.url.startswith("https://example.invalid/")
                            for source in corpus.sources))
