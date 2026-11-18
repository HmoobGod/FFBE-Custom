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
3. **Bulk unit management — source-only preview IMPLEMENTED**:
   `source/server/bulk_fusion_preview.py` mirrors the structural
   selection guards in `ffbe_player.py::serve_unit_mix`:
   owned instance IDs, nonempty material lists, duplicate bases,
   duplicate/reused donors, and base-as-donor conflicts. It returns
   detached operation summaries and **always executable=False**.
   `test_bulk_fusion_preview.py` uses synthetic units and verifies
   no roster, party, inventory, currency, receipt, dirty flag, or
   gameplay mutation. No actual fusion, EXP/trust estimation, native
   request, or full eligibility decision is implemented. Runtime
   fusion also requires more player-state, reward, and native checks.
4. **Quest favorites — ephemeral source-only preview IMPLEMENTED**:
   `source/server/quest_favorites_view.py` accepts caller-provided
   synthetic/catalog `F_MISSION_MST.qo3PECw6` mission rows and
   temporary bookmark IDs. It supports a detached view, stable
   favorites-first ordering, favorites-only and source-backed mode
   (`gQR24kST`)/dungeon (`U9iHsau3`) filters, plus an ephemeral
   pure toggle. `test_quest_favorites_view.py` exercises invalid
   and duplicate IDs, filters, stable order, and unchanged mission
   progress, rewards, save and dirty flags. No runtime table loading,
   persistence, native navigation, quest unlocking or game UI
   is implemented. See `docs/QUEST_FAVORITES_VIEW.md`.
5. **Better reward summaries — source-only preview IMPLEMENTED**:
   `source/server/reward_receipt_summary.py` takes caller-supplied
   committed copies of `exvius_repeat.attempt` and totals only the
   recorded `paid` challenge reward rows by original `kind:id`,
   preserving mission separation. It ignores repeat receipt copies
   of the same local sequence, rejects conflicting duplicates, lists
   withheld-entry counts without paying them, and skips pending,
   incomplete, or unknown-result receipts. `test_reward_receipt_summary.py`
   exercises both original-shaped receipt aggregation and unchanged
   wallet, inventory, progress and saves. No native results UI, client
   counter, runtime request, receipt archive, normal-drop reporting,
   reward credit, or save changes exist. See
   `docs/REWARD_RECEIPT_SUMMARY.md`.

## Develop after receipt and eligible-source rules are verified

6. **Adjustable EXP and gil — pure source-only preview IMPLEMENTED**:
   `source/server/progression_multiplier_preview.py` projects
   independent rank EXP, unit EXP and earned-gil amounts, all at
   default 1x. Its optional 1x–5x whole-number settings require
   nonnegative earnings, reject unknown channels and potential
   debits, and never mutate wallet, rank, roster, existing EXP,
   archive counters, receipts or saves. The synthetic
   `test_progression_multiplier_preview.py` covers these guards.
   This is not a real earning multiplier: source eligibility,
   normal mission credit paths (missing `ffbe_battle.py`),
   residual level-up rules and exactly-once payout integration
   need separate evidence. See
   `docs/PROGRESSION_MULTIPLIER_PREVIEW.md`.
7. **Adjustable drop rates — pure hypothetical preview IMPLEMENTED**:
   `source/server/drop_rate_preview.py` models caller-provided original
   `9BetM2Ds` candidate strings (`kind:id:count:rate`) with a
   default 1x and optional 1x–5x settings, no random roll and no
   credit. A 0–100 percentage scale and 100 cap are explicit
   *hypothetical* model assumptions; the exact native RNG formula,
   per-result attempt identity, and eligible drop sources remain
   unverified. `test_drop_rate_preview.py` uses synthetic data
   for candidate preservation, invalid/zero rates, and unchanged
   wallet, inventory, receipts and saves. The original
   `ROLL_DROPS` remains ON and `MIRROR_DROPS` remains OFF.
   No original actual drop manipulation or game UI is implemented.
   See `docs/DROP_RATE_PREVIEW.md`.
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

## Shared read-only QoL interface — standalone CLI IMPLEMENTED

`source/exvius/qol_preview_cli.py` exposes **existing**, independent
read-only roster sorting, party preset comparison, temporary quest favorites,
and completed challenge receipt summaries through a human-readable command
line. It reads only caller-supplied JSON on stdin and writes only text/JSON
to stdout. No server runtime, native hooks, PlayerState, file paths,
game saves, account network, inventory mutation or result-screen code.
`test_qol_preview_cli.py` runs subprocess tests in an isolated empty
directory to prove output and rejection paths. It does **not** provide
an in-game menu or claim Android gameplay acceptance.
See `docs/READ_ONLY_QOL_CLI.md`.

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

Next genuine integration gate: verify a safe read-only
Android/native QoL entry point independently before any actual in-game
UI or hook implementation. The existing title menu can create a new
save, and the Home menu uses native Frida/Cocos code; this new
standalone CLI does not modify either. No actual credit, drop
rolls, repeat automation or native hooks are authorized.
Keep repeat-stop and native battle controls on HOLD.
