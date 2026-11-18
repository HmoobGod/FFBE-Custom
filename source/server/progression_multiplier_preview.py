"""Pure, source-only EXP and earned-gil multiplier PREVIEW.

Original source:
  player_state.py::add_rank_exp   - residual rank EXP + energy on rank-up
  player_state.py::add_unit_exp   - residual unit EXP + capped total_exp
  player_state.py::add_currency   - mixed credit/debit method; positive gil
                                  increments TOTAL_GIL_GET archive counter
  player_state.py::spend_currency - separately handles costs

No live caller, PlayerState import, credit/expense interception, save
persistence, native UI, receipt processing, or original master data.
The caller MUST already have independently determined that a positive
amount represents a legitimate, uncredited EARNING of the named channel.
This helper cannot make that determination, and never does the credit.
"""
from __future__ import annotations

from types import MappingProxyType

CHANNELS = ("rank_exp", "unit_exp", "earned_gil")
DEFAULT_MULTIPLIERS = MappingProxyType({channel: 1 for channel in CHANNELS})
ALLOWED_MULTIPLIERS = frozenset({1, 2, 3, 4, 5})
MAX_PREVIEW_AMOUNT = 2**63 - 1


def normalize_earning_multipliers(settings=None) -> dict[str, int]:
    """Return detached settings; defaults are the original 1x for all.

    Pure prototype permits only positive whole-number 1x..5x rates so
    no rounding rule, negatives, or unexpectedly large factor is guessed.
    Unsupported/unknown keys fail closed instead of enabling a channel.
    """
    if settings is None:
        return dict(DEFAULT_MULTIPLIERS)
    if not isinstance(settings, dict):
        raise TypeError("settings must be a mapping or None")
    if set(settings) - set(CHANNELS):
        raise ValueError("unknown progression multiplier channel")
    result = dict(DEFAULT_MULTIPLIERS)
    for channel, value in settings.items():
        if type(value) is not int or value not in ALLOWED_MULTIPLIERS:
            raise ValueError(f"{channel}: multiplier must be an integer from 1 to 5")
        result[channel] = value
    return result


def preview_progression_earning(channel, earned_amount, settings=None):
    """Calculate a NON-AUTHORITATIVE projected earned amount.

    Does not read or modify wallets, EXP, balances, roster, receipts, or
    saves. A negative amount (potential spend/debit) is rejected, not
    multiplied. Values beyond a signed 64-bit preview ceiling reject
    instead of making a promise about the native game's integer limits.
    """
    if not isinstance(channel, str) or channel not in CHANNELS:
        raise ValueError("unsupported earning channel")
    policy = normalize_earning_multipliers(settings)
    if type(earned_amount) is not int or not 0 <= earned_amount <= MAX_PREVIEW_AMOUNT:
        raise ValueError("earned_amount must be a nonnegative bounded integer")
    multiplier = policy[channel]
    projected = earned_amount * multiplier
    if projected > MAX_PREVIEW_AMOUNT:
        raise OverflowError("projected earning exceeds preview ceiling")
    return {
        "preview_only": True,
        "credited": False,
        "source_eligibility_verified": False,
        "channel": channel,
        "multiplier": multiplier,
        "original_amount": earned_amount,
        "projected_amount": projected,
        "additional_amount": projected - earned_amount,
    }
