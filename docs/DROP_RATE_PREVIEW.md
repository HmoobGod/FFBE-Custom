# Adjustable normal-drop rates — pure source-only preview

**Status:** independent hypothetical rate-model prototype on PUBLIC
`develop`; **no native/gameplay integration, reward-roll change,
payout, inventory mutation, result-screen change, save or build.**

## What the permitted original source actually establishes

- `source/server/ffbe_config.py` labels the `y35YvQjZ`
  WaveBattleInfo rows as containing the `9BetM2Ds` **candidate**
  list. It identifies the separate `09HRWXDf` response as the
  mission-result item display channel.
- The same source explicitly reports that the client **discards the
  candidate's rate** when the candidate pool is handed over as-is,
  which previously displayed too many items at once. It documents
  an existing server-side `ROLL_DROPS` runtime setting (default ON),
  and says a failed candidate roll may grant no items. This
  setting is **not changed** by the new preview.
- The original source references `LAST_DROPS`, keyed by mission,
  to connect battle-load and mission-end views, but does not establish
  a unique client attempt nonce. The actual `ffbe_battle.py`
  roll and credit implementation is absent from the filtered
  public source tree.
- Prior `MIRROR_DROPS` result-screen experiments caused client
  black screens. The original `MIRROR_DROPS` default remains OFF.
  No result-screen mirroring is attempted here.
- Source-authored examples use four-field normal-drop candidate
  strings such as `20:1209000976:450:100`.
  The per-candidate numeric **percentage** interpretation is a
  conservative hypothetical preview model, **not independently
  proven to be the precise native RNG rule or eligible rate scale**.
- The original `source/docs/reference/tbmonkey_api_calls/validated_endpoints.md`
  likewise distinguishes a candidate pool from the display of
  earned result rows and delegates selection to the server.

This evidence permits a pure display-only candidate-rate *model*,
but not any live modification of drop chances or payouts.

## Prototype API

`source/server/drop_rate_preview.py` provides:

```python
from drop_rate_preview import (
    normalize_drop_rate_options, preview_normal_drop_rates
)

settings = normalize_drop_rate_options({"normal_drop_multiplier": 2})
preview = preview_normal_drop_rates(
    "20:1209000976:450:30,20:1209000975:1200:100",
    settings
)
# Two existing candidate rows only; hypothetical 30 -> 60, 100 -> 100.
# No random selection or item credit is ever performed.
```

The caller supplies native-looking `kind:id:count:rate` candidates.
The helper never imports live data files or a native/server runtime,
never creates new item IDs, never changes counts or positions, never
collapses repeated original candidate occurrences, and never rolls
chance outcomes. Defaults are `1x` with no other option enabled.

The optional integer factors `1x`–`5x` and the modeled integer
0–100 percentage ceiling are **prototype guardrails, not verified
native limits**. Hypothetical rates are multiplied then capped at 100.
Rate 0 remains 0, rate 100 remains 100. Invalid/unknown factors,
negative/fractional/out-of-range rates, malformed candidate strings,
and nonpositive counts reject instead of being silently reinterpreted.

Every result states `preview_only=True`, `rolled=False`,
`credited=False`, `native_rate_semantics_verified=False`,
and `source_eligibility_verified=False`. Do not infer that a
100% modeled rate means an actual item was won.

## Synthetic CI and remaining blockers

`source/exvius/tests/test_drop_rate_preview.py` uses only
fictional inputs and tests original-order preservation,
defaults, modeled 0/100 caps, invalid rates and inputs,
empty candidate pools, duplicate candidate occurrences,
deterministic results, and unchanged synthetic wallet,
inventory, quest progress, receipts, save dirty flags and
account state. Source-only CI executes the suite without
game data or APKs.

**Not established:** the native roll algorithm, eligible enemy
and reward classes, per-result once-only credit boundary,
actual drop outcome, result-screen parsing and exact sequencing
across repeated same-mission attempts. The live `ROLL_DROPS`,
`LAST_DROPS`, `MIRROR_DROPS`, normal rewards and game logic
remain byte-for-byte unchanged.

The next meaningful work is source-backed analysis of a
**safe visible in-game UI integration** for existing read-only QoL
prototypes, or separately authorized native/client evidence;
not a speculative credit or drop-roll hook. Repeat-stop
remains on HOLD.
