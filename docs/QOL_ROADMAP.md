# FFBE-Custom — 12-feature QoL implementation roadmap

Research checkpoint: 2026-11-18.
Scope: PUBLIC `HmoobGod/FFBE-Custom` source-only checkout, based on
Elvlin's permissioned, filtered upstream source at `upstream-source`
`f567ba6ab2e4e5c7c064ad0d0abf3c9c4de0df2d`.
This order is by **safe implementability and dependency**, not the user's
relative preference for each feature. No Android build or original game
content is present. No item below is declared playable until tested in an
authorized runtime.

## Implement first — source-only prototypes, no gameplay wiring

1. **Advanced unit sorting** — **first implementation committed**:
   `source/server/unit_roster_view.py` provides an isolated,
   nonmutating preview for original order, level ascending/descending,
   favorites-first and favorites/level, plus favorites-only and
   warehouse/active filters. Uses only original PlayerState row fields
   `instance_id`, `level`, `favourite`, `storage_state`
   (`player_state.py::set_favourites`, `set_storage`, `_unit_rows`).
   `test_unit_roster_view.py` uses synthetic roster data. **NOT a native
   game screen**, not connected to real saves or client wire replies.
   Client in-game sorting requires separate UI verification.
2. **Party presets — source-only preview IMPLEMENTED**:
   `source/server/party_preset_preview.py` compares owned-unit instance IDs,
   member types, unique slot positions, names, and existing target deck IDs
   using the exact decoded PlayerState member/deck fields validated by
   `ffbe_player.py::apply_party_edit`. Normal parties have 5 slots;
   supported special modes have 6. `test_party_preset_preview.py`
   exercises synthetic comparison, invalid ownership, duplicate
   instances/slots, unsupported modes, no save mutations, and no
   automatic active-deck switching. **No native UI or live save writes.**
   Applying/saving presets remains blocked pending separate UI,
   ownership, and save-compatibility evidence.
3. **Bulk unit management — preview only**:
   `ffbe_player.py::serve_unit_mix` already validates base/donor
   uniqueness and uses a durable hash receipt. Safe next scope:
   simulate and review candidate sets, preserving all actual fusion,
   sell, favorite, storage, spending and rollback logic unchanged.
4. **Quest favorites**: separate local, ephemeral list of confirmed
   mission IDs; never mark mission completion or modify progress.
   Existing mission IDs appear in `exvius_actions_modes.py` and
   `F_MISSION_MST` references. UX/native navigation and durable
   storage format are not independently verified.
5. **Better reward summaries**: read-only formatting/aggregation of
   **verified** per-attempt credit receipts. Existing ledger:
   `exvius_repeat.py::complete_attempt`, `claim_mission_rewards`,
   `repeat_challenge_rewards`. It records challenge rewards
   separately from normal drops. Cannot yet claim a complete
   multi-run payout report from client constructor counts.

## Develop after receipt and eligible-source rules are verified

6. **Adjustable EXP and gil**: pure opt-in pre-credit multiplier
   design with original 1x defaults, separately for rank EXP,
   unit EXP, and positive *earned* gil. Existing
   `player_state.py::{add_rank_exp,add_unit_exp,add_currency}`
   also support costs, stored residual EXP and player archive
   counters; scaling already-stored totals or spending is unsafe.
   Runtime settlement paths (notably absent `ffbe_battle.py`) must
   be verified before actually changing earnings.
7. **Adjustable drop rates**: candidate drops and actual awarded drops
   are different channels (see `ffbe_config.py` and
   `source/docs/reference/tbmonkey_api_calls/validated_endpoints.md`).
   Require identified legitimate random-selection point, per-result
   idempotency and no changes to limited/one-time/paid items.
8. **Repeat farming controls** — **pure policy already committed**:
   `repeat_stop_policy.js` and `repeat_observation_guard.js`.
   Disabled defaults; source-only tests pass. Actual opt-in gameplay
   wiring is on **HOLD** until an accepted, uniquely bound mission
   result, complete settlement and safe post-settlement repeat-stop
   invocation are independently established.

## Native-client integration: HOLD, no assumed gameplay success

9. **Battle speed controls**: upstream `android_build.py` supports
   1x and experimental 10x; `android_test.js` adjusts a global
   scheduler scale, not battle-only timing. Need safe per-scene
   activation/restoration and client verification before optional
   2x/3x settings.
10. **Skip animations**: no independently verified animation-specific
    skip seam; do not skip mission/end settlements or story/critical
    UI transitions. Investigate source-first only when a real
    per-animation event boundary is identified.
11. **Auto Battle improvements**: native repeat/autoplay observers
    are **not** a player-command AI. Need player-only legality,
    turn/action ownership, safe healing, disabled-defaults, manual
    fallback and enemy-AI isolation. No automatic items or changes to
    NPC/enemy AI are authorized here.
12. **Auto-retry defeated quests**: depends on actual authoritative
    confirmed defeat, clean failed-run settlement, unambiguous
    attempt identity, safe restart and retry limit. Current server's
    `attempt['cleared'] = (cleared is True)` collapses unknown into
    false; **do not infer defeat from stored False**. Therefore this
    remains the last/highest-risk gameplay automation item.

## Implementation gates

- Public repo stays PUBLIC. Keep original authorship and `upstream-source`
  untouched; changes are reversible on `develop`.
- Never change live canonical roster ordering or persist optional
  view state without explicit save-schema review.
- Keep rewards, purchases, quest progress, fusion, manual gameplay,
  existing no-duplicate-payment receipts, and enemy/NPC AI unchanged.
- No original data/assets, native code execution, APK builds, testing
  game binaries, installations, releases, merges or schedulers.
- CI is a *source-only* validation gate, not gameplay/device acceptance.

Next safely independent QoL feature after the unit and party view helpers:
a standalone **bulk fusion/material selection preview** using only
synthetic roster data and the existing validated server fusion input
rules. Do not perform fusion or modify inventory in that preview.
