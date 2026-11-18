"""Synthetic source-only tests for transient quest favorite previews.

No original F_MISSION_MST data files, account saves, native UI, network,
quest completions, reward transactions, or gameplay entry points.
"""
from __future__ import annotations

from copy import deepcopy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from quest_favorites_view import preview_quest_favorites, toggle_ephemeral_favorite


def state_fixture():
    return {
        "missions": [
            {"qo3PECw6": "1110100", "gQR24kST": "1", "U9iHsau3": "100",
             "nested": {"original": [1, 2]}},
            {"qo3PECw6": "1110101", "gQR24kST": "1", "U9iHsau3": "100"},
            {"qo3PECw6": "8991106", "gQR24kST": "50", "U9iHsau3": "900"},
            {"qo3PECw6": "1110102", "gQR24kST": "1", "U9iHsau3": "101"},
            {"qo3PECw6": "8991107", "gQR24kST": "50", "U9iHsau3": "900"},
        ],
        "mission_progress": {"cleared": ["1110100"], "switches": {"10002200": True}},
        "party": {"active_deck": 0},
        "rewards": {"gil": 500, "lapis": 12},
        "player_save": {"version": 7, "dirty": False},
    }


def shown(preview):
    return [entry["mission_id"] for entry in preview["entries"]]


