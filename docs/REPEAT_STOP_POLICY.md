# Repeat-farming stop policy — source-only prototype

**Status: implemented and synthetic-testable, NOT connected to gameplay.**
Original author: Elvlin (see repository README). Work here is confined to
`develop`; `upstream-source` remains the unmodified filtered import.

## Files

- `source/exvius/repeat_stop_policy.js` — pure option normalizer and
  continuation decision. **No Frida, native, Java or server integration.**
- `source/exvius/test_repeat_stop_policy.js` — synthetic deterministic tests
  (Node.js only, no game assets or player state).
- `.github/workflows/source-checks.yml` — runs the test alongside existing
  client and server source-only regressions.

## Opt-in controls

The module accepts a temporary caller-supplied policy object:

```js
// Both OFF by default. No persisted setting or game UI has been added.
{ maxCompletedRuns: null, stopOnFailure: false }

// Illustration of a FUTURE caller's opt-in settings only:
{ maxCompletedRuns: 10, stopOnFailure: true }
```

- `maxCompletedRuns`: `null` means unlimited. A positive, safe integer means
  stop when at least N **confirmed completed results** have been counted,
  including failed results. N=1 allows a first run at count 0 and stops
  after one result.
- `stopOnFailure`: `false` means the policy does not stop on failures.
  `true` stops on a confirmed failed result, even below the run limit.
- Unrecognized/invalid options cause an exception instead of silently
  disabling a safety condition; any future integration must treat that as
  a stop. No external config is consumed in this prototype.

## Pure evaluation contract

`decideRepeatStop(options, progress)` returns
`{stop: boolean, reason: string}`, where `progress` is an independent
**verified** summary:

```js
{completedRuns: 0, lastCleared: null}    // before the first run
{completedRuns: 1, lastCleared: true}    // after one confirmed clear
{completedRuns: 2, lastCleared: false}   // after one confirmed failed result
```

Possible reasons: `disabled`, `continue`, `failure`,
`max-completed-runs`, `unverified-progress`, and `unverified-result`.
With any option enabled, unknown/contradictory progress returns a safe stop.
With both options OFF, the function returns `stop:false` without checking
a game result, preserving the original no-policy behavior.

Priority if both stop rules match: `failure` before
`max-completed-runs`. There are no clocks, timers, mutable globals, I/O,
save edits or network operations. Repeated identical inputs return the
same decision.

## Crucial integration boundary

**The module does not presently stop actual farming.** The existing
`mission_repeat.js` observes native repeat sequence events and
`MissionResultResponse` constructors and marks repeated MissionEnd
requests for reward reconciliation. Those events are **not yet verified**
as authoritative clear/failure outcomes or as safe commands to stop the
native repeat UI.

Before any wiring, verify (on a separately authorized device/test build)
a trustworthy cleared/failed result and the original native repeat-stop
entry point. Use the client to stop *future* runs only after the current
result settles. Do not abort a mission mid-result, use an inferred result,
disable manual play, or touch enemy AI.

`source/server/exvius_repeat.py` retains exclusive reward settlement:
pending-load receipts, retries, Lapis and one-time challenge rewards remain
unchanged. No policies are written into the original save schema. Any future
settings storage must be designed and reviewed separately for save
compatibility and opt-in defaults.

## Verified scope / remaining blockers

- Synthetic test covers disabled defaults, one/three-run limits, failure
  stops, unknown outcomes, invalid options, and deterministic immutable inputs.
- CI runs Python and JS syntax, existing repeat receipts tests, and this new
  source-only test.
- Original client, game assets, native binary, exact stop UI semantics and
  runtime save compatibility are **not** verified by these tests.
- No APK, build, installation, release, merge or scheduling is performed.

Reversion is simply removing these two new JS files, this documentation,
and the one added CI command from `develop`. All existing gameplay and
server reward code remains byte-for-byte unchanged.
