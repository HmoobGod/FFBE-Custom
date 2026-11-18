"""Pure, read-only party preset preview for FFBE-Custom.

Uses the exact decoded PlayerState deck/member fields validated by
ffbe_player.apply_party_edit: party['decks'], party['active_deck'],
deck['id'/'name'/'members'], and each member's member_type, disp_order,
instance_id. A caller passes the selected party snapshot explicitly.
This function never calls PlayerState.special_party (which can mutate it),
writes a save, edits a deck, switches the active deck, or touches native UI.

Not a verified in-game UI feature. All inputs in tests are synthetic.
"""
from __future__ import annotations

from copy import deepcopy


PARTY_SLOTS = {"normal": 5, "7": 6, "8": 6, "11": 6, "50": 6}


def _id(value, label: str) -> str:
    """Keep original instance/deck identity as decimal text, not int."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{label} must be a decimal ID")
    result = str(value)
    if not result or not result.isascii() or not result.isdecimal():
        raise ValueError(f"{label} must be a decimal ID")
    return result


def _number(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{label} must be a nonnegative integer")
    result = str(value)
    if not result or not result.isascii() or not result.isdecimal():
        raise ValueError(f"{label} must be a nonnegative integer")
    return int(result)


def _members(raw, known: set[str], slots: int, *, allow_empty=False):
    if not isinstance(raw, (list, tuple)):
        raise ValueError("members must be a list")
    if not allow_empty and not raw:
        raise ValueError("a proposed party cannot be empty")
    if len(raw) > slots:
        raise ValueError("party exceeds its native slot limit")
    seen_slots: set[int] = set()
    seen_instances: set[str] = set()
    normalized: list[dict] = []
    for member in raw:
        if not isinstance(member, dict):
            raise ValueError("every member must be a mapping")
        kind = _number(member.get("member_type"), "member_type")
        order = _number(member.get("disp_order"), "disp_order")
        iid = _id(member.get("instance_id"), "instance_id")
        if kind not in (0, 1):
            raise ValueError("member_type must be 0 or 1")
        if order >= slots or order in seen_slots:
            raise ValueError("invalid or duplicate party slot")
        if iid in seen_instances:
            raise ValueError("duplicate unit instance ID")
        if iid not in known:
            raise ValueError("party contains an unowned unit instance ID")
        seen_slots.add(order)
        seen_instances.add(iid)
        normalized.append({
            "member_type": kind,
            "disp_order": order,
            "instance_id": iid,
        })
    return sorted(normalized, key=lambda member: member["disp_order"])


def preview_party_preset(roster, party, preset, *, mode="normal"):
    """Compare an owned, existing deck to a proposed arrangement.

    Raises ValueError/TypeError on unsafe or ambiguous inputs. Returns a
    completely detached *preview*, never a modified party or save object.
    The optional preset name previews a rename but does not persist it.
    Only normal 5-slot and source-recognized special 6-slot modes are known.
    """
    if mode not in PARTY_SLOTS:
        raise ValueError("unsupported party mode")
    if not isinstance(roster, (list, tuple)) or any(
        not isinstance(unit, dict) for unit in roster
    ):
        raise TypeError("roster must contain owned unit mappings")
    if not isinstance(party, dict) or not isinstance(preset, dict):
        raise TypeError("party and preset must be mappings")
    raw_decks = party.get("decks")
    if not isinstance(raw_decks, list):
        raise ValueError("party must contain its existing decks")

    known: set[str] = set()
    for unit in roster:
        instance = _id(unit.get("instance_id"), "owned instance_id")
        if instance in known:
            raise ValueError("roster contains duplicate instance IDs")
        known.add(instance)

    decks = {}
    for deck in raw_decks:
        if not isinstance(deck, dict):
            raise ValueError("invalid existing deck")
        did = _id(deck.get("id"), "deck id")
        if did in decks:
            raise ValueError("duplicate existing deck id")
        decks[did] = deck
    active_id = _id(party.get("active_deck"), "active deck id")
    if active_id not in decks:
        raise ValueError("active deck does not exist")

    target_id = _id(preset.get("id"), "preset deck id")
    if target_id not in decks:
        raise ValueError("preset target deck is not an existing deck")
    before = decks[target_id]
    if not isinstance(before.get("name"), str):
        raise ValueError("existing deck name must be text")

    slots = PARTY_SLOTS[mode]
    current_members = _members(before.get("members"), known, slots, allow_empty=True)
    proposed_members = _members(preset.get("members"), known, slots)
    old_name = before["name"]
    new_name = preset.get("name", old_name)
    if not isinstance(new_name, str) or not new_name:
        raise ValueError("preset name must be non-empty text")

    current_slots = {m["disp_order"]: m for m in current_members}
    new_slots = {m["disp_order"]: m for m in proposed_members}
    changes = [
        {"slot": slot, "before": deepcopy(current_slots.get(slot)),
         "after": deepcopy(new_slots.get(slot))}
        for slot in range(slots)
        if current_slots.get(slot) != new_slots.get(slot)
    ]

    return deepcopy({
        "preview_only": True,
        "applied": False,
        "manual_gameplay_unchanged": True,
        "mode": mode,
        "slot_limit": slots,
        "target_deck_id": target_id,
        "active_deck_id": active_id,
        "target_is_active": target_id == active_id,
        "before": {"name": old_name, "members": current_members},
        "proposed": {"name": new_name, "members": proposed_members},
        "slot_changes": changes,
        "name_changed": old_name != new_name,
        "unchanged": not changes and old_name == new_name,
    })
