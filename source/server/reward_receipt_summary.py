"""Pure read-only summary of committed challenge reward receipt snapshots.

Source contract: exvius_repeat.complete_attempt writes its last attempt in
player.data['exvius_repeat']['attempt'] with mid, sequence, status, cleared,
paid=[{'id': challenge_id, 'rewards': [{'kind','id','count', ...}]}],
and blocked=[{'id','entry','reason'}]. Never credits rewards or reads saves.

Scope is stored challenge paid rows only. Normal drops, mission bonuses,
side-mode rewards and all other game currency/EXP are excluded. Inputs must
be trusted committed receipt snapshots from ONE player's ledger lineage.
The original save retains only its most recent attempt: a multi-attempt
summary requires caller-provided historical copies. Sequence is not a
native/client nonce or globally unique identifier.
"""
from __future__ import annotations

from copy import deepcopy
import json


def _whole(value, field, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{field} must be a nonnegative integer")
    raw = str(value)
    if not raw or not raw.isascii() or not raw.isdecimal():
        raise ValueError(f"{field} must be a nonnegative integer")
    parsed = int(raw)
    if positive and parsed < 1:
        raise ValueError(f"{field} must be positive")
    return parsed


def _nonempty(value, field):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{field} must be a nonempty ID")
    text = str(value)
    if not text or not text.strip():
        raise ValueError(f"{field} must be a nonempty ID")
    return text


def _verified(receipt):
    """Return normalized paid rows or a reason nothing can be claimed."""
    if not isinstance(receipt, dict):
        return None, "incomplete-receipt"
    if receipt.get("status") != "completed":
        return None, "unsettled-or-unknown-status"
    try:
        mid = _nonempty(receipt.get("mid"), "mid")
        seq = _whole(receipt.get("sequence"), "sequence", positive=True)
    except ValueError:
        return None, "incomplete-receipt"
    if not isinstance(receipt.get("paid"), list) or not isinstance(receipt.get("blocked"), list):
        return None, "incomplete-receipt"
    if receipt.get("cleared") is not True:
        # Stored False merges actual failures and UNKNOWN; never infer either.
        if receipt["paid"]:
            raise ValueError("non-clear receipt contradicts its paid rewards")
        return None, "unverified-clear-status"

    paid, used_challenges = [], set()
    for entry in receipt["paid"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("rewards"), list):
            raise ValueError("malformed challenge payout entry")
        challenge = _nonempty(entry.get("id"), "challenge id")
        if challenge in used_challenges:
            raise ValueError("duplicate challenge within one paid receipt")
        used_challenges.add(challenge)
        rewards = []
        if not entry["rewards"]:
            raise ValueError("empty paid challenge has no credit evidence")
        for row in entry["rewards"]:
            if not isinstance(row, dict):
                raise ValueError("invalid credited reward row")
            kind = _whole(row.get("kind"), "reward kind")
            item = _whole(row.get("id"), "reward id")
            count = _whole(row.get("count"), "reward count", positive=True)
            rewards.append({"kind": kind, "id": item, "count": count})
        paid.append({"id": challenge, "rewards": rewards})

    for entry in receipt["blocked"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("reason"), str):
            raise ValueError("malformed blocked challenge entry")
        _nonempty(entry.get("id"), "blocked challenge id")

    # Later additions to the same attempt, such as mission_bonus_awards
    # or quest_progress_recorded, are deliberately not part of identity.
    try:
        fingerprint = json.dumps({
            "paid": receipt["paid"], "blocked": receipt["blocked"],
            "cleared": receipt["cleared"]
        }, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("non-serializable receipt fields") from exc
    return {
        "mid": mid, "sequence": seq, "paid": paid,
        "blocked_count": len(receipt["blocked"]),
        "fingerprint": fingerprint,
    }, None


def summarize_challenge_reward_receipts(attempt_snapshots):
    """Summarize settled challenge rows without any state mutation.

    Repeated snapshots of the same locally scoped server sequence count
    once; conflicting snapshots at that sequence raise. Source ordering
    is maintained. This does not prove a client-side result acknowledgement.
    """
    if not isinstance(attempt_snapshots, (list, tuple)):
        raise TypeError("attempt_snapshots must be a list or tuple")

    seen = {}
    totals = {}
    mission_totals = {}
    receipts = []
    skipped = []
    duplicate_count = 0
    blocked_count = 0
    for index, snapshot in enumerate(attempt_snapshots):
        normalized, reason = _verified(snapshot)
        if reason is not None:
            skipped.append({"index": index, "reason": reason})
            continue
        seq = normalized["sequence"]
        identity = (normalized["mid"], normalized["fingerprint"])
        if seq in seen:
            if seen[seq] != identity:
                raise ValueError("conflicting completed receipts for one local sequence")
            duplicate_count += 1
            continue
        seen[seq] = identity
        mid = normalized["mid"]
        blocked_count += normalized["blocked_count"]
        if mid not in mission_totals:
            mission_totals[mid] = {"mission_id": mid, "receipt_count": 0, "totals": {}}
        mission_totals[mid]["receipt_count"] += 1

        count_rows = 0
        for challenge in normalized["paid"]:
            for reward in challenge["rewards"]:
                key = (reward["kind"], reward["id"])
                totals[key] = totals.get(key, 0) + reward["count"]
                local = mission_totals[mid]["totals"]
                local[key] = local.get(key, 0) + reward["count"]
                count_rows += 1
        receipts.append({
            "mission_id": mid, "sequence": seq,
            "paid_challenge_count": len(normalized["paid"]),
            "paid_reward_row_count": count_rows,
            "blocked_entry_count": normalized["blocked_count"],
        })

    def rows(group):
        return [{"kind": kind, "id": item, "count": count}
                for (kind, item), count in group.items()]

    return deepcopy({
        "preview_only": True,
        "credited": False,
        "source": "exvius_repeat.attempt.paid",
        "scope": "challenge-reward-receipts-only",
        "receipt_count": len(receipts),
        "duplicate_snapshots_ignored": duplicate_count,
        "skipped": skipped,
        "blocked_entry_count": blocked_count,
        "totals": rows(totals),
        "by_mission": [
            {"mission_id": v["mission_id"], "receipt_count": v["receipt_count"],
             "totals": rows(v["totals"])} for v in mission_totals.values()
        ],
        "receipts": receipts,
    })
