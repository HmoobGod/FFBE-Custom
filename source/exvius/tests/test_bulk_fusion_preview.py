"""Synthetic source-only tests for bulk fusion selection previews.

No game data, native executable, PlayerState runtime, network, transactions,
save writes or original asset files are accessed.
"""
from __future__ import annotations

from copy import deepcopy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server"))
from bulk_fusion_preview import preview_bulk_fusion


def snapshot():
    return {
        "roster": [
            {"instance_id": "101", "master_id": "9001", "level": 40,
             "equipment": {"1": "sword"}},
            {"instance_id": "102", "master_id": "9002", "level": 20},
            {"instance_id": "201", "master_id": "9101", "level": 2},
            {"instance_id": "202", "master_id": "9101", "level": 4},
            {"instance_id": "203", "master_id": "9102", "level": 5},
            {"instance_id": "204", "master_id": "9103", "level": 1},
        ],
        "party": {
            "active_deck": 0,
            "decks": [{"id": 0, "members": [
                {"member_type": 0, "disp_order": 0, "instance_id": "101"}]}],
        },
        "inventory": {"items": {"22": 10}},
        "wallet": {"gil": 123456, "lapis_free": 200},
        "exvius_unit_mix": {"prior_receipt": {"result": "unchanged"}},
        "dirty": False,
    }


def selection(base, *donors):
    return {"base_id": base, "material_ids": list(donors)}


