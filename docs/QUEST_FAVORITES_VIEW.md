# Quest favorites — ephemeral source-only QoL prototype

Status: **pure source-only preview and optional temporary toggle implemented**.
No original game assets, user save, live catalog, emulator, native hook, server
route, Android navigation, or account state has been accessed or modified.

## Source-backed mission identity

Verified in the permitted `develop` source:

- `source/server/player_state.py::mission_row` retrieves the original
  `F_MISSION_MST.ndjson` entry through `MISSION_KEY`, the native
  `qo3PECw6` mission identifier.
- `source/server/exvius_actions_modes.py::_missions` uses
  `F_MISSION_MST.ndjson`, keyed by `qo3PECw6`, filtering
  `gQR24kST` for mission mode and `U9iHsau3` for dungeon.
- `source/server/ffbe_config.py` identifies
  `MissionEndRequest.jQsE54Iz[0].qo3PECw6` as the same
  original mission-id space.

These fields distinguish mission IDs from daily-quest, area, stage,
and challenge IDs. They do **not** establish that any particular mission
is unlocked, cleared, playable, or presently discoverable by the client.

## Standalone API

`source/server/quest_favorites_view.py` exposes two pure functions:

```python
rows = [
    {"qo3PECw6": "1110100", "gQR24kST": "1", "U9iHsau3": "100"},
    {"qo3PECw6": "1110101", "gQR24kST": "1", "U9iHsau3": "100"},
]

preview = preview_quest_favorites(
    rows,
    ["1110100"],  # temporary caller-provided favorites; not a saved setting
    favorites_only=False,
    favorites_first=True,
    mode=None,
    dungeon=None,
)

new_ephemeral_ids = toggle_ephemeral_favorite(rows, ["1110100"], "1110101")
```

These are **illustrative synthetic catalog rows**, not downloaded master
data. The new functions never read `F_MISSION_MST` themselves.

The preview returns detached records containing the original row
(`entry['mission']`), mission ID, and an `is_favorite` annotation.
The original catalog order is retained by default. The favorites-first
option sorts only by the temporary favorite bit with a stable sort,
preserving original relative order within both groups. Mode/dungeon
filters compare **the actual source tokens**, never inferred completion
or visibility flags. Duplicate favorite IDs are deduplicated with
first-occurrence order; duplicate catalog IDs, unknown bookmarked IDs
and malformed input fail closed.

`toggle_ephemeral_favorite` returns a new list of favorite IDs with a
single mission added or removed. It does not own a global list; the
caller can discard it immediately. Neither function can visit a
mission, start a quest, update unlock switches, or earn rewards.

## CI and safety

`source/exvius/tests/test_quest_favorites_view.py` uses only synthetic
mission rows and a synthetic snapshot of cleared missions, switches,
party, rewards and save dirty flag. It covers the original mission
identifier, invalid/missing IDs, duplicated bookmarks/catalog rows,
mode/dungeon filtering, stable ordering, toggle behavior, detached
nested output, and unchanged progress/rewards/save state.

The source-only workflow executes this test with existing unit,
party, fusion, repeat-reward and syntax checks. Source-only CI is not
evidence that the game has a functional bookmark button.

## Still not implemented

- Native quest-menu favorites or navigation
- Persistent bookmarks across launches
- Confirmed unlock/playability visibility
- Live mission table loading by this helper
- Any gameplay, rewards, save or progression change

The next independent roadmap item is **better reward summaries**, based
strictly on verified completed receipt records and without re-crediting
items. Repeat-stop integration remains on HOLD.
