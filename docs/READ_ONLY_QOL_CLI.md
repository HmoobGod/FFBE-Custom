# Standalone read-only QoL command-line interface

Status (2026-11-18): **SOURCE-ONLY CLI implemented**, not an Android
or native FFBE menu. It reuses the existing validated preview modules;
it does not create another inventory/party/reward implementation.

## Why this is a separate CLI

- `source/exvius/android/OfflineMenu.java` is a title overlay
  with Continue/New Game handlers, and the matching
  `source/server/offline_menu.py` can create or replace a local
  save. Attaching a new gameplay QoL view to this UI without native
  validation risks mixing read-only previews with mutations.
- `source/exvius/home_carousel.js` implements menu changes using
  Cocos/native symbols through Frida. There is no verified isolated
  in-game entry point for these particular preview functions.
- Therefore **no hooks, original client UI, Java/Frida initialization,
  server endpoints or save paths were edited.** This CLI is a
  separate user-visible *development preview*, not gameplay UI.

## Interface

Run from the repository root with Python 3.10 or later.
The command reads a **caller-supplied JSON object from standard input**.
The CLI never opens a game save or mission master-data file and does
not write output files. It imports only the already-tested, pure helper
modules under `source/server/`.

Available commands:

- `python source/exvius/qol_preview_cli.py roster`
  - Input envelope: `{"roster":[...decoded owned unit rows...]}`
  - Flags: `--sort original|level_asc|level_desc|favorites_first|favorites_level_desc`,
    `--storage all|active|warehouse`, `--favorites-only`.
  - Defaults preserve original roster order and show all units.
- `python source/exvius/qol_preview_cli.py party`
  - Input envelope: `{"roster":[...],"party":{...},"preset":{...}}`.
  - Optional `--mode normal|7|8|11|50`.
  - Compares existing deck slots against a proposed arrangement.
    **Does not switch the active party or save a preset**.
- `python source/exvius/qol_preview_cli.py quests`
  - Input envelope: `{"missions":[...],"favorite_ids":[...]}`.
  - Flags: `--favorites-only`, `--favorites-first`,
    `--mode SOURCE_MISSION_MODE_ID`, `--dungeon SOURCE_DUNGEON_ID`.
  - Bookmark IDs exist only in the supplied object. No persistence,
    native navigation, or unlock/completion handling.
- `python source/exvius/qol_preview_cli.py rewards`
  - Input envelope: `{"attempt_snapshots":[...]}`.
  - Counts committed `exvius_repeat.attempt.paid` **challenge
    reward rows only**; repeats of the same local receipt are
    deduplicated. Requires trusted snapshots from one player ledger.
    Does not synthesize missing history or normal-drop payouts.

Default output is **readable text**. Put `--json` before the subcommand
for structured output, e.g.
`python source/exvius/qol_preview_cli.py --json roster --sort level_desc`.
The JSON is printed to stdout, not saved automatically.

### Minimal synthetic invocation

```sh
python source/exvius/qol_preview_cli.py roster --sort favorites_first <<'EXAMPLE'
{"roster":[
 {"instance_id":"101","level":20,"favourite":0,"storage_state":0},
 {"instance_id":"102","level":40,"favourite":1,"storage_state":0}
]}
EXAMPLE
```

This displays the two **synthetic** units (102 before 101) in a
read-only report. It is not connected to an actual roster or game.

## Operational and safety boundaries

- The JSON input size is limited to 1,048,576 characters; invalid
  JSON, unsupported fields and malformed requests exit with code 2,
  a message on stderr, and **no partial preview output**.
- The CLI does not have parameters to read/write files, launch a game,
  connect to a remote server, execute a fusion, alter a save, or grant
  rewards. It never imports live `PlayerState` or Android/Frida code.
- Use only synthetic/anonymized caller-supplied data when testing. Do
  not publish actual personal game saves or protected master tables to
  this public repository.
- It returns detached results from the source-only preview helpers.
  A pass in GitHub Actions is not native-client/device acceptance.
- `source/exvius/tests/test_qol_preview_cli.py` exercises four
  command paths with synthetic stdin in an isolated empty working
  directory and checks errors, deterministic ordering, nonmutation,
  and no files written in that directory. The workflow runs this
  test in the existing public-source job.
- Repeat-stop, native UI, battle speed, auto-battle, actual credits,
  drop rolls, save migration and game builds remain on HOLD.

Next genuine integration gate: document and independently verify a
nonmutating Android/native QoL view entry point and its safe lifecycle,
with explicit authorization before any hook or APK work. Do not claim
the command-line preview is playable in the original game.
