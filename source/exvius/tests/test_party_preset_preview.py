"""Synthetic tests for the read-only FFBE party preset comparison helper.

This test module reads NO original client, game data, native library, user
save, or PlayerState runtime singleton. It does not apply/switch decks.
"""
from __future__ import annotations

from copy import deepcopy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from party_preset_preview import preview_party_preset


def member(instance, slot, kind=0):
    return {"member_type": kind, "disp_order": slot, "instance_id": str(instance)}


def example():
    roster = [
        {"instance_id": str(n), "master_id": str(n + 10000),
         "equipment": {"1": str(n + 200)}}
        for n in range(101, 108)
    ]
    party = {
        "active_deck": 0,
        "decks": [
            {"id": 0, "name": "Story", "members": [member(101, 0), member(102, 1)],
             "extra_metadata": ["do not edit"]},
            {"id": 1, "name": "Boss", "members": [member(103, 0)]},
        ],
        "beast_decks": {"0": {0: "owned-beast"}},
    }
    return roster, party


class PartyPresetPreview(unittest.TestCase):
    def test_same_deck_is_noop_and_read_only(self):
        roster, party = example()
        before = deepcopy((roster, party))
        result = preview_party_preset(
            roster, party, {"id": 0, "members": [member(101, 0), member(102, 1)]})
        self.assertTrue(result["preview_only"])
        self.assertFalse(result["applied"])
        self.assertTrue(result["manual_gameplay_unchanged"])
        self.assertTrue(result["unchanged"])
        self.assertEqual(result["slot_changes"], [])
        self.assertEqual(result["active_deck_id"], "0")
        self.assertEqual(result["target_deck_id"], "0")
        self.assertTrue(result["target_is_active"])
        self.assertEqual((roster, party), before)

    def test_comparison_lists_only_changed_slots(self):
        roster, party = example()
        proposal = {"id": 0, "name": "Farming", "members": [
            member(102, 0), member(101, 1), member(104, 2)]}
        result = preview_party_preset(roster, party, proposal)
        self.assertFalse(result["unchanged"])
        self.assertTrue(result["name_changed"])
        self.assertEqual(result["before"]["name"], "Story")
        self.assertEqual(result["proposed"]["name"], "Farming")
        self.assertEqual([v["slot"] for v in result["slot_changes"]], [0, 1, 2])
        self.assertEqual(result["slot_changes"][2]["before"], None)
        self.assertEqual(result["slot_changes"][2]["after"]["instance_id"], "104")
        self.assertEqual(party["decks"][0]["name"], "Story")

    def test_preview_nonactive_deck_does_not_switch(self):
        roster, party = example()
        result = preview_party_preset(roster, party,
            {"id": 1, "name": "Boss New", "members": [member(107, 0)]})
        self.assertFalse(result["target_is_active"])
        self.assertEqual(result["target_deck_id"], "1")
        self.assertEqual(result["active_deck_id"], "0")
        self.assertEqual(party["active_deck"], 0)
        self.assertEqual(party["decks"][1]["name"], "Boss")
        self.assertFalse(result["applied"])

    def test_member_order_does_not_create_false_differences(self):
        roster, party = example()
        result = preview_party_preset(roster, party,
            {"id": "0", "members": [member(102, "1"), member(101, "0")]})
        self.assertTrue(result["unchanged"])
        self.assertEqual(result["slot_changes"], [])

    def test_deep_result_mutations_do_not_modify_input_or_saves(self):
        roster, party = example()
        original = deepcopy((roster, party))
        result = preview_party_preset(roster, party,
            {"id": 0, "members": [member(102, 0), member(107, 3)]})
        result["proposed"]["members"][0]["instance_id"] = "999"
        result["slot_changes"][0]["after"]["instance_id"] = "998"
        result["before"]["name"] = "Modified"
        self.assertEqual((roster, party), original)

    def test_5_slot_normal_limit(self):
        roster, party = example()
        proposal = {"id": 0, "members": [member(101 + n, n) for n in range(6)]}
        with self.assertRaisesRegex(ValueError, "slot limit"):
            preview_party_preset(roster, party, proposal)

    def test_6_slot_special_modes(self):
        roster, party = example()
        proposal = {"id": 0, "members": [member(101 + n, n) for n in range(6)]}
        for mode in ("7", "8", "11", "50"):
            with self.subTest(mode=mode):
                result = preview_party_preset(roster, party, proposal, mode=mode)
                self.assertEqual(result["slot_limit"], 6)
                self.assertEqual(result["proposed"]["members"][-1]["disp_order"], 5)
                self.assertEqual(party["decks"][0]["members"], [member(101, 0), member(102, 1)])

    def test_slots_outside_range_or_duplicated(self):
        roster, party = example()
        for proposed in [
            [member(101, 5)], [member(101, 0), member(102, 0)],
            [member(101, -1)], [member(101, 1.5)],
        ]:
            with self.subTest(proposed=proposed):
                with self.assertRaises(ValueError):
                    preview_party_preset(roster, party, {"id": 0, "members": proposed})

    def test_duplicate_units_even_across_different_slots(self):
        roster, party = example()
        with self.assertRaisesRegex(ValueError, "duplicate unit"):
            preview_party_preset(roster, party,
                {"id": 0, "members": [member(101, 0), member(101, 1)]})

    def test_unowned_unit_rejects_entire_preview_no_partial(self):
        roster, party = example()
        original = deepcopy((roster, party))
        with self.assertRaisesRegex(ValueError, "unowned"):
            preview_party_preset(roster, party,
                {"id": 0, "members": [member(101, 0), member(999, 1)]})
        self.assertEqual((roster, party), original)

    def test_member_type_bounds(self):
        roster, party = example()
        for kind in (-1, 2, "oops", True):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    preview_party_preset(roster, party,
                        {"id": 0, "members": [member(101, 0, kind)]})
        self.assertEqual(preview_party_preset(roster, party,
            {"id": 0, "members": [member(101, 0, 1)]})["proposed"]["members"][0]["member_type"], 1)

    def test_empty_malformed_candidate_rejected(self):
        roster, party = example()
        for proposal in [
            {"id": 0, "members": []},
            {"id": 0, "members": "0:0:101"},
            {"id": 0, "members": [{"member_type": 0, "disp_order": 0}]},
            {"id": 0, "members": [None]},
            {"id": 0, "name": "", "members": [member(101, 0)]},
        ]:
            with self.subTest(proposal=proposal):
                with self.assertRaises(ValueError):
                    preview_party_preset(roster, party, proposal)

    def test_only_existing_deck_ids_and_valid_active_deck(self):
        roster, party = example()
        with self.assertRaisesRegex(ValueError, "not an existing deck"):
            preview_party_preset(roster, party,
                {"id": 99, "members": [member(101, 0)]})
        bad = deepcopy(party)
        bad["active_deck"] = 99
        with self.assertRaisesRegex(ValueError, "active deck does not exist"):
            preview_party_preset(roster, bad, {"id": 0, "members": [member(101, 0)]})
        bad = deepcopy(party)
        bad["decks"].append(deepcopy(bad["decks"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate existing deck"):
            preview_party_preset(roster, bad, {"id": 0, "members": [member(101, 0)]})

    def test_malformed_owned_roster_rejected(self):
        roster, party = example()
        duplicate = deepcopy(roster) + [deepcopy(roster[0])]
        with self.assertRaisesRegex(ValueError, "duplicate instance IDs"):
            preview_party_preset(duplicate, party, {"id": 0, "members": [member(101, 0)]})
        with self.assertRaises(TypeError):
            preview_party_preset([None], party, {"id": 0, "members": [member(101, 0)]})

    def test_invalid_mode_and_party_input_fail_closed(self):
        roster, party = example()
        proposal = {"id": 0, "members": [member(101, 0)]}
        with self.assertRaisesRegex(ValueError, "unsupported party mode"):
            preview_party_preset(roster, party, proposal, mode="unknown")
        with self.assertRaises(TypeError):
            preview_party_preset(roster, None, proposal)
        with self.assertRaises(TypeError):
            preview_party_preset(roster, party, None)

    def test_empty_existing_deck_is_previewable_but_never_saved(self):
        roster, party = example()
        party["decks"][0]["members"] = []
        result = preview_party_preset(roster, party,
            {"id": 0, "members": [member(101, 0)]})
        self.assertEqual(result["before"]["members"], [])
        self.assertEqual(result["slot_changes"][0]["before"], None)
        self.assertEqual(party["decks"][0]["members"], [])

    def test_comparing_is_deterministic_and_not_an_apply_or_save(self):
        roster, party = example()
        snap = deepcopy((roster, party))
        proposal = {"id": 1, "members": [member(104, 0), member(105, 1)]}
        expected = preview_party_preset(roster, party, proposal)
        for _ in range(30):
            self.assertEqual(preview_party_preset(roster, party, proposal), expected)
        self.assertEqual((roster, party), snap)
        self.assertEqual(expected["active_deck_id"], "0")
        self.assertFalse(expected["applied"])


if __name__ == "__main__":
    unittest.main()
