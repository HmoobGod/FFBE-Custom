"""Synthetic, source-only unit roster view regression tests.

No original game assets, master tables, saved games, network, or native UI.
Only the standalone unit_roster_view module is imported.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from unit_roster_view import select_roster_view


def fixture():
    return [
        {"instance_id": "A", "master_id": "100", "level": 10,
         "favourite": 0, "storage_state": 0, "equip": {"slots": [7]}},
        {"instance_id": "B", "master_id": "200", "level": 50,
         "favourite": 1, "storage_state": 1},
        {"instance_id": "C", "master_id": "300", "level": "50",
         "favourite": "1", "storage_state": 0},
        {"instance_id": "D", "master_id": "400", "level": 1,
         "favourite": 0, "storage_state": "1"},
        {"instance_id": "E", "master_id": "500", "level": 50,
         "favourite": 0, "storage_state": 0},
    ]


def ids(rows):
    return [row["instance_id"] for row in rows]


class UnitRosterView(unittest.TestCase):
    def test_defaults_preserve_every_unit_and_exact_order(self):
        roster = fixture()
        result = select_roster_view(roster)
        self.assertEqual(result, roster)
        self.assertEqual(ids(result), ["A", "B", "C", "D", "E"])
        self.assertIsNot(result, roster)
        for source, copied in zip(roster, result):
            self.assertIsNot(source, copied)

    def test_defensive_nested_copy_does_not_modify_save_state(self):
        roster = fixture()
        before = copy.deepcopy(roster)
        preview = select_roster_view(roster)
        preview[0]["equip"]["slots"][0] = 999
        preview[0]["favourite"] = 1
        preview.pop()
        self.assertEqual(roster, before)

    def test_favorites_first_stable(self):
        self.assertEqual(ids(select_roster_view(fixture(), sort="favorites_first")),
                         ["B", "C", "A", "D", "E"])

    def test_levels_ascending_stable(self):
        self.assertEqual(ids(select_roster_view(fixture(), sort="level_asc")),
                         ["D", "A", "B", "C", "E"])

    def test_levels_descending_stable(self):
        self.assertEqual(ids(select_roster_view(fixture(), sort="level_desc")),
                         ["B", "C", "E", "A", "D"])

    def test_favorites_then_level_descending_stable(self):
        self.assertEqual(ids(select_roster_view(fixture(), sort="favorites_level_desc")),
                         ["B", "C", "E", "A", "D"])

    def test_warehouse_only_does_not_move_or_unequip(self):
        roster = fixture()
        before = copy.deepcopy(roster)
        self.assertEqual(ids(select_roster_view(roster, storage="warehouse")),
                         ["B", "D"])
        self.assertEqual(roster, before)

    def test_active_only(self):
        self.assertEqual(ids(select_roster_view(fixture(), storage="active")),
                         ["A", "C", "E"])

    def test_favorites_only_and_combination(self):
        self.assertEqual(ids(select_roster_view(fixture(), favorites_only=True)),
                         ["B", "C"])
        self.assertEqual(ids(select_roster_view(fixture(), favorites_only=True,
                                                storage="active")),
                         ["C"])
        self.assertEqual(ids(select_roster_view(fixture(), favorites_only=True,
                                                storage="warehouse")),
                         ["B"])

    def test_empty_roster_and_tuple_input(self):
        self.assertEqual(select_roster_view([]), [])
        self.assertEqual(ids(select_roster_view(tuple(fixture()))),
                         ["A", "B", "C", "D", "E"])

    def test_missing_optional_fields_preserve_original_view(self):
        rows = [{"instance_id": "X", "master_id": "7"}]
        self.assertEqual(select_roster_view(rows), rows)
        self.assertEqual(select_roster_view(rows, favorites_only=True), [])
        self.assertEqual(ids(select_roster_view(rows, storage="active")), ["X"])

    def test_fail_invalid_options(self):
        rows = fixture()
        with self.assertRaises(ValueError):
            select_roster_view(rows, sort="rarity_desc")
        with self.assertRaises(ValueError):
            select_roster_view(rows, storage="hidden")
        for bad in (None, 1, "true", [], {}):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(TypeError):
                    select_roster_view(rows, favorites_only=bad)

    def test_fail_invalid_row_structure(self):
        for bad in (None, {}, "rows", 1):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(TypeError):
                    select_roster_view(bad)
        with self.assertRaises(TypeError):
            select_roster_view([{} , 12])

    def test_only_validate_fields_needed_by_active_view(self):
        rows = [{"instance_id": "X", "level": "?", "favourite": 77,
                 "storage_state": 8}]
        self.assertEqual(select_roster_view(rows), rows)
        with self.assertRaises(ValueError):
            select_roster_view(rows, sort="level_desc")
        with self.assertRaises(ValueError):
            select_roster_view(rows, sort="favorites_first")
        with self.assertRaises(ValueError):
            select_roster_view(rows, favorites_only=True)
        with self.assertRaises(ValueError):
            select_roster_view(rows, storage="warehouse")

    def test_pure_repeated_calls(self):
        roster = fixture()
        before = copy.deepcopy(roster)
        first = select_roster_view(roster, sort="favorites_level_desc",
                                   storage="active")
        for _ in range(20):
            self.assertEqual(select_roster_view(roster, sort="favorites_level_desc",
                                                storage="active"), first)
        self.assertEqual(roster, before)


if __name__ == "__main__":
    unittest.main()
