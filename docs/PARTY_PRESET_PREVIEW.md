# Party presets — read-only source-only prototype

**Status:** Pure party preview and comparison implemented on `develop`.
**Not connected to the original client, saved presets, live party edits, or
an Android menu.** No user save or game build was accessed.

## Actual source-backed fields

- `source/server/ffbe_player.py::apply_party_edit` verifies owned
  `instance_id` values against `State.player.data["roster"]`.
- `party["decks"]` owns existing `id`, `name`, `members`.
  `party["active_deck"]` names an existing deck.
- Member dictionaries use `member_type` (0 or 1),
  `disp_order` (zero-based position), `instance_id` (unique owned unit).
- Normal-party edits allow slots 0–4. Supported special modes
  `7`, `8`, `11` (and `50` alias for `11`) allow slots 0–5.
- This prototype uses the decoded data shape, **not** the obfuscated
  `PartyDeckEditRequest` wire representation. The caller must provide
  the *correct already-selected party snapshot* for that mode; the
  helper deliberately never calls `PlayerState.special_party`,
  which may create state and mark it dirty.

## Prototype entry point

`source/server/party_preset_preview.py::preview_party_preset` accepts:

```python
preview_party_preset(
    roster,    # list of original owned unit mappings, no synthetic unlocks
    party,     # chosen existing party with decks/active_deck
    {"id": 0, "name": "Quest Farming", "members": [
        {"member_type": 0, "disp_order": 0, "instance_id": "101"},
        {"member_type": 0, "disp_order": 1, "instance_id": "102"},
    ]},
    mode="normal",  # or "7", "8", "11", "50" for special 6-slot types
)
```

The function returns **only detached data**:
`before`, `proposed`, `slot_changes`, `name_changed`,
`unchanged`, target/active deck IDs, `preview_only=True`,
`applied=False`, and `manual_gameplay_unchanged=True`.

It refuses unowned units, duplicate instances or occupied slots,
invalid/out-of-range slot positions, unknown deck IDs, invalid
member types, malformed inputs and empty proposed parties. It allows
an empty **existing** deck to be previewed without populating it.
Slot comparisons are stable and order-independent: equal slot
members do not produce false differences when listed in a different
array order.

Inputs and nested output are independent copies. No PlayerState
method, native function, resource file, network call, or save writer
is imported. No original party loadouts, equipment, changes, or
mutations are caused.

## Testing and activation boundaries

- Synthetic tests are in
  `source/exvius/tests/test_party_preset_preview.py`.
- CI executes the isolated test suite with other source-only tests.
- In-game preset selection, applying a new party, renaming saved decks,
  showing a UI, and persisting configurations **remain unimplemented**.
- Original `apply_party_edit`, normal/special-party behavior,
  roster, saves, equipment, combat, manual fallback and original
  rewards are untouched.
- Do not describe a green source-only CI result as device gameplay
  acceptance; any native or save integration requires separate
  validation and authorization.
