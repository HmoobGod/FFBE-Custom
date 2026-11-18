"""Pure, hypothetical preview of native normal-drop candidate rates.

The permitted source describes WaveBattleInfo token 9BetM2Ds as a
per-monster CANDIDATE list, separate from actual awarded items, and
provides authored strings such as "20:1209000976:450:100".
This source-only helper accepts a caller-supplied 4-field candidate CSV
(kind:id:count:rate), never loads real tables or executes a roll.

The 0..100 percent interpretation and 1..5x multiplier here are a
HYPOTHETICAL PREVIEW MODEL, NOT independently proven native RNG math.
No rewards are selected, granted, persisted, or mirrored to the native
result-screen item channel. Default 1x preserves the supplied rate.
"""
from __future__ import annotations

from types import MappingProxyType

DEFAULT_DROP_RATE_OPTIONS = MappingProxyType({"normal_drop_multiplier": 1})
ALLOWED_MULTIPLIERS = frozenset((1, 2, 3, 4, 5))


def normalize_drop_rate_options(options=None):
    """Validate separate, optional model settings without storing them."""
    if options is None:
        return dict(DEFAULT_DROP_RATE_OPTIONS)
    if not isinstance(options, dict):
        raise TypeError("drop-rate options must be a dict or None")
    if set(options) - {"normal_drop_multiplier"}:
        raise ValueError("unknown drop-rate option")
    factor = options.get("normal_drop_multiplier", 1)
    if type(factor) is not int or factor not in ALLOWED_MULTIPLIERS:
        raise ValueError("normal_drop_multiplier must be an integer from 1 to 5")
    return {"normal_drop_multiplier": factor}


def _whole(raw, label, *, positive=False, maximum=None):
    if not isinstance(raw, str) or not raw or not raw.isascii() or not raw.isdecimal():
        raise ValueError(f"{label} must be a decimal integer")
    value = int(raw)
    if positive and value < 1:
        raise ValueError(f"{label} must be positive")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} exceeds preview model ceiling")
    return value


def preview_normal_drop_rates(candidate_csv, options=None):
    """Return independent, deterministic rates for EXISTING candidate rows.

    Each native-looking row is kind:id:count:rate. This helper models rate
    as an integer 0..100 percentage (not an established actual engine RNG
    probability), and clamps a multiplied hypothetical rate at 100.
    No random generator, catalog access, eligibility decision, new drop,
    result response, inventory, receipt or server state is involved.
    Duplicate candidate occurrences are kept as independent source rows.
    """
    normalized = normalize_drop_rate_options(options)
    if not isinstance(candidate_csv, str):
        raise TypeError("candidate_csv must be caller-provided text")
    factor = normalized["normal_drop_multiplier"]
    previews = []
    if candidate_csv:
        for idx, item in enumerate(candidate_csv.split(",")):
            parts = item.split(":")
            if len(parts) != 4:
                raise ValueError("native-looking drop candidate must have four fields")
            kind = _whole(parts[0], "kind")
            item_id = _whole(parts[1], "item_id")
            count = _whole(parts[2], "count", positive=True)
            rate = _whole(parts[3], "rate", maximum=100)
            previews.append({
                "index": idx,
                "kind": kind,
                "id": item_id,
                "count": count,
                "original_rate_percent_model": rate,
                "hypothetical_rate_percent_model": min(100, rate * factor),
            })
    return {
        "preview_only": True,
        "rolled": False,
        "credited": False,
        "native_rate_semantics_verified": False,
        "source_eligibility_verified": False,
        "channel": "9BetM2Ds",
        "rate_model": "hypothetical-integer-percent-0-to-100",
        "multiplier": factor,
        "candidate_count": len(previews),
        "candidates": previews,
    }