class QuestFavoritesViewTests(unittest.TestCase):
    def test_defaults_show_catalog_order_without_bookmarking(self):
        state = state_fixture()
        snap = deepcopy(state)
        result = preview_quest_favorites(state["missions"])
        self.assertEqual(shown(result),
                         ["1110100", "1110101", "8991106", "1110102", "8991107"])
        self.assertEqual(result["favorite_ids"], [])
        self.assertEqual(result["visible_count"], 5)
        self.assertEqual(result["visible_favorites"], 0)
        self.assertTrue(result["preview_only"])
        self.assertFalse(result["persisted"])
        self.assertFalse(result["navigation_performed"])
        self.assertEqual(state, snap)

    def test_favorites_annotate_in_original_catalog_order(self):
        state = state_fixture()
        view = preview_quest_favorites(
            state["missions"], ["8991106", "1110100"])
        self.assertEqual(shown(view),
                         ["1110100", "1110101", "8991106", "1110102", "8991107"])
        self.assertEqual([entry["is_favorite"] for entry in view["entries"]],
                         [True, False, True, False, False])
        self.assertEqual(view["favorite_ids"], ["8991106", "1110100"])
        self.assertEqual(view["visible_favorites"], 2)

    def test_favorites_first_preserves_relative_catalog_order(self):
        state = state_fixture()
        view = preview_quest_favorites(
            state["missions"], ["8991107", "1110101", "8991106"],
            favorites_first=True)
        self.assertEqual(shown(view),
                         ["1110101", "8991106", "8991107", "1110100", "1110102"])

    def test_favorites_only_retains_catalog_order(self):
        state = state_fixture()
        view = preview_quest_favorites(
            state["missions"], ["8991107", "1110100", "8991106"],
            favorites_only=True)
        self.assertEqual(shown(view), ["1110100", "8991106", "8991107"])
        self.assertEqual(view["visible_count"], 3)
        self.assertEqual(view["visible_favorites"], 3)

    def test_duplicate_favorites_deduplicated_without_duplicate_cards(self):
        state = state_fixture()
        view = preview_quest_favorites(state["missions"],
                                        ["1110101", "1110101", "8991107", "1110101"])
        self.assertEqual(view["favorite_ids"], ["1110101", "8991107"])
        self.assertEqual(view["visible_count"], 5)
        self.assertEqual(view["visible_favorites"], 2)
        self.assertEqual(len(set(shown(view))), 5)

    def test_mode_filter_uses_original_catalog_field(self):
        state = state_fixture()
        result = preview_quest_favorites(
            state["missions"], ["1110100", "8991107"],
            mode="50", favorites_first=True)
        self.assertEqual(shown(result), ["8991107", "8991106"])
        self.assertEqual(result["visible_favorites"], 1)

    def test_dungeon_filter_uses_original_catalog_field(self):
        state = state_fixture()
        result = preview_quest_favorites(
            state["missions"], ["1110100", "1110101", "8991107"],
            dungeon="100", favorites_only=True)
        self.assertEqual(shown(result), ["1110100", "1110101"])

    def test_combined_mode_and_dungeon_filters(self):
        state = state_fixture()
        result = preview_quest_favorites(state["missions"], ["8991106"],
                                         mode=50, dungeon=900)
        self.assertEqual(shown(result), ["8991106", "8991107"])

    def test_filters_never_claim_mission_is_unlocked(self):
        state = state_fixture()
        view = preview_quest_favorites(state["missions"], ["8991106"], mode="50")
        self.assertNotIn("unlocked", view["entries"][0])
        self.assertNotIn("cleared", view["entries"][0])
        self.assertFalse(view["navigation_performed"])

    def test_toggle_add_remove_only_returns_ephemeral_ids(self):
        state = state_fixture()
        before = deepcopy(state)
        initial = ["1110100"]
        added = toggle_ephemeral_favorite(
            state["missions"], initial, "8991106")
        self.assertEqual(added, ["1110100", "8991106"])
        removed = toggle_ephemeral_favorite(
            state["missions"], added, "1110100")
        self.assertEqual(removed, ["8991106"])
        self.assertEqual(initial, ["1110100"])
        self.assertEqual(state, before)

    def test_toggle_deduplicates_existing_selection(self):
        state = state_fixture()
        self.assertEqual(toggle_ephemeral_favorite(
            state["missions"], ["1110101", "1110101"], "8991107"),
            ["1110101", "8991107"])
        self.assertEqual(toggle_ephemeral_favorite(
            state["missions"], ["1110101", "1110101"], "1110101"), [])

    def test_reject_unknown_favorites_and_toggle_targets(self):
        state = state_fixture()
        original = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "outside the catalog"):
            preview_quest_favorites(state["missions"], ["9999999"])
        with self.assertRaisesRegex(ValueError, "unknown mission"):
            toggle_ephemeral_favorite(state["missions"], [], "9999999")
        self.assertEqual(state, original)

    def test_reject_duplicate_catalog_ids_and_malformed_catalog_rows(self):
        state = state_fixture()
        with self.assertRaisesRegex(ValueError, "duplicate mission"):
            preview_quest_favorites(state["missions"] + [deepcopy(state["missions"][0])])
        for rows in (None, {}, "missions", [None], [123]):
            with self.subTest(rows=repr(rows)):
                with self.assertRaises(TypeError):
                    preview_quest_favorites(rows)
        for rows in ([{}], [{"qo3PECw6": "not-an-id"}],
                     [{"qo3PECw6": "0"}]):
            with self.subTest(rows=repr(rows)):
                with self.assertRaises(ValueError):
                    preview_quest_favorites(rows)

    def test_reject_invalid_bookmark_ids_and_types(self):
        state = state_fixture()
        for selection in (None, "1110100", 1, {}):
            with self.subTest(selection=repr(selection)):
                with self.assertRaises(TypeError):
                    preview_quest_favorites(state["missions"], selection)
        for mid in (None, "", "unknown", "-1", 3.5, True, [], "111 0100", "0"):
            with self.subTest(mid=repr(mid)):
                with self.assertRaises(ValueError):
                    preview_quest_favorites(state["missions"], [mid])

    def test_reject_invalid_filter_values_and_switch_types(self):
        state = state_fixture()
        for bad in ("NaN", -1, True, {}, []):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(ValueError):
                    preview_quest_favorites(state["missions"], mode=bad)
        for flag in (None, 1, "yes", [], {}):
            with self.subTest(flag=repr(flag)):
                with self.assertRaises(TypeError):
                    preview_quest_favorites(state["missions"], favorites_first=flag)

    def test_missing_filter_field_does_not_make_up_a_match(self):
        rows = [{"qo3PECw6": "2000"}, {"qo3PECw6": "3000", "gQR24kST": "50"}]
        self.assertEqual(shown(preview_quest_favorites(rows, mode="50")), ["3000"])
        self.assertEqual(shown(preview_quest_favorites(rows, dungeon="10")), [])

    def test_empty_catalog_is_legitimate_when_favorites_empty(self):
        view = preview_quest_favorites([], [], favorites_only=True)
        self.assertEqual(view["entries"], [])
        self.assertEqual(view["visible_favorites"], 0)

    def test_nested_output_mutation_never_changes_missions_or_progress(self):
        state = state_fixture()
        snap = deepcopy(state)
        view = preview_quest_favorites(state["missions"], ["1110100"])
        view["entries"][0]["mission"]["nested"]["original"].append(999)
        view["entries"][0]["mission_id"] = "999"
        view["favorite_ids"].append("8991107")
        self.assertEqual(state, snap)

    def test_deterministic_calls_do_not_change_saves_or_mission_progress(self):
        state = state_fixture()
        before = deepcopy(state)
        selections = ["8991106", "1110100"]
        view = preview_quest_favorites(
            state["missions"], selections, favorites_first=True, dungeon="900")
        for _ in range(30):
            self.assertEqual(preview_quest_favorites(
                state["missions"], selections, favorites_first=True,
                dungeon="900"), view)
        self.assertEqual(state, before)
        self.assertEqual(selections, ["8991106", "1110100"])
        self.assertEqual(state["player_save"]["dirty"], False)
        self.assertEqual(state["mission_progress"]["cleared"], ["1110100"])


if __name__ == "__main__":
    unittest.main()
