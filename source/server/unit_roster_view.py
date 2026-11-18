"""Read-only FFBE unit roster view — source-only QoL prototype.

Operates on a caller-supplied list of existing player roster rows, not the
client's obfuscated reply, canonical PlayerState, or on-disk save. No imports
from server runtime or original game data. Never reorder or mutate the input.

Verified PlayerState fields: instance_id, level, favourite, storage_state.
Unknown master-data rarity, equip stats, and native UI ordering are not
guessed. Not connected to the server response pipeline or Android client.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

SORTS = frozenset({
    "original", "level_asc", "level_desc", "favorites_first",
    "favorites_level_desc",
})
STORAGE_FILTERS = frozenset({"all", "active", "warehouse"})


def _favourite(row: dict) -> bool:
    value = row.get("favourite", 0)
    if value in (0, "0", False, None):
        return False
    if value in (1, "1", True):
        return True
    raise ValueError("unit favourite is not a supported 0/1 flag")


def _warehouse(row: dict) -> bool:
    value = row.get("storage_state", 0)
    if value in (0, "0", False, None):
        return False
    if value in (1, "1", True):
        return True
    raise ValueError("unit storage state is not a supported 0/1 flag")


def _level(row: dict) -> int:
    value = row.get("level")
    if isinstance(value, bool) or not (
        isinstance(value, int) or
        (isinstance(value, str) and value.isascii() and value.isdecimal())
    ):
        raise ValueError("unit level must be a positive integer")
    level = int(value)
    if level < 1:
        raise ValueError("unit level must be a positive integer")
    return level


def select_roster_view(
    roster: list[dict] | tuple[dict, ...],
    *,
    sort: str = "original",
    favorites_only: bool = False,
    storage: str = "all",
) -> list[dict[str, Any]]:
    """Return a defensive COPY of a filtered and stably sorted roster.

    All controls default to their original no-op setting. The order of the
    canonical roster and all row fields are preserved with default settings.
    Equal sort keys preserve original order. Filters do not change saved
    favourites, warehouse membership, party decks, equipment, or currency.

    Invalid options and malformed fields needed by an enabled filter/sort
    raise rather than quietly hiding or misordering units.
    """
    if not isinstance(roster, (list, tuple)):
        raise TypeError("roster must be a list or tuple of unit rows")
    if any(not isinstance(row, dict) for row in roster):
        raise TypeError("each roster unit must be a mapping")
    if sort not in SORTS:
        raise ValueError("unsupported roster sort")
    if storage not in STORAGE_FILTERS:
        raise ValueError("unsupported storage filter")
    if not isinstance(favorites_only, bool):
        raise TypeError("favorites_only must be boolean")

    rows = list(roster)
    if storage != "all":
        rows = [row for row in rows
                if _warehouse(row) == (storage == "warehouse")]
    if favorites_only:
        rows = [row for row in rows if _favourite(row)]

    if sort == "level_asc":
        rows.sort(key=_level)
    elif sort == "level_desc":
        rows.sort(key=_level, reverse=True)
    elif sort == "favorites_first":
        rows.sort(key=lambda row: not _favourite(row))
    elif sort == "favorites_level_desc":
        rows.sort(key=lambda row: (not _favourite(row), -_level(row)))
    # sort == "original" intentionally performs no sorting at all.

    return deepcopy(rows)
