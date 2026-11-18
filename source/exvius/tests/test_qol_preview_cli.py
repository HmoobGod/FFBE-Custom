"""Run the standalone QoL CLI with synthetic stdin, never game data.

Every test starts a new Python process with -B in an isolated empty cwd.
No save files, game assets, network, native hooks, runtime PlayerState or
private user information is accessed.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "qol_preview_cli.py"


def roster():
    return [
        {"instance_id": "101", "level": 12, "favourite": 0, "storage_state": 0},
        {"instance_id": "102", "level": 55, "favourite": 1, "storage_state": 1},
        {"instance_id": "103", "level": 38, "favourite": 1, "storage_state": 0},
    ]


def party():
    return {
        "active_deck": 0,
        "decks": [
            {"id": 0, "name": "Normal",
             "members": [{"member_type": 0, "disp_order": 0, "instance_id": "101"}]},
            {"id": 1, "name": "Boss",
             "members": [{"member_type": 0, "disp_order": 0, "instance_id": "102"}]},
        ],
    }


def missions():
    return [
        {"qo3PECw6": "1001", "gQR24kST": "1", "U9iHsau3": "10"},
        {"qo3PECw6": "1002", "gQR24kST": "1", "U9iHsau3": "10"},
        {"qo3PECw6": "2001", "gQR24kST": "50", "U9iHsau3": "20"},
    ]


def receipt(mid="1001", seq=1, *, cleared=True, paid=None, status="completed"):
    return {
        "mid": mid, "sequence": seq, "status": status,
        "cleared": cleared, "blocked": [],
        "paid": (
            [{"id": "c1", "rewards": [
                {"kind": 50, "id": 1, "count": 20},
                {"kind": 30, "id": 1, "count": 10},
            ]}] if paid is None else paid
        ),
    }


class QoLPreviewCLITests(unittest.TestCase):
    def run_cli(self, *args, payload=None, raw=None):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-B", str(CLI), *args],
                input=raw if raw is not None else json.dumps(payload),
                text=True, capture_output=True, cwd=directory,
                timeout=10, check=False,
            )
            self.assertEqual(list(Path(directory).iterdir()), [])
            return result

    def test_roster_text_is_human_readable_and_original_order(self):
        payload = {"roster": roster()}
        original = deepcopy(payload)
        p = self.run_cli("roster", payload=payload)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("SOURCE-ONLY PREVIEW", p.stdout)
        self.assertIn("Roster: 3 unit(s)", p.stdout)
        self.assertLess(p.stdout.index("Unit 101"), p.stdout.index("Unit 102"))
        self.assertLess(p.stdout.index("Unit 102"), p.stdout.index("Unit 103"))
        self.assertEqual(payload, original)

    def test_roster_filters_reuse_pure_view_not_new_sort_logic(self):
        p = self.run_cli("--json", "roster", "--sort", "favorites_level_desc",
                         "--storage", "active", payload={"roster": roster()})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual([x["instance_id"] for x in json.loads(p.stdout)],
                         ["103", "101"])
        self.assertEqual(p.stderr, "")

    def test_roster_favorites_only(self):
        p = self.run_cli("--json", "roster", "--favorites-only",
                         payload={"roster": roster()})
        self.assertEqual([x["instance_id"] for x in json.loads(p.stdout)],
                         ["102", "103"])

    def test_party_text_shows_changes_but_does_not_apply(self):
        payload = {
            "roster": roster(), "party": party(),
            "preset": {"id": 1, "name": "Boss+", "members": [
                {"member_type": 0, "disp_order": 0, "instance_id": "103"},
            ]},
        }
        old = deepcopy(payload)
        p = self.run_cli("party", payload=payload)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Deck 1 (active=0): Boss -> Boss+", p.stdout)
        self.assertIn("Slot 1: 102 -> 103", p.stdout)
        self.assertIn("NOT APPLIED", p.stdout)
        self.assertEqual(payload, old)

    def test_party_json_proves_active_deck_unchanged(self):
        p = self.run_cli("--json", "party", payload={
            "roster": roster(), "party": party(),
            "preset": {"id": 1, "members": [
                {"member_type": 0, "disp_order": 0, "instance_id": "101"}
            ]},
        })
        self.assertEqual(p.returncode, 0, p.stderr)
        d = json.loads(p.stdout)
        self.assertTrue(d["preview_only"])
        self.assertFalse(d["applied"])
        self.assertEqual(d["active_deck_id"], "0")
        self.assertFalse(d["target_is_active"])

    def test_party_invalid_unowned_rejected_no_partial_stdout(self):
        p = self.run_cli("party", payload={
            "roster": roster(), "party": party(),
            "preset": {"id": 1, "members": [
                {"member_type": 0, "disp_order": 0, "instance_id": "999"}
            ]},
        })
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("unowned", p.stderr)

    def test_quest_favorites_text_stably_reorders_without_navigation(self):
        p = self.run_cli("quests", "--favorites-first", payload={
            "missions": missions(), "favorite_ids": ["2001", "1001"]
        })
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertLess(p.stdout.index("Mission 1001"), p.stdout.index("Mission 2001"))
        self.assertLess(p.stdout.index("Mission 2001"), p.stdout.index("Mission 1002"))
        self.assertIn("navigation and progress unchanged", p.stdout)

    def test_quest_favorites_source_mode_and_dungeon_filters(self):
        p = self.run_cli("--json", "quests", "--favorites-only", "--mode", "1",
                         "--dungeon", "10", payload={
            "missions": missions(), "favorite_ids": ["2001", "1002"]
        })
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual([r["mission_id"] for r in data["entries"]], ["1002"])
        self.assertFalse(data["navigation_performed"])
        self.assertFalse(data["persisted"])

    def test_unknown_favorite_rejected(self):
        p = self.run_cli("quests", payload={
            "missions": missions(), "favorite_ids": ["9999"]
        })
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("outside the catalog", p.stderr)

    def test_rewards_text_reports_credited_challenges_but_no_payout(self):
        p = self.run_cli("rewards", payload={
            "attempt_snapshots": [receipt(), receipt(), receipt(seq=2, paid=[
                {"id": "c1", "rewards": [{"kind": 50, "id": 1, "count": 20}]}
            ])],
        })
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Challenge receipts: 2 unique; 1 duplicate copies ignored", p.stdout)
        self.assertIn("Reward kind=50 id=1 count=40", p.stdout)
        self.assertIn("Reward kind=30 id=1 count=10", p.stdout)
        self.assertIn("NO CREDIT", p.stdout)

    def test_rewards_json_does_not_infer_unknown_outcome(self):
        unknown = receipt(cleared=False, paid=[])
        pending = receipt(seq=2, status="pending")
        p = self.run_cli("--json", "rewards", payload={
            "attempt_snapshots": [unknown, pending]
        })
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["totals"], [])
        self.assertEqual(data["receipt_count"], 0)
        self.assertEqual(len(data["skipped"]), 2)
        self.assertFalse(data["credited"])

    def test_conflicting_receipt_duplicate_fails_without_partial_output(self):
        other = receipt()
        other["paid"][0]["rewards"][0]["count"] = 999
        p = self.run_cli("--json", "rewards", payload={
            "attempt_snapshots": [receipt(), other]
        })
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("conflicting", p.stderr)

    def test_reject_invalid_json_and_unknown_envelope_keys(self):
        for raw in ("not-json", "[]", '{"roster":NaN}', ""):
            with self.subTest(raw=raw):
                p = self.run_cli("roster", raw=raw)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, "")
        p = self.run_cli("roster", payload={"roster": roster(), "wallet": {"gil": 10}})
        self.assertEqual(p.returncode, 2)
        self.assertIn("invalid preview fields", p.stderr)

    def test_missing_fields_rejected(self):
        for command, payload in [
            ("roster", {}), ("party", {"roster": roster()}),
            ("quests", {"favorite_ids": []}), ("rewards", {})
        ]:
            with self.subTest(view=command):
                p = self.run_cli(command, payload=payload)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, "")

    def test_limit_rejects_input_before_parsing(self):
        p = self.run_cli("roster", raw=" " * (1_048_576 + 1))
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("preview limit", p.stderr)

    def test_help_does_not_require_input_data(self):
        with tempfile.TemporaryDirectory() as directory:
            p = subprocess.run(
                [sys.executable, "-B", str(CLI), "--help"],
                input="", text=True, capture_output=True, cwd=directory, timeout=10
            )
            self.assertEqual(p.returncode, 0)
            self.assertIn("roster", p.stdout)
            self.assertIn("party", p.stdout)
            self.assertIn("quests", p.stdout)
            self.assertIn("rewards", p.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_cli_never_imports_runtime_player_state_or_native_ui(self):
        source = CLI.read_text()
        self.assertNotIn("from player_state import", source)
        self.assertNotIn("import ffbe_state", source)
        self.assertNotIn("import offline_menu", source)
        self.assertNotIn("import android", source)
        self.assertNotIn("subprocess.", source)


if __name__ == "__main__":
    unittest.main()
