# QoL source map — initial inspection (2026-11-18)

**Scope:** read-only assessment of the permitted, public **source-only** import at
`develop` commit `c9a9713932149f261f06ae0377a5e450e60130fe`.
Original filtered-history base `upstream-source` `f567ba6ab2e4e5c7c064ad0d0abf3c9c4de0df2d`.
This document identifies edit points; it **does not claim game behavior has changed**.
All references are to code in this public repository.

## 1. Auto Battle — needs a separate design

**What is verified:** `source/exvius/mission_repeat.js` (lines 1–48) observes
`MissionRepeatResultInfo`/ `MissionRepeatUtil` and marks each completed
**repeat sequence** in `MissionEndRequest`. It does not contain a
player-move-selection policy. `source/exvius/android_test.js` wires this
hook under the startup stage `mission repeat` (around line 220).

**Boundary:** client-side repeat/autoplay state is not proof of an autonomous
legal battle-command engine. No safe source-only implementation target for
turn-by-turn Auto Battle was established in this audit. Do not hijack the
native battle command loop, automate items, or alter enemy AI without
separately verifying player-only command ownership and a manual fallback.

**Research next:** identify documented player-command interception and
manual/auto UI controls in permitted sources, then write a source-only
synthetic command-selection test before any native hook change.

## 2. Repeat farming — existing engine; safest near-term integration

**Client:** `source/exvius/mission_repeat.js` explicitly distinguishes the
first completed run from subsequent runs via `repeatRunMark` and an
`exvRepeatRun` marker.

**Server:** `source/server/exvius_repeat.py` provides
`begin_attempt` (line 13), `complete_attempt` (line 42),
`claim_mission_rewards` (line 121) and
`repeat_challenge_rewards` (line 168). It guards one loaded attempt,
keeps challenge reward receipts, pays original challenge Lapis per
qualifying clear but avoids repaying one-time non-Lapis rewards, and
rolls state back when partial credit fails. Failed/unknown results do
not create a successful clear.

**Entry points:** `source/server/exvius_actions_modes.py` calls
`begin_attempt` near line 210, and the mode result path calls
`repeat_challenge_rewards` near line 361.

**Safe extension:** preserve the existing reward and receipt ledger;
add only optional, user-visible repeat limits/stop conditions once the
corresponding client events and native UI have been verified. Don't
grant rewards from a timer or a client-only “completed” signal.

**Tests:** `source/exvius/test_mission_repeat.js`,
`source/exvius/tests/test_repeat.py`, and
`source/exvius/tests/test_upstream_repeat.py` contain synthetic
first-run, retry, restart, rollback and one-time/non-Lapis scenarios.
A very delayed retry remains a documented limitation of the current
mission-load idempotency boundary; do not claim durable attempt-ID
deduplication beyond the existing contract.

## 3. Battle speed — existing global test option, not a battle-only toggle

`source/exvius/android_build.py` (lines 27–46) permits only `--speed 1`
or `--speed 10`; the 10× option is explicitly labeled **TEST**.
`source/exvius/android_test.js` (lines 450–472) writes the scheduler
time-scale float `+0x24` on Cocos scheduler updates when `scale != 1`.
This accelerates **game time globally**; battle-only targeting has
not been established.

**Safe extension:** do not ship 10× as a normal default. Start by
testing a pure, clamped `1×/2×/3×` configuration parser without
modifying the binary hook, then separately validate scene-scoped
enable/restore logic and cutscenes on an authorized local build.
On-device speed stability is **unverified** here.

## 4. Unit management — existing transactions should stay authoritative

`source/server/ffbe_player.py` already handles
`apply_party_edit` (line 257), `serve_unit_favourite` (435),
`serve_unit_storage` (470), and `serve_unit_mix` (673).
`serve_unit_mix` batches multiple bases with a durable hash receipt
and transaction rollback. `source/server/player_state.py` has
`set_favourites` (2657), `set_storage` (2675),
`mix_units` (2794), `drop_units` (2869),
and `_unit_rows` (5056). Party edits reject non-owned unit IDs and
duplicate/malformed slot data rather than silently applying partial
decks. Unit roster projections preserve warehouse state.

**Safe extension:** prototype **read-only sorting/filtering/preset
preview** around current roster projections; do not reorder
`data['roster']` or rewrite inventory, equip, deck, and fusion
transactions just to change their visual order. Preserve favorites,
warehouse status, party membership and material-consumption guards.
Any bulk action needs explicit preview/confirmation and retry tests.

## 5. Adjustable progression — several ledgers, not one multiplier

`source/server/player_state.py` implements
`add_rank_exp` (2893), `add_currency` (2939), and
`add_unit_exp` (4116). Both rank EXP and unit EXP track
**residual EXP within a level**; rank-ups add the new energy capacity
to the held energy, while unit EXP has its own max-level/cumulative
total cap. `source/server/exvius_repeat.py` handles replayable
challenge Lapis separately from one-time rewards. Purchase/awakening
spending uses `source/server/exvius_actions_shops.py::_pay`
(183), with checks for materials and gil.

**Safe extension:** design isolated per-source opt-in parameters
(default all 1×) for rank EXP, unit EXP, earned gil, and eligible
normal battle drops. Only scale positive earned amounts at an
identified **pre-credit boundary**, once per verified completion.
Never scale quest claim receipts, spend/debits, Lapis, gacha costs,
purchased items, one-time rewards, or any persisted balance after
credit. Repeated results must not multiply again. Don't write settings
to existing saves before save-schema and migration tests pass.

## Build and runtime blockers

- The filtered import consists of source code and docs, **without**
  upstream JSON game tables, original APK, downloadable content,
  signing material, or extracted native binaries. It cannot produce
  or verify a playable Android build on its own.
- The pinned upstream tree does not contain `source/server/ffbe_battle.py`
  although `source/server/exvius_repeat.py` and
  `source/server/exvius_actions_modes.py` reference
  `ffbe_battle`. Do not infer that these runtime import paths work
  from Python syntax checks alone. Resolve source completeness
  separately and without importing copyrighted assets.
- Native client battle-command selectors, real party UI presentation,
  original assets, live save compatibility, and on-device performance
  are **not** established by source-only tests.

## Implementation order (proposal, not approvals)

1. Expand source-only CI with the existing isolated Python repeat
   tests (no real game data).
2. Add repeat-farming **stop condition** design with synthetic fixtures,
   avoiding payout changes.
3. Add read-only unit sorting/filtering specification and tests.
4. Design progression configuration with 1× defaults and explicit
   source/receipt eligibility, then implement only after choosing
   values and confirming save migration.
5. Investigate true player-only Auto Battle and scene-scoped speed
   hooks before any native changes.

**Preserved:** `upstream-source` unchanged; `main` unchanged;
`develop` may receive documentation and CI-only improvements.
No APK build, install, release, original asset upload, or scheduler.
