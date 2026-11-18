# Adjustable EXP and gil — pure source-only multiplier preview

**Status:** an isolated, reversible earning projection exists on PUBLIC
`develop`. Not connected to any runtime credit, quest, fusion, battle
result, native hook, player save or account. No earning rates are changed.

## Original source-backed credit boundaries

Checked against `source/server/player_state.py`:

- `add_rank_exp(amount)` (near line 2893) increases rank EXP in the
  **current rank's residual** field and walks rank-up thresholds. Rank-ups
  add the NEW rank energy cap to current energy, including over-cap.
- `add_unit_exp(instance_id, amount)` (near line 4116) advances that
  unit's residual EXP and level, also updating `total_exp` with a
  master-specific cap. Fusion can call this method; its existence alone
  does **not** identify a safe earned-battle-EXP source.
- `add_currency(kind, amount)` (near line 2939) is a general balance
  mutation method; positive gil also increments the original
  `TOTAL_GIL_GET` archive counter. It does NOT distinguish eligible
  quest gil from other credit sources by itself.
- `spend_currency` (near line 2947) and `spend_lapis` are distinct
  debit pathways. They must never be passed through a future earning
  multiplier. Positive values from other routes (grants, mail,
  reimbursements, purchases, receipts) cannot be assumed to be
  ordinary earned gil without separately verified provenance.
- `exvius_actions_modes.py` refers to `ffbe_battle.credit_mission_rewards`
  for normal mission settlement; the pinned filtered/public source
  tree does not include `ffbe_battle.py`. Consequently neither the
  exact eligible earned amount nor safe once-only pre-credit insertion
  is established by this source-only prototype.

No rank calculations, unit caps, energy, currency, archive, receipts,
inventory or save schema were modified.

## Standalone API and deliberate restrictions

`source/server/progression_multiplier_preview.py` exports:

```python
from progression_multiplier_preview import (
    normalize_earning_multipliers, preview_progression_earning
)

# Both omitted settings and empty settings mean all-original 1x rates.
settings = normalize_earning_multipliers({
    "rank_exp": 2, "unit_exp": 3, "earned_gil": 5
})
example = preview_progression_earning("rank_exp", 100, settings)
# {"preview_only": True, "credited": False,
#  "source_eligibility_verified": False, "channel": "rank_exp",
#  "multiplier": 2, "original_amount": 100,
#  "projected_amount": 200, "additional_amount": 100}
```

All channels have independent, default `1` rates.
The prototype deliberately accepts only integer **1x–5x** settings
and nonnegative whole-number input amounts. The restricted range is
a conservative *prototype choice*, not a verified native-game rate
limit. This avoids rounding ambiguity and invalid factors. Zero
remains zero. Negative values, potential spending/debits, unknown
channels, unknown settings, booleans, fractions, and values exceeding
the signed-64-bit preview ceiling are rejected. No runtime conversion,
credit or rounding is attempted.

The helper cannot independently determine that a proposed number is
a legal/eligible earning event and **always returns
`source_eligibility_verified=False`**. The projections must not be
treated as earned/persisted rewards or actual gameplay statistics.

## Synthetic test coverage

`source/exvius/tests/test_progression_multiplier_preview.py` checks:

- 1x default settings for rank EXP, unit EXP, and gil;
- independent 2x/3x/4x/5x positive earned previews;
- zero, negative/debit, unknown-source and invalid-setting handling;
- bounded integer overflow rather than silent arithmetic wraps;
- deterministic results and defensive detached settings;
- unchanged synthetic wallet, roster, rank, currency, inventory,
  mission progress, receipts, and save version/dirty flags;
- no converted earnings being recorded as a real credit.

GitHub Actions runs the suite in the original source-only workflow.
An exact-head green workflow means **source-only tests passed**, not
that the game awards boosted EXP or gil.

## Actual gameplay integration — on HOLD

A future implementation must first demonstrate actual earned-source
provenance, signed/typed currency paths, proper order relative to
level caps and archive counters, exactly-once reward settlement,
and player-save compatibility. It must not multiply stored residual
EXP, existing balances, equipment/fusion valuation, spending, purchase
prices, replay receipts or existing paid rewards. No implementation
of actual credit scaling, original data access or APK testing is
authorized in this checkpoint.

Repeat-stop and native battle behavior also remain on HOLD.
