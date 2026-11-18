
# FFBE-Custom — standalone offline visual QoL preview

**Status (2026-11-18):** independently generated, source-only HTML demo.
It is **not** the original Android client, an in-game menu, a live
account viewer, or a supported way to edit actual player data.

## Source-backed implementation

`source/exvius/qol_visual_preview.py` imports only three existing,
purely read-only Python helpers:

- `source/server/unit_roster_view.py::select_roster_view`
- `source/server/party_preset_preview.py::preview_party_preset`
- `source/server/quest_favorites_view.py::preview_quest_favorites`

The generator calls these verified helpers to **precompute** every
supported combination of the controls for its fictional fixtures,
then embeds those results in one self-contained HTML page. Browser
controls only select among these precomputed pure-helper outputs.

There is **no browser-to-Python bridge, network call, server endpoint,
file picker, original game database, account information, PlayerState
import, native/UI hook, game install, APK, copyrighted artwork or save
file**. The quest-star controls update temporary **in-memory** selection
only and reset on reload; they do not persist to localStorage, cookies
or the original game. A strict local HTML Content Security Policy has
`default-src 'none'` and `connect-src 'none'`, and embeds the sample
styles, JavaScript and data without external dependencies.

## Create and open the page

From the public repo's root (Python 3.10+ installed):

```sh
python -B source/exvius/qol_visual_preview.py > ffbe-qol-preview.html
```

Open the generated `ffbe-qol-preview.html` directly in any current
desktop or mobile browser that allows local HTML files. No local server
or internet connection is needed to operate the page. Generating an
HTML file is only creating this **static sample-page artifact**; it
does not save or persist player/bookmark/game data. Do not commit the
generated HTML if it contains any future privately supplied inputs.

This command runs the Python pure preview logic **at generation time**.
Once the page exists, it does not require Python or a server.
The committed source-only Python generator itself writes just to
standard output, not to a specified save path.

## Available visual controls

1. **Unit roster:** original/favorites/level sorts, active/warehouse
   filters, and favorites-only filtering.
2. **Party comparison:** three illustrative existing deck/preset
   combinations, before/after changes, original active deck unchanged.
3. **Quest favorites:** three fictional mission IDs, clickable stars
   to toggle temporary bookmarks, favorites first/only, and original
   `gQR24kST` mode / `U9iHsau3` dungeon filters. A reload starts with
   **zero** bookmarks.

This page intentionally does **not** show rank EXP, gil modifiers,
drop-rate previews, real reward payout records, or automated battle
controls. The prior standalone read-only CLI remains available for
recorded challenge-receipt summaries, also with caller-supplied data.

## Testing

- `source/exvius/tests/test_qol_visual_preview.py` verifies the
  generator's data comes from existing helpers, preserves expected
  unit/party/quest views, covers all cross-product states, makes
  deterministic HTML, enforces offline security features, and
  writes no files when run from an isolated temporary directory.
- `source/exvius/test_qol_visual_preview.cjs` runs the actual embedded
  browser JavaScript in a controlled in-memory DOM stand-in. It
  dispatches real change/click handlers to verify roster sort/filter,
  party selection, quest star toggling, favorites first/only,
  mode/dungeon filtering, visible/hidden panels and reset on a new
  page instance. It rejects network/native/persistence functions.
- `source/exvius/test_qol_visual_browser.cjs` launches installed
  Chrome/Chromium in headless mode with the exact locally generated
  fictional `file://` page. The test uses loopback Chrome DevTools
  Protocol **only as the test harness**. It verifies real DOM
  rendering, roster sorting, warehouse filtering, party comparison,
  quest stars, bookmark reset on reload, 320px responsive width,
  no browser JavaScript exceptions, and no external page HTTP requests.
  The test clearly outputs SKIP if no browser is installed; a green
  CI alone is not evidence of a real-browser pass.
- GitHub Actions executes the Python, simulated-DOM, and optional
  real-Chromium tests in the source-only job. The 2026-11-18 run
  `44389947210` printed **BROWSER PASS** for headless Chromium.
  These are offline HTML/browser acceptance checks, **not** native
  Android game or device acceptance.

## Remaining boundaries

The original `source/exvius/android/OfflineMenu.java` is a title
Continue/New Game overlay; its companion server handler may create a
new save. The original Home menu extensions use Frida/Cocos native
symbols. Neither is a verified safe integration site for these
standalone QoL features without separately authorized client testing.

**No original Java, Home menu, PlayerState, mission/reward settlement,
save format, repeat control, enemy AI or native game logic was changed.**
Keep repeat-stop, actual Auto Battle and game-side QoL hooks on HOLD.

Next useful step is separately verifying a nonmutating client
view-entry lifecycle, or increasing independent browser acceptance
for this already-useful offline sample page. Do not make speculative
native hooks or claim Android gameplay acceptance.