class BulkFusionPreview(unittest.TestCase):
    def test_single_base_selection_is_read_only_and_not_executable(self):
        state = snapshot()
        before = deepcopy(state)
        preview = preview_bulk_fusion(state["roster"], [selection("101", "201", "202")])
        self.assertTrue(preview["preview_only"])
        self.assertFalse(preview["executed"])
        self.assertFalse(preview["executable"])
        self.assertTrue(preview["requires_runtime_validation"])
        self.assertEqual(preview["base_count"], 1)
        self.assertEqual(preview["donor_count"], 2)
        self.assertEqual(preview["operations"][0]["base_id"], "101")
        self.assertEqual(preview["operations"][0]["base_master_id"], "9001")
        self.assertEqual(preview["operations"][0]["material_ids"], ["201", "202"])
        self.assertEqual(preview["operations"][0]["material_master_ids"], ["9101", "9101"])
        self.assertEqual(state, before)

    def test_multiple_bases_preserve_selection_order_and_material_order(self):
        state = snapshot()
        preview = preview_bulk_fusion(state["roster"], [
            selection("102", "203"),
            selection("101", "202", "201"),
        ])
        self.assertEqual(preview["base_count"], 2)
        self.assertEqual(preview["donor_count"], 3)
        self.assertEqual([x["base_id"] for x in preview["operations"]], ["102", "101"])
        self.assertEqual(preview["operations"][1]["material_ids"], ["202", "201"])

    def test_same_master_ids_are_not_duplicate_instances(self):
        state = snapshot()
        preview = preview_bulk_fusion(state["roster"], [selection("101", "201", "202")])
        self.assertEqual(preview["donor_count"], 2)
        self.assertFalse(preview["executable"])

    def test_duplicate_donor_within_one_base_rejected(self):
        state = snapshot()
        with self.assertRaisesRegex(ValueError, "duplicate donor"):
            preview_bulk_fusion(state["roster"], [selection("101", "201", "201")])

    def test_reused_donor_across_bases_rejected(self):
        state = snapshot()
        with self.assertRaisesRegex(ValueError, "donor reused"):
            preview_bulk_fusion(state["roster"], [
                selection("101", "201"), selection("102", "201")])

    def test_duplicate_base_across_operations_rejected(self):
        state = snapshot()
        with self.assertRaisesRegex(ValueError, "duplicate base"):
            preview_bulk_fusion(state["roster"], [
                selection("101", "201"), selection("101", "202")])

    def test_self_donor_rejected(self):
        state = snapshot()
        with self.assertRaisesRegex(ValueError, "own donor"):
            preview_bulk_fusion(state["roster"], [selection("101", "101")])

    def test_cross_batch_base_donor_conflicts_rejected_both_orders(self):
        state = snapshot()
        for operations in (
            [selection("101", "201"), selection("201", "202")],
            [selection("201", "202"), selection("101", "201")],
        ):
            with self.subTest(operations=operations):
                with self.assertRaisesRegex(ValueError, "base and a donor"):
                    preview_bulk_fusion(state["roster"], operations)

    def test_unowned_donor_refuses_entire_batch_no_partial_state_change(self):
        state = snapshot()
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "unowned"):
            preview_bulk_fusion(state["roster"], [
                selection("101", "201"), selection("102", "999")])
        self.assertEqual(state, before)

    def test_unowned_base_rejected(self):
        state = snapshot()
        with self.assertRaisesRegex(ValueError, "unowned"):
            preview_bulk_fusion(state["roster"], [selection("999", "201")])

    def test_empty_batch_or_empty_materials_rejected(self):
        state = snapshot()
        for operations in ([], (), None, "101:201", {}):
            with self.subTest(operations=operations):
                with self.assertRaises(ValueError):
                    preview_bulk_fusion(state["roster"], operations)
        with self.assertRaisesRegex(ValueError, "nonempty material_ids"):
            preview_bulk_fusion(state["roster"], [selection("101")])

    def test_bad_selection_shape_and_material_ids_rejected(self):
        state = snapshot()
        for operations in ([None], [123], [{"base_id": "101", "material_ids": "201"}],
                           [{"base_id": "101"}], [{"material_ids": ["201"]}]):
            with self.subTest(operations=operations):
                with self.assertRaises(ValueError):
                    preview_bulk_fusion(state["roster"], operations)

    def test_malformed_instances_rejected_without_guessing(self):
        state = snapshot()
        for invalid in (None, "", "unknown", "-1", "1:2", True, -1, 1.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    preview_bulk_fusion(state["roster"], [selection("101", invalid)])
        with self.assertRaises(ValueError):
            preview_bulk_fusion(state["roster"], [selection(True, "201")])

    def test_duplicate_roster_identity_rejected(self):
        state = snapshot()
        double = state["roster"] + [deepcopy(state["roster"][0])]
        with self.assertRaisesRegex(ValueError, "duplicate owned"):
            preview_bulk_fusion(double, [selection("101", "201")])

    def test_invalid_roster_fails_closed(self):
        for roster in (None, {}, "roster", [{"instance_id": "101"}, None]):
            with self.subTest(roster=roster):
                with self.assertRaises(TypeError):
                    preview_bulk_fusion(roster, [selection("101", "201")])
        with self.assertRaises(ValueError):
            preview_bulk_fusion([{"instance_id": "bad"}], [selection("101", "201")])

    def test_output_is_fully_detached_and_deterministic(self):
        state = snapshot()
        ops = [selection("101", "201", "202"), selection("102", "203")]
        before = deepcopy((state, ops))
        preview = preview_bulk_fusion(state["roster"], ops)
        for _ in range(15):
            self.assertEqual(preview_bulk_fusion(state["roster"], ops), preview)
        preview["operations"][0]["material_ids"][0] = "999"
        preview["operations"][0]["base_master_id"] = "changed"
        preview["operations"].pop()
        self.assertEqual((state, ops), before)

    def test_structural_validity_never_claims_full_fusion_eligibility(self):
        state = snapshot()
        # The original runtime would apply additional player-state, party,
        # affinity, trust reward, and master-data checks. This helper never
        # pronounces the proposed irreversible operation executable.
        for ops in ([selection("101", "201")],
                    [selection("102", "204"), selection("101", "202")]):
            preview = preview_bulk_fusion(state["roster"], ops)
            self.assertFalse(preview["executable"])
            self.assertTrue(preview["requires_runtime_validation"])
            self.assertEqual(state["wallet"]["gil"], 123456)
            self.assertEqual(state["inventory"]["items"]["22"], 10)
            self.assertFalse(state["dirty"])
            self.assertEqual(state["exvius_unit_mix"],
                             {"prior_receipt": {"result": "unchanged"}})


if __name__ == "__main__":
    unittest.main()
