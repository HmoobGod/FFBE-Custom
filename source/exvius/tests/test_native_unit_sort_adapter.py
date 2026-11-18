"""Isolated synthetic checks for a pure FFBE native-sort decision policy.

No original client, APK, ELF, saves, player data, native bridge, or runtime
integration is imported or executed by these tests.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from native_unit_sort_adapter import (
    PINNED_ELF_SHA256,
    UNIT_LIST_SCENE,
    NATIVE_LEVEL_LIKE_DESC_MODE,
    NATIVE_LEVEL_LIKE_DESC_PAIR,
    choose_native_unit_sort,
)


def eligible_context():
    return {
        "enabled": True,
        "mode": NATIVE_LEVEL_LIKE_DESC_MODE,
        "elf_sha256": PINNED_ELF_SHA256,
        "scene_name": UNIT_LIST_SCENE,
        "scene_identity_verified": True,
    }


class NativeUnitSortPolicyTests(unittest.TestCase):
    def test_exact_pinned_elf_and_only_allowlisted_pair(self):
        self.assertEqual(
            PINNED_ELF_SHA256,
            "a127654037f2f28a70cce7c64ff0a9d291770ea904cdf5bcba59a7af9a6937e4",
        )
        self.assertEqual(NATIVE_LEVEL_LIKE_DESC_PAIR, (0, 1))
        self.assertEqual(choose_native_unit_sort(**eligible_context()), (0, 1))

    def test_defaults_are_disabled_and_request_no_native_action(self):
        self.assertIsNone(choose_native_unit_sort())
        self.assertIsNone(choose_native_unit_sort(
            mode=NATIVE_LEVEL_LIKE_DESC_MODE,
            elf_sha256=PINNED_ELF_SHA256,
            scene_name=UNIT_LIST_SCENE,
            scene_identity_verified=True,
        ))

    def test_false_enabled_never_selects_any_pair(self):
        data = eligible_context()
        data["enabled"] = False
        self.assertIsNone(choose_native_unit_sort(**data))

    def test_enabled_must_be_literal_true_not_truthy(self):
        for bad in (None, 0, 1, "true", "True", [], [True], {}, object()):
            with self.subTest(enabled=repr(bad)):
                data = eligible_context()
                data["enabled"] = bad
                self.assertIsNone(choose_native_unit_sort(**data))

    def test_scene_attestation_must_be_literal_true(self):
        for bad in (None, False, 0, 1, "true", [], [True], {}):
            with self.subTest(scene_identity_verified=repr(bad)):
                data = eligible_context()
                data["scene_identity_verified"] = bad
                self.assertIsNone(choose_native_unit_sort(**data))

    def test_missing_or_unrecognized_scene_falls_back(self):
        for bad in (None, "", "UnitDetailScene", "UnitListSortFilterSettingScene",
                    "UnitListScene ", "unitlistscene", 0, True, [], {}):
            with self.subTest(scene_name=repr(bad)):
                data = eligible_context()
                data["scene_name"] = bad
                self.assertIsNone(choose_native_unit_sort(**data))

    def test_wrong_or_unverified_fingerprint_falls_back(self):
        for bad in (None, "", "0" * 64,
                    PINNED_ELF_SHA256[:-1] + "0",
                    PINNED_ELF_SHA256.upper(),
                    PINNED_ELF_SHA256 + " ",
                    0, 1, True, [], {}):
            with self.subTest(elf_sha256=repr(bad)):
                data = eligible_context()
                data["elf_sha256"] = bad
                self.assertIsNone(choose_native_unit_sort(**data))

    def test_original_sort_is_not_rewritten_even_when_enabled(self):
        data = eligible_context()
        data["mode"] = "original"
        self.assertIsNone(choose_native_unit_sort(**data))

    def test_favorites_modes_are_never_allowed(self):
        for mode in ("favorites_first", "favorites_level_desc",
                     "favorites_only", "favorite"):
            with self.subTest(mode=mode):
                data = eligible_context()
                data["mode"] = mode
                self.assertIsNone(choose_native_unit_sort(**data))

    def test_plain_level_and_unverified_modes_are_not_native_claims(self):
        for mode in ("level_desc", "level_asc", "native_level_like_asc",
                     "rarity_desc", "native_level_like_desc "):
            with self.subTest(mode=mode):
                data = eligible_context()
                data["mode"] = mode
                self.assertIsNone(choose_native_unit_sort(**data))

    def test_raw_numeric_types_and_untrusted_values_are_never_forwarded(self):
        for mode in ((0, 1), (0, 0), (27, 1), 0, 1, 27, None,
                     True, False, [], {}, object()):
            with self.subTest(mode=repr(mode)):
                data = eligible_context()
                data["mode"] = mode
                self.assertIsNone(choose_native_unit_sort(**data))

    def test_missing_each_attestation_component_fails_closed(self):
        for key in eligible_context():
            with self.subTest(missing=key):
                data = eligible_context()
                data.pop(key)
                self.assertIsNone(choose_native_unit_sort(**data))

    def test_policy_is_repeatable_and_does_not_mutate_its_inputs(self):
        data = eligible_context()
        original = deepcopy(data)
        for _ in range(30):
            self.assertEqual(choose_native_unit_sort(**data), (0, 1))
            self.assertEqual(data, original)

    def test_unrecognized_player_state_arguments_are_not_accepted(self):
        for forbidden in ("roster", "response", "equipment", "party",
                          "favorites", "warehouse", "save", "sort_filter"):
            with self.subTest(forbidden=forbidden):
                data = eligible_context()
                data[forbidden] = {"nested": [1, 2]}
                with self.assertRaises(TypeError):
                    choose_native_unit_sort(**data)

    def test_result_is_immutable_and_not_an_effect(self):
        result = choose_native_unit_sort(**eligible_context())
        self.assertIsInstance(result, tuple)
        with self.assertRaises(TypeError):
            result[0] = 27

    def test_no_assumed_native_level_desc_equivalence(self):
        # Native level-like uses regular Lv + LimitExLvNum; a plain level
        # comparison can disagree and is NOT performed by this adapter.
        synthetic = [
            {"id": "A", "lv": 50, "limit_ex": 0},
            {"id": "B", "lv": 49, "limit_ex": 3},
        ]
        plain_order = sorted(synthetic, key=lambda row: row["lv"], reverse=True)
        native_primary = sorted(
            synthetic, key=lambda row: row["lv"] + row["limit_ex"], reverse=True)
        self.assertEqual([r["id"] for r in plain_order], ["A", "B"])
        self.assertEqual([r["id"] for r in native_primary], ["B", "A"])
        self.assertEqual(choose_native_unit_sort(**eligible_context()), (0, 1))


if __name__ == "__main__":
    unittest.main()
