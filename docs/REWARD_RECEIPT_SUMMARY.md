# Better reward summaries — read-only source-only QoL prototype

**Status:** an isolated pure summary of original challenge-payout receipts
has been implemented. **Not wired to a client result screen, native
hooks, live game, user save, reward executor, or runtime server.**

## Source-backed receipt provenance

Inspected in the PUBLIC permitted source:

- `source/server/exvius_repeat.py::begin_attempt` stores one most-recent
  attempt in `player.data['exvius_repeat']['attempt']`:
  `mid`, local server `sequence`, and `status='pending'`.
- `exvius_repeat.complete_attempt` completes the existing controlled
  challenge-reward transaction, then stores `status='completed'`,
  `cleared=(cleared is True)`, `paid`, and `blocked` in that attempt.
- A `paid` entry is `{'id': challenge_id, 'rewards': [row, ...]}`.
  Each credited reward row includes numeric `kind`, `id`, and
  positive `count` (additional unit metadata can also be present).
- `blocked` entries represent **withheld**, unsupported or failed
  challenge reward entries and are not earned payouts.
- `claim_mission_rewards` and other settlement paths operate
  separately; `repeat_challenge_rewards` can add
  `mission_bonus_awards` or other side effects **after** the challenge
  attempt is marked completed. This summary intentionally excludes
  those and all normal drops, EXP, unit awards outside the challenge
  `paid` rows, and any currency spent or earned elsewhere.
- The original ledger persists **only the most recent attempt**, not
  a comprehensive historical log. A multi-attempt preview requires
  separately supplied historical copies from the same player ledger
  lineage. No tracking, collection or save-format changes were added.

## Implemented API

`source/server/reward_receipt_summary.py` exports
`summarize_challenge_reward_receipts(attempt_snapshots)`.

It accepts caller-supplied snapshots of the original attempt
dictionaries and returns a detached preview with:

- `receipt_count`: unique completed and confirmed-clear snapshots
  that passed structural validation (including legitimate zero-paid
  challenge clears).
- `totals`: stable first-seen combined counts, grouped by the original
  `kind` and `id` fields, not invented item descriptions.
- `by_mission`: same totals within each `mid`.
- `receipts`: local server sequence, mission, credited challenge and
  reward-row counts, and withheld-entry counts.
- `duplicate_snapshots_ignored`: matching snapshots with the same
  locally scoped sequence only count once.
- `skipped`: pending, incomplete, or unknown-result snapshots with
  reasons. The helper never infers "defeat" from persisted
  `cleared=False`, which may also represent an unknown outcome.
- `blocked_entry_count`: count of withheld entries, never paid amounts.
- `preview_only=True` and `credited=False`.

Conflicting completed snapshots with the same local sequence or
malformed paid rows fail closed with an exception. Multiple identical
reward occurrences **within one real receipt** retain their summed
quantities: the deduplication is of duplicate *receipt snapshots*, not
individual reward rows.

The local `sequence` is **not a native/client nonce, globally unique
transaction ID, or proof that a completed result was delivered to the
client**. Callers must supply trusted snapshots from the same ledger
lineage. Do not aggregate arbitrary saves or use constructor counts
to synthesize records.

## Safety and tests

`source/exvius/tests/test_reward_receipt_summary.py` uses synthetic
original-shaped challenge receipts; it tests repeated copies,
sequential actual-style Lapis/non-Lapis grants, partial blocked
entries, different mission grouping, duplicate original reward
occurrences, unknown/false/pending/incomplete outcomes, conflicting
sequence records, invalid counts and IDs, and unchanged wallet,
inventory, quest progress, save flags, and source receipts.

The source-only workflow runs this suite alongside roster, party,
fusion, quest favorites, repeat receipts and JavaScript checks.
No original server reward logic or PlayerState was edited.

## Not implemented / next evidence

An actual native **game reward summary UI** still needs independently
verified read-only client integration and complete per-attempt receipt
provenance. No whole-run or lifetime reward totals can be claimed from
the single stored attempt or client constructors. Full-game accounting
requires separately verified other reward sources and idempotent IDs.

**Repeat-stop and native battle controls remain on HOLD.**
