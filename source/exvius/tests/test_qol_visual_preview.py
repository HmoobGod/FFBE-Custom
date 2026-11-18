
"""Synthetic tests for offline visual HTML generated from actual pure helpers."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "qol_visual_preview.py"
spec = importlib.util.spec_from_file_location("qol_visual_preview", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OfflineVisualQoLTests(unittest.TestCase):
    def test_precomputed_roster_views_match_known_sort_and_filter(self):
        data = module.preview_data()
        self.assertEqual(len(data["roster"]), 5 * 3 * 2)
        self.assertEqual([r["instance_id"] for r in data["roster"]["original|all|0"]],
                         ["101","102","103","104"])
        self.assertEqual([r["instance_id"] for r in data["roster"]["level_desc|all|0"]],
                         ["102","104","103","101"])
        self.assertEqual([r["instance_id"] for r in data["roster"]["favorites_first|active|1"]],
                         ["102","104"])
        self.assertEqual([r["instance_id"] for r in data["roster"]["original|warehouse|0"]],
                         ["103"])

    def test_precomputed_party_views_compare_but_cannot_apply(self):
        data = module.preview_data()
        self.assertEqual(set(data["party"]), {"original","farming","boss"})
        self.assertTrue(data["party"]["original"]["unchanged"])
        self.assertEqual([r["slot"] for r in data["party"]["farming"]["slot_changes"]],
                         [0,1,2])
        self.assertEqual(data["party"]["farming"]["active_deck_id"], "0")
        self.assertEqual(data["party"]["boss"]["target_deck_id"], "1")
        self.assertFalse(data["party"]["boss"]["target_is_active"])
        for proposal in data["party"].values():
            self.assertTrue(proposal["preview_only"])
            self.assertFalse(proposal["applied"])
            self.assertTrue(proposal["manual_gameplay_unchanged"])

    def test_all_ephemeral_favorite_and_filter_combinations_precomputed(self):
        data = module.preview_data()
        self.assertEqual(len(data["quest_ids"]), 3)
        self.assertEqual(len(data["quests"]), 8 * 2 * 2 * 3 * 3)
        base = data["quests"]["0|0|0|all|all"]
        self.assertEqual([r["id"] for r in base["entries"]],
                         ["1110100","1110101","8991106"])
        self.assertEqual(base["visible_favorites"], 0)
        view = data["quests"]["5|0|1|all|all"]
        self.assertEqual([r["id"] for r in view["entries"]],
                         ["1110100","8991106","1110101"])
        self.assertEqual(view["visible_favorites"], 2)
        only = data["quests"]["5|1|0|1|100"]
        self.assertEqual([r["id"] for r in only["entries"]], ["1110100"])
        empty = data["quests"]["0|1|0|all|all"]
        self.assertEqual(empty["entries"], [])

    def test_generation_is_deterministic_pure_and_synthetic(self):
        units, party, proposals, quests = module.synthetic_inputs()
        original = deepcopy((units,party,proposals,quests))
        first = module.build_html()
        self.assertEqual(module.build_html(), first)
        self.assertEqual((units,party,proposals,quests), original)
        self.assertIn("fictional_samples_only", first)
        self.assertIn("qol-fixtures", first)
        self.assertIn("aria-pressed", first)
        self.assertIn("Offline QoL Preview", first)
        self.assertNotIn("__QOL_FIXTURES__", first)

    def test_complete_html_disables_network_and_storage(self):
        html = module.build_html()
        self.assertIn("default-src 'none'", html)
        self.assertIn("connect-src 'none'", html)
        self.assertIn("form-action 'none'", html)
        for forbidden in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage",
                          "indexedDB", "WebSocket", "navigator.sendBeacon",
                          "PlayerState", "Frida", "NativeFunction", "original game asset"):
            # The informational note may spell PlayerState/Frida, but never
            # references these as executable JS function calls.
            if forbidden in ("PlayerState", "Frida"):
                self.assertLess(html.count(forbidden), 3)
                continue
            self.assertNotIn(forbidden, html)

    def test_stdout_generation_from_empty_cwd_writes_no_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, "-B", str(SOURCE)], cwd=temporary, input="",
                text=True, capture_output=True, check=False, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.startswith("<!doctype html>"))
            self.assertIn("Quality of Life", result.stdout)
            self.assertEqual(result.stderr, "")
            self.assertEqual(list(Path(temporary).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
