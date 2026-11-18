# Bulk fusion — read-only source-only selection preview

**Status:** structural selection preview implemented on PUBLIC `develop`.
It does not execute fusion, call native functions, read game assets,
operate on a live PlayerState, or write saves/receipts/currency.

## Actual original source and contract

`source/server/ffbe_player.py::serve_unit_mix` accepts the original
`UnitMixRequest` group `MIX_GROUP`, where each node has:

- `og2GHy49`: base unit's **instance** ID;
- `WbGYcN17`: comma-delimited donor/material instance IDs.

The handler rejects empty material lists, reused base IDs, duplicate
materials within one operation, donors reused across operations,
any base also used as a donor, and unknown/unowned instance IDs.
It also checks existing durable retry receipts. The actual
`PlayerState.mix_units` can consume donors, update unit EXP/affinity
and LB, grant original rewards, and cause other persistent effects.
These operations remain **untouched**.

## New isolated helper

`source/server/bulk_fusion_preview.py::preview_bulk_fusion` takes an
already-decoded, synthetic/caller-supplied roster and list of
selection mappings, without constructing the native request:

```python
preview_bulk_fusion(
    roster=[{"instance_id": "101", "master_id": "9001"},
            {"instance_id": "201", "master_id": "9101"}],
    selections=[{"base_id": "101", "material_ids": ["201"]}],
)
```

It validates structure and ownership, then returns **detached**
operation summaries preserving selection/material order, master ID
labels when provided, and unique base/donor counts. Every successful
preview has:

```python
{"preview_only": True, "executed": False,
 "executable": False, "requires_runtime_validation": True, ...}
```

A valid *structural selection* **does not establish that fusion can
safely be executed**. The helper cannot validate special trust
bonuses, rare unit/master requirements, reward capacity, actual
native party-membership restrictions, live receipts, or runtime
availability. It does not estimate XP, LB, trust, gil, or rewards
because that would require verified original master data and
transaction behavior. It does not authorize a future auto-fusion.

## Tests and safety gates

`source/exvius/tests/test_bulk_fusion_preview.py` uses synthetic
data to verify owned bases/donors, same-master distinct instances,
duplicate donor/base cases, cross-operation base/donor conflicts,
invalid IDs/requests, no partial handling of invalid batches,
deterministic detached output, and unchanged roster, party, currency,
inventory, receipt and dirty-state snapshots. The source-only
workflow runs those tests with other existing regressions.

**Still blocked:** native UI presentation, item eligibility
and irreversible fusion actions. No runtime effect, live save
compatibility proof, APK, or gameplay acceptance is claimed.
Revert by removing the module/tests, one CI step and this note;
no original server fusion or upstream code was edited.
