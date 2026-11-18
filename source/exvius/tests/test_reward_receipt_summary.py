"""Synthetic, read-only challenge receipt summary tests for FFBE-Custom.

No original game data, ffbe_battle imports, native execution, network, saves
or player state runtime. Tests model fields that exvius_repeat.complete_attempt
stores only after its controlled challenge credit transaction.
"""
from __future__ import annotations

from copy import deepcopy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from reward_receipt_summary import summarize_challenge_reward_receipts as summarize


def reward(kind, item, count, **metadata):
    return {"kind": kind, "id": item, "count": count, **metadata}


def completed(mid="m1", seq=1, paid=None, blocked=None, **extras):
    return {
        "mid": mid, "sequence": seq, "status": "completed", "cleared": True,
        "paid": deepcopy(paid) if paid is not None else [
            {"id": "c1", "rewards": [
                reward(50, 1, 20), reward(30, 1, 50), reward(20, 101, 2),
            ]}
        ],
        "blocked": deepcopy(blocked) if blocked is not None else [],
        **extras,
    }


def totals(view):
    return {(x["kind"], x["id"]): x["count"] for x in view["totals"]}


class RewardReceiptSummary(unittest.TestCase):
    def test_empty_is_a_read_only_empty_summary(self):
        view = summarize([])
        self.assertEqual(view["receipt_count"], 0)
        self.assertEqual(view["totals"], [])
        self.assertEqual(view["receipts"], [])
        self.assertTrue(view["preview_only"])
        self.assertFalse(view["credited"])
        self.assertEqual(view["scope"], "challenge-reward-receipts-only")

    def test_exact_original_paid_shape_and_total_order(self):
        view = summarize([completed()])
        self.assertEqual(view["receipt_count"], 1)
        self.assertEqual(view["totals"], [
            reward(50, 1, 20), reward(30, 1, 50), reward(20, 101, 2)
        ])
        self.assertEqual(view["receipts"][0]["paid_challenge_count"], 1)
        self.assertEqual(view["receipts"][0]["paid_reward_row_count"], 3)
        self.assertEqual(view["receipts"][0]["sequence"], 1)

    def test_idempotent_repeated_copies_of_one_completed_receipt(self):
        first = completed()
        later = deepcopy(first)
        later["quest_progress_recorded"] = True
        later["mission_bonus_awards"] = [reward(30, 1, 99999)]
        view = summarize([first, deepcopy(first), later, deepcopy(later)])
        self.assertEqual(view["receipt_count"], 1)
        self.assertEqual(view["duplicate_snapshots_ignored"], 3)
        self.assertEqual(totals(view), {(50, 1): 20, (30, 1): 50, (20, 101): 2})

    def test_real_one_time_non_lapis_and_repeat_lapis_pattern(self):
        second = completed(seq=2, paid=[{
            "id": "c1", "rewards": [reward(50, 1, 20)]
        }])
        third = completed(seq=3, paid=[{
            "id": "c1", "rewards": [reward(50, 1, 20)]
        }])
        view = summarize([completed(), second, third, deepcopy(third)])
        self.assertEqual(view["receipt_count"], 3)
        self.assertEqual(view["duplicate_snapshots_ignored"], 1)
        self.assertEqual(totals(view), {(50, 1): 60, (30, 1): 50, (20, 101): 2})
        self.assertEqual(view["by_mission"][0]["receipt_count"], 3)

    def test_two_missions_have_separate_aggregates(self):
        other = completed("m2", 2, paid=[{
            "id": "c-other", "rewards": [reward(50, 1, 5), reward(21, 900, 1)]
        }])
        view = summarize([completed(), other])
        self.assertEqual(view["receipt_count"], 2)
        self.assertEqual(totals(view), {
            (50, 1): 25, (30, 1): 50, (20, 101): 2, (21, 900): 1
        })
        self.assertEqual([v["mission_id"] for v in view["by_mission"]], ["m1", "m2"])
        self.assertEqual(view["by_mission"][1]["totals"],
                         [reward(50, 1, 5), reward(21, 900, 1)])

    def test_duplicate_original_reward_occurrences_are_not_lost(self):
        rows = [{"id": "dupe", "rewards": [
            reward(30, 1, 5), reward(50, 1, 20), reward(30, 1, 7)
        ]}]
        view = summarize([completed(paid=rows)])
        self.assertEqual(view["totals"], [reward(30, 1, 12), reward(50, 1, 20)])
        self.assertEqual(view["receipts"][0]["paid_reward_row_count"], 3)

    def test_blocked_entries_not_added_to_paid_totals(self):
        blocked = [{"id": "c-bad", "entry": "999:1:1",
                    "reason": "unsupported reward type or missing master data"}]
        result = summarize([completed(blocked=blocked)])
        self.assertEqual(result["blocked_entry_count"], 1)
        self.assertEqual(result["receipts"][0]["blocked_entry_count"], 1)
        self.assertEqual(totals(result)[(50, 1)], 20)
        self.assertNotIn((999, 1), totals(result))

    def test_completed_with_no_paid_rows_is_not_a_fabricated_award(self):
        view = summarize([completed(paid=[], blocked=[])])
        self.assertEqual(view["receipt_count"], 1)
        self.assertEqual(view["totals"], [])
        self.assertEqual(view["receipts"][0]["paid_challenge_count"], 0)

    def test_pending_and_unknown_status_skipped(self):
        pending = completed()
        pending["status"] = "pending"
        other = completed(seq=2)
        other["status"] = "unknown"
        view = summarize([pending, other])
        self.assertEqual(view["receipt_count"], 0)
        self.assertEqual(view["skipped"], [
            {"index": 0, "reason": "unsettled-or-unknown-status"},
            {"index": 1, "reason": "unsettled-or-unknown-status"}
        ])

    def test_failed_or_unknown_stored_false_never_proves_defeat(self):
        a = completed(paid=[])
        a["cleared"] = False
        b = completed(seq=2, paid=[])
        b["cleared"] = None
        result = summarize([a, b])
        self.assertEqual(result["totals"], [])
        self.assertEqual([x["reason"] for x in result["skipped"]],
                         ["unverified-clear-status", "unverified-clear-status"])

    def test_constructor_like_record_cannot_claim_a_credit(self):
        view = summarize([{"MissionResultResponse": True, "cleared": True,
                           "paid": [{"id": "fake", "rewards": [reward(50, 1, 999)]}]}])
        self.assertEqual(view["totals"], [])
        self.assertEqual(view["receipt_count"], 0)

    def test_missing_record_fields_and_identities_skip_instead_of_guessing(self):
        cases = [
            None, {}, completed(seq=0), completed(seq=True),
            completed(mid="", seq=1),
            {"mid": "m1", "status": "completed", "cleared": True,
             "paid": [], "blocked": []},
            {"mid": "m1", "sequence": 1, "status": "completed",
             "cleared": True, "paid": []},
        ]
        view = summarize(cases)
        self.assertEqual(view["receipt_count"], 0)
        self.assertEqual(view["totals"], [])
        self.assertEqual(len(view["skipped"]), len(cases))

    def test_same_sequence_conflicting_payload_rejected(self):
        changed = completed()
        changed["paid"][0]["rewards"][0]["count"] = 99
        with self.assertRaisesRegex(ValueError, "conflicting"):
            summarize([completed(), changed])

    def test_same_sequence_different_mission_id_rejected(self):
        with self.assertRaisesRegex(ValueError, "conflicting"):
            summarize([completed("m1", 1), completed("m2", 1)])

    def test_invalid_reward_quantity_or_id_fails_closed(self):
        for bad in (0, -1, True, "1.5", None, 1.5, "nan"):
            with self.subTest(bad=bad):
                fake = completed(paid=[{
                    "id": "c", "rewards": [reward(50, 1, bad)]
                }])
                with self.assertRaises(ValueError):
                    summarize([fake])
        for bad in ("oops", -1, True, {}, []):
            with self.subTest(bad=bad):
                fake = completed(paid=[{"id": "c", "rewards": [reward(50, bad, 1)]}])
                with self.assertRaises(ValueError):
                    summarize([fake])

    def test_duplicate_challenge_and_malformed_challenge_rejected(self):
        a = {"id": "c1", "rewards": [reward(50, 1, 2)]}
        with self.assertRaisesRegex(ValueError, "duplicate challenge"):
            summarize([completed(paid=[a, deepcopy(a)])])
        for bad in ({"id": "c1", "rewards": []},
                    {"id": "c1", "rewards": "50:1:1"}, None, 55):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    summarize([completed(paid=[bad])])

    def test_nonclear_with_paid_rows_is_a_contradiction(self):
        receipt = completed()
        receipt["cleared"] = False
        with self.assertRaisesRegex(ValueError, "contradicts"):
            summarize([receipt])

    def test_malformed_blocked_record_fails_closed(self):
        for row in (None, {}, {"id": "c", "reason": 5}):
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    summarize([completed(blocked=[row])])

    def test_input_type_must_be_list_or_tuple(self):
        for bad in (None, {}, "records", 1):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    summarize(bad)
        self.assertEqual(summarize(())["receipt_count"], 0)

    def test_mutating_summary_cannot_change_source_or_player_state(self):
        state = {
            "wallet": {"50:1": 20}, "inventory": {"20:101": 2},
            "progress": {"missions": ["m1"]},
            "save": {"version": 7, "dirty": False},
            "exvius_repeat": {"attempt": completed()},
        }
        before = deepcopy(state)
        attempt = state["exvius_repeat"]["attempt"]
        result = summarize([attempt])
        result["totals"][0]["count"] = 1000000
        result["receipts"][0]["sequence"] = -1
        result["by_mission"][0]["totals"][0]["count"] = -1
        self.assertEqual(state, before)

    def test_deterministic_reporting_without_creating_receipts(self):
        originals = [completed(), completed(seq=2, paid=[{
            "id": "c1", "rewards": [reward(50, 1, 20)]
        }])]
        before = deepcopy(originals)
        expected = summarize(originals)
        for _ in range(35):
            self.assertEqual(summarize(originals), expected)
        self.assertEqual(originals, before)
        self.assertFalse(expected["credited"])
        self.assertEqual(expected["source"], "exvius_repeat.attempt.paid")


if __name__ == "__main__":
    unittest.main()
