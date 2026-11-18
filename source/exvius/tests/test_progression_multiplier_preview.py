"""Synthetic tests of read-only EXP/gil earning previews.

No original assets, master tables, real accounts, native execution,
reward payout, PlayerState writes, or save-format changes.
"""
from copy import deepcopy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from progression_multiplier_preview import (
    CHANNELS, DEFAULT_MULTIPLIERS, MAX_PREVIEW_AMOUNT,
    normalize_earning_multipliers, preview_progression_earning,
)


def player_snapshot():
    return {
        "rank": {"level": 25, "exp": 9, "nrg": 80, "last_up": None},
        "roster": [
            {"instance_id": "11", "master_id": "300", "level": 30,
             "exp": 99, "total_exp": 10500}
        ],
        "wallet": {"gil": 3700, "lapis_free": 200},
        "inventory": {"items": [{"item_type": 20, "item_id": 10, "count": 2}]},
        "progress": {"claimed": ["mission1"]},
        "receipts": {"mission:1": {"paid": [{"count": 20}]}},
        "save": {"schema": "v7", "dirty": False},
    }


class ProgressionMultiplierPreviewTests(unittest.TestCase):
    def test_defaults_are_separate_original_1x(self):
        self.assertEqual(CHANNELS, ("rank_exp", "unit_exp", "earned_gil"))
        self.assertEqual(dict(DEFAULT_MULTIPLIERS), {
            "rank_exp": 1, "unit_exp": 1, "earned_gil": 1
        })
        self.assertEqual(normalize_earning_multipliers(), dict(DEFAULT_MULTIPLIERS))
        self.assertEqual(normalize_earning_multipliers({}), dict(DEFAULT_MULTIPLIERS))
        for channel in CHANNELS:
            with self.subTest(channel=channel):
                preview = preview_progression_earning(channel, 170)
                self.assertEqual(preview["multiplier"], 1)
                self.assertEqual(preview["original_amount"], 170)
                self.assertEqual(preview["projected_amount"], 170)
                self.assertEqual(preview["additional_amount"], 0)
                self.assertTrue(preview["preview_only"])
                self.assertFalse(preview["credited"])
                self.assertFalse(preview["source_eligibility_verified"])

    def test_rank_exp_can_preview_3x_independently(self):
        settings = {"rank_exp": 3}
        self.assertEqual(preview_progression_earning("rank_exp", 40, settings)["projected_amount"], 120)
        self.assertEqual(preview_progression_earning("unit_exp", 40, settings)["projected_amount"], 40)
        self.assertEqual(preview_progression_earning("earned_gil", 40, settings)["projected_amount"], 40)

    def test_unit_exp_can_preview_4x_independently(self):
        settings = {"unit_exp": 4}
        preview = preview_progression_earning("unit_exp", 250, settings)
        self.assertEqual((preview["original_amount"], preview["projected_amount"],
                          preview["additional_amount"]), (250, 1000, 750))
        self.assertEqual(preview_progression_earning("rank_exp", 250, settings)["projected_amount"], 250)

    def test_earned_gil_can_preview_2x_independently(self):
        settings = {"earned_gil": 2}
        self.assertEqual(preview_progression_earning("earned_gil", 123, settings)["projected_amount"], 246)
        self.assertEqual(preview_progression_earning("rank_exp", 123, settings)["projected_amount"], 123)
        self.assertEqual(preview_progression_earning("unit_exp", 123, settings)["projected_amount"], 123)

    def test_all_three_settings_can_be_distinct(self):
        settings = {"rank_exp": 2, "unit_exp": 3, "earned_gil": 5}
        self.assertEqual([preview_progression_earning(ch, 10, settings)["projected_amount"]
                          for ch in CHANNELS], [20, 30, 50])
        self.assertEqual(settings, {"rank_exp": 2, "unit_exp": 3, "earned_gil": 5})

    def test_zero_earns_zero_even_at_five_x(self):
        for ch in CHANNELS:
            with self.subTest(channel=ch):
                value = preview_progression_earning(ch, 0, {ch: 5})
                self.assertEqual(value["original_amount"], 0)
                self.assertEqual(value["projected_amount"], 0)
                self.assertEqual(value["additional_amount"], 0)

    def test_negative_or_debit_amounts_are_rejected_never_scaled(self):
        for ch in CHANNELS:
            for negative in (-1, -50, -999999):
                with self.subTest(channel=ch, amount=negative):
                    with self.assertRaisesRegex(ValueError, "nonnegative"):
                        preview_progression_earning(ch, negative, {ch: 5})

    def test_spending_and_lapis_channels_are_not_supported(self):
        for bad in ("gil_spend", "spend_currency", "lapis_free", "lapis_paid",
                    "friend_point", "rank", "total_exp", "normal_drop", "reward"):
            with self.subTest(channel=bad):
                with self.assertRaisesRegex(ValueError, "unsupported earning"):
                    preview_progression_earning(bad, 10)
        with self.assertRaises(ValueError):
            preview_progression_earning(None, 10)

    def test_invalid_multiplier_values_rejected(self):
        for bad in (0, -1, 6, 2.5, True, False, "2", None, [], {}, float("nan")):
            with self.subTest(bad=repr(bad)):
                with self.assertRaisesRegex(ValueError, "integer from 1 to 5"):
                    normalize_earning_multipliers({"earned_gil": bad})
        self.assertEqual(normalize_earning_multipliers({"rank_exp": 5})["rank_exp"], 5)

    def test_unknown_or_invalid_config_container_rejected(self):
        for bad in (None,):  # None is the documented no-settings default.
            self.assertEqual(normalize_earning_multipliers(bad), dict(DEFAULT_MULTIPLIERS))
        for bad in ([], (), 4, "earned_gil", True):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(TypeError):
                    normalize_earning_multipliers(bad)
        with self.assertRaisesRegex(ValueError, "unknown progression"):
            normalize_earning_multipliers({"lapis": 3})
        with self.assertRaisesRegex(ValueError, "unknown progression"):
            normalize_earning_multipliers({"rank_exp": 2, "bonus_exp": 3})

    def test_invalid_earned_amounts_fail_closed(self):
        for bad in (None, True, False, 5.5, "5", [], {}, float("inf"), float("nan")):
            with self.subTest(bad=repr(bad)):
                with self.assertRaisesRegex(ValueError, "nonnegative bounded"):
                    preview_progression_earning("rank_exp", bad)
        with self.assertRaises(ValueError):
            preview_progression_earning("rank_exp", MAX_PREVIEW_AMOUNT + 1)

    def test_safe_ceiling_and_overflow(self):
        self.assertEqual(preview_progression_earning("earned_gil",
                         MAX_PREVIEW_AMOUNT)["projected_amount"], MAX_PREVIEW_AMOUNT)
        with self.assertRaises(OverflowError):
            preview_progression_earning("earned_gil", MAX_PREVIEW_AMOUNT, {"earned_gil": 2})
        self.assertEqual(preview_progression_earning("unit_exp",
                         MAX_PREVIEW_AMOUNT // 5, {"unit_exp": 5})["projected_amount"],
                         (MAX_PREVIEW_AMOUNT // 5) * 5)

    def test_config_is_not_mutated_or_shared(self):
        config = {"rank_exp": 2}
        a = normalize_earning_multipliers(config)
        a["unit_exp"] = 5
        self.assertEqual(config, {"rank_exp": 2})
        self.assertEqual(normalize_earning_multipliers(config), {
            "rank_exp": 2, "unit_exp": 1, "earned_gil": 1
        })
        self.assertEqual(dict(DEFAULT_MULTIPLIERS), {
            "rank_exp": 1, "unit_exp": 1, "earned_gil": 1
        })

    def test_preview_is_a_detached_result(self):
        config = {"rank_exp": 3}
        a = preview_progression_earning("rank_exp", 25, config)
        a["projected_amount"] = 999999
        self.assertEqual(preview_progression_earning("rank_exp", 25, config)["projected_amount"], 75)
        self.assertEqual(config, {"rank_exp": 3})

    def test_all_player_state_and_save_data_unchanged(self):
        player = player_snapshot()
        config = {"rank_exp": 3, "unit_exp": 2, "earned_gil": 5}
        snapshot = deepcopy((player, config))
        for ch in CHANNELS:
            preview_progression_earning(ch, 100, config)
        self.assertEqual((player, config), snapshot)
        self.assertEqual(player["wallet"], {"gil": 3700, "lapis_free": 200})
        self.assertEqual(player["rank"]["exp"], 9)
        self.assertEqual(player["roster"][0]["total_exp"], 10500)
        self.assertEqual(player["save"], {"schema": "v7", "dirty": False})
        self.assertEqual(player["progress"], {"claimed": ["mission1"]})
        self.assertEqual(player["receipts"]["mission:1"]["paid"][0]["count"], 20)

    def test_manual_spending_amounts_not_previewed_or_changed(self):
        state = player_snapshot()
        old = deepcopy(state)
        simulated_cost = -550
        with self.assertRaises(ValueError):
            preview_progression_earning("earned_gil", simulated_cost, {"earned_gil": 5})
        self.assertEqual(state, old)

    def test_pure_deterministic_repeated_calls(self):
        config = {"rank_exp": 2, "unit_exp": 4, "earned_gil": 3}
        expected = [preview_progression_earning(ch, 125, config) for ch in CHANNELS]
        for _ in range(50):
            self.assertEqual([preview_progression_earning(ch, 125, config)
                              for ch in CHANNELS], expected)
        self.assertEqual(config, {"rank_exp": 2, "unit_exp": 4, "earned_gil": 3})

    def test_preview_never_confuses_earning_with_paid_receipt(self):
        result = preview_progression_earning("earned_gil", 75, {"earned_gil": 5})
        self.assertEqual(result["projected_amount"], 375)
        self.assertFalse(result["credited"])
        self.assertFalse(result["source_eligibility_verified"])
        self.assertNotIn("receipt_id", result)
        self.assertNotIn("wallet", result)
        self.assertNotIn("save", result)


if __name__ == "__main__":
    unittest.main()
