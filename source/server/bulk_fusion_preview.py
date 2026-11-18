"""Read-only, source-only bulk fusion/material selection preview.

This mirrors the structural input guards in ffbe_player.serve_unit_mix:
one or more bases, nonempty material lists, no reused base/donor,
no duplicate materials, no base also used as a donor, and all units owned.

It does NOT call PlayerState.mix_units, consume units, compute EXP/trust
rewards, modify a receipt, or submit a native request. Source-only
structural validity does not imply a fusion is executable: the original
engine also checks master data, affinity, special bonuses, reward
capacity, party membership, and runtime state.
"""
from __future__ import annotations

from copy import deepcopy


def _instance_id(value, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{label}: expected a decimal unit instance ID")
    text = str(value)
    if not text or not text.isascii() or not text.isdecimal():
        raise ValueError(f"{label}: expected a decimal unit instance ID")
    return text


def preview_bulk_fusion(roster, selections):
    """Return a detached, all-or-nothing fusion selection preview.

    Input is a decoded selection list, not a native UnitMixRequest:
    [{"base_id": "101", "material_ids": ["201", "202"]}, ...].
    Input ordering and material ordering are preserved. Every referenced
    unit must already occur in the supplied roster. Even a valid preview
    always reports executable=False; runtime eligibility is NOT proven.
    """
    if not isinstance(roster, (list, tuple)) or any(
        not isinstance(unit, dict) for unit in roster
    ):
        raise TypeError("roster must be a list of owned unit mappings")
    if not isinstance(selections, (list, tuple)) or not selections:
        raise ValueError("selections must be a nonempty batch")

    owned = {}
    for unit in roster:
        iid = _instance_id(unit.get("instance_id"), "roster instance_id")
        if iid in owned:
            raise ValueError("duplicate owned unit instance ID")
        owned[iid] = unit

    bases = set()
    donors = set()
    operations = []
    for selection in selections:
        if not isinstance(selection, dict):
            raise ValueError("each selection must be a mapping")
        base = _instance_id(selection.get("base_id"), "base_id")
        materials = selection.get("material_ids")
        if not isinstance(materials, (list, tuple)) or not materials:
            raise ValueError("each base must have nonempty material_ids")
        material_ids = [
            _instance_id(iid, "material_id") for iid in materials
        ]
        if len(set(material_ids)) != len(material_ids):
            raise ValueError("duplicate donor in one selection")
        if base in bases:
            raise ValueError("duplicate base across selections")
        if any(iid in donors for iid in material_ids):
            raise ValueError("donor reused across selections")
        if base in material_ids:
            raise ValueError("base cannot be its own donor")
        if base not in owned or any(iid not in owned for iid in material_ids):
            raise ValueError("selection references an unowned unit instance ID")
        bases.add(base)
        donors.update(material_ids)
        operations.append({
            "base_id": base,
            "base_master_id": deepcopy(owned[base].get("master_id")),
            "material_ids": list(material_ids),
            "material_master_ids": [
                deepcopy(owned[iid].get("master_id")) for iid in material_ids
            ],
            "donor_count": len(material_ids),
        })

    if bases.intersection(donors):
        raise ValueError("a unit cannot be a base and a donor in one batch")

    return deepcopy({
        "preview_only": True,
        "executed": False,
        "executable": False,
        "requires_runtime_validation": True,
        "base_count": len(operations),
        "donor_count": len(donors),
        "operations": operations,
    })
