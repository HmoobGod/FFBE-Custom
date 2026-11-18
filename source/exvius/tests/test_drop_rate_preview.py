"""Synthetic source-only test coverage for inert normal-drop rate previews.

No server runtime, original game tables, APK, native RNG, inventory,
player save, result screen, quest progress or credits are touched.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from drop_rate_preview import (
    DEFAULT_DROP_RATE_OPTIONS, normalize_drop_rate_options,
    preview_normal_drop_rates,
)


def fixture():
    return {
        "wallet": {"gil": 300, "lapis": 20},
        "inventory": {"items": [{"item_type": 20, "item_id": 55, "count": 1}]},
        "mission_progress": {"cleared": ["mission1"], "switches": [101]},
        "save": {"schema": "v7", "dirty": False},
        "receipts": {"attempt": {"mid": "mission1", "paid": []}},
        "last_drops": {"mission1": ["20:55:1"]},
    }


class DropRatePreviewTests(unittest.TestCase):
    def test_defaults_preserve_native_looking_input_rate(self):
        csv = "20:1209000976:450:100,20:1209000975:1200:30"
        preview = preview_normal_drop_rates(csv)
        self.assertEqual(normalize_drop_rate_options(), {"normal_drop_multiplier": 1})
        self.assertEqual(dict(DEFAULT_DROP_RATE_OPTIONS), {"normal_drop_multiplier": 1})
        self.assertEqual(preview["multiplier"], 1)
        self.assertEqual(preview["candidate_count"], 2)
        self.assertEqual([r["original_rate_percent_model"] for r in preview["candidates"]], [100, 30])
        self.assertEqual([r["hypothetical_rate_percent_model"] for r in preview["candidates"]], [100, 30])
        self.assertTrue(preview["preview_only"])
        self.assertFalse(preview["rolled"])
        self.assertFalse(preview["credited"])
        self.assertFalse(preview["native_rate_semantics_verified"])
        self.assertFalse(preview["source_eligibility_verified"])

    def test_optional_integer_multiplier_is_independent(self):
        csv = "20:10:1:25"
        for factor in (1, 2, 3, 4, 5):
            with self.subTest(factor=factor):
                view = preview_normal_drop_rates(csv, {"normal_drop_multiplier": factor})
                self.assertEqual(view["candidates"][0]["hypothetical_rate_percent_model"],
                                 min(100, 25 * factor))
                self.assertEqual(view["candidates"][0]["original_rate_percent_model"], 25)

    def test_zero_remains_zero_even_at_five_x(self):
        view = preview_normal_drop_rates("20:10:1:0", {"normal_drop_multiplier": 5})
        self.assertEqual(view["candidates"][0]["hypothetical_rate_percent_model"], 0)

    def test_rate_is_clamped_not_overflowed(self):
        view = preview_normal_drop_rates("20:10:1:60,20:11:1:100",
                                         {"normal_drop_multiplier": 5})
        self.assertEqual([c["hypothetical_rate_percent_model"] for c in view["candidates"]],
                         [100, 100])

    def test_empty_candidate_pool_stays_empty(self):
        view = preview_normal_drop_rates("", {"normal_drop_multiplier": 5})
        self.assertEqual(view["candidate_count"], 0)
        self.assertEqual(view["candidates"], [])
        self.assertFalse(view["rolled"])

    def test_preserves_all_original_candidate_identifiers_amounts_order(self):
        csv = "10:1001:2:30,20:1002:4:50,21:1003:1:100"
        view = preview_normal_drop_rates(csv, {"normal_drop_multiplier": 3})
        self.assertEqual([(c["kind"], c["id"], c["count"]) for c in view["candidates"]],
                         [(10, 1001, 2), (20, 1002, 4), (21, 1003, 1)])
        self.assertEqual([c["index"] for c in view["candidates"]], [0, 1, 2])

    def test_same_candidate_repeated_is_not_collapsed_into_new_awards(self):
        view = preview_normal_drop_rates("20:55:1:30,20:55:1:30")
        self.assertEqual(view["candidate_count"], 2)
        self.assertEqual(view["candidates"][0]["id"], view["candidates"][1]["id"])
        self.assertNotIn("selected", view)
        self.assertNotIn("awards", view)
        self.assertNotIn("paid", view)

    def test_invalid_negative_fractional_and_over_100_rates_reject(self):
        for rate in ("-1", "101", "1000", "10.5", "", "1e1", "0x30", " 30", "30 ",
                     "NaN", "+30"):
            with self.subTest(rate=rate):
                with self.assertRaises(ValueError):
                    preview_normal_drop_rates(f"20:55:1:{rate}")

    def test_invalid_empty_missing_or_extra_tuple_fields_reject(self):
        for entry in ("20:55:1", "20:55:1:30:0", "20:55:1:30,",
                      ",20:55:1:30", "20:55:1:30,,20:12:1:30",
                      "20:55::30", "not-a-tuple", "20:55:1:30\n"):
            with self.subTest(entry=entry):
                with self.assertRaises(ValueError):
                    preview_normal_drop_rates(entry)

    def test_nonpositive_quantity_rejects(self):
        for count in ("0", "-1", "1.5", "", "nan"):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    preview_normal_drop_rates(f"20:55:{count}:50")

    def test_malformed_item_and_type_rejected(self):
        for original in ("?:55:1:50", "-1:55:1:50", "20:-2:1:50", "20:xx:1:50",
                         "True:55:1:50", "20:５５:1:50"):
            with self.subTest(original=original):
                with self.assertRaises(ValueError):
                    preview_normal_drop_rates(original)

    def test_invalid_configuration_rejected(self):
        for bad in (0, -1, 6, 2.5, True, False, "2", None, [], {}, float("inf")):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(ValueError):
                    normalize_drop_rate_options({"normal_drop_multiplier": bad})
        with self.assertRaises(ValueError):
            normalize_drop_rate_options({"drop_everything": 5})

    def test_config_container_invalid_rejects(self):
        for bad in ([], (), "1", True, 1):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(TypeError):
                    normalize_drop_rate_options(bad)
        self.assertEqual(normalize_drop_rate_options({}), {"normal_drop_multiplier": 1})

    def test_input_type_invalid_rejects(self):
        for bad in (None, {}, [], 12, False):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(TypeError):
                    preview_normal_drop_rates(bad)

    def test_default_settings_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            DEFAULT_DROP_RATE_OPTIONS["normal_drop_multiplier"] = 5
        copy = normalize_drop_rate_options()
        copy["normal_drop_multiplier"] = 4
        self.assertEqual(dict(DEFAULT_DROP_RATE_OPTIONS), {"normal_drop_multiplier": 1})

    def test_no_probabilistic_roll_or_item_credit_ever_performed(self):
        view = preview_normal_drop_rates("20:55:1:100")
        self.assertEqual(view["candidates"][0]["hypothetical_rate_percent_model"], 100)
        self.assertFalse(view["rolled"])
        self.assertFalse(view["credited"])
        self.assertNotIn("selected_drop", view)
        self.assertNotIn("payout", view)

    def test_unchanged_wallet_inventory_progress_receipts_and_save(self):
        player = fixture()
        snap = deepcopy(player)
        preview_normal_drop_rates("20:55:1:30,20:101:1:40", {"normal_drop_multiplier": 5})
        self.assertEqual(player, snap)
        self.assertEqual(player["wallet"]["gil"], 300)
        self.assertEqual(player["inventory"]["items"][0]["count"], 1)
        self.assertEqual(player["save"]["dirty"], False)

    def test_config_result_and_snapshot_are_detached_and_pure(self):
        player = fixture()
        before = deepcopy(player)
        policy = {"normal_drop_multiplier": 3}
        original_policy = deepcopy(policy)
        result = preview_normal_drop_rates("20:55:1:20", policy)
        result["candidates"][0]["id"] = 999
        self.assertEqual(player, before)
        self.assertEqual(policy, original_policy)
        self.assertEqual(preview_normal_drop_rates("20:55:1:20", policy)["candidates"][0]["id"], 55)

    def test_deterministic_repeated_source_only_preview(self):
        policy = {"normal_drop_multiplier": 4}
        csv = "20:55:1:30,20:56:2:12,20:57:1:100"
        expected = preview_normal_drop_rates(csv, policy)
        for _ in range(100):
            self.assertEqual(preview_normal_drop_rates(csv, policy), expected)
        self.assertEqual(csv, "20:55:1:30,20:56:2:12,20:57:1:100")
        self.assertEqual(policy, {"normal_drop_multiplier": 4})


if __name__ == "__main__":
    unittest.main()
