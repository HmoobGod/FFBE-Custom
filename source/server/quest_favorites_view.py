"""Ephemeral, read-only quest favorites view for source-only FFBE-Custom.

Original catalog identity: F_MISSION_MST.qo3PECw6.
Original optional filters: gQR24kST (mode) and U9iHsau3 (dungeon).
See exvius_actions_modes._missions/_mission and player_state.mission_row.

All bookmarks are supplied by the caller and returned as detached values.
No global bookmark registry, saves, client navigation, completion switches,
game master-data loading, reward changes, or PlayerState imports are used.
"""
from __future__ import annotations

from copy import deepcopy

MISSION_ID = "qo3PECw6"
MISSION_MODE = "gQR24kST"
MISSION_DUNGEON = "U9iHsau3"


def _id(value, field: str, *, allow_zero=False) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{field} must be a decimal identifier")
    normalized = str(value)
    if not normalized or not normalized.isascii() or not normalized.isdecimal():
        raise ValueError(f"{field} must be a decimal identifier")
    if not allow_zero and int(normalized) == 0:
        raise ValueError(f"{field} must be a nonzero mission identifier")
    return normalized


def _catalog(mission_rows):
    if not isinstance(mission_rows, (list, tuple)):
        raise TypeError("mission_rows must be a list or tuple of catalog rows")
    rows, known = [], set()
    for row in mission_rows:
        if not isinstance(row, dict):
            raise TypeError("mission catalog rows must be mappings")
        mid = _id(row.get(MISSION_ID), MISSION_ID)
        if mid in known:
            raise ValueError("duplicate mission ID in catalog")
        known.add(mid)
        rows.append((mid, row))
    return rows, known


def _favorites(favorite_ids, known):
    if not isinstance(favorite_ids, (list, tuple)):
        raise TypeError("favorite_ids must be an ephemeral list or tuple")
    unique, seen = [], set()
    for raw in favorite_ids:
        mid = _id(raw, "favorite mission ID")
        if mid not in known:
            raise ValueError("favorite refers to a mission outside the catalog")
        if mid not in seen:
            seen.add(mid)
            unique.append(mid)
    return unique


def preview_quest_favorites(
    mission_rows, favorite_ids=(), *,
    favorites_only=False, favorites_first=False,
    mode=None, dungeon=None
):
    """Return a stable, detached view; never alter mission catalog or progress.

    Default: every catalog row in its original order, with ephemeral favorite
    annotations. When favorites_first=True, pinned missions precede other
    missions while maintaining original relative order within each group.
    Optional mode/dungeon filters compare exact source-backed field values.
    No mission eligibility, clear status, game UI, or navigation is inferred.
    """
    if not isinstance(favorites_only, bool) or not isinstance(favorites_first, bool):
        raise TypeError("favorites options must be booleans")
    mode_id = _id(mode, "mode", allow_zero=True) if mode is not None else None
    dungeon_id = _id(dungeon, "dungeon", allow_zero=True) if dungeon is not None else None
    rows, known = _catalog(mission_rows)
    ordered_favorites = _favorites(favorite_ids, known)
    marked = set(ordered_favorites)

    result = []
    for mid, source_row in rows:
        if mode_id is not None and str(source_row.get(MISSION_MODE)) != mode_id:
            continue
        if dungeon_id is not None and str(source_row.get(MISSION_DUNGEON)) != dungeon_id:
            continue
        favorite = mid in marked
        if favorites_only and not favorite:
            continue
        result.append({
            "mission_id": mid,
            "is_favorite": favorite,
            "mission": deepcopy(source_row),
        })
    if favorites_first:
        result.sort(key=lambda entry: not entry["is_favorite"])

    return {
        "preview_only": True,
        "persisted": False,
        "navigation_performed": False,
        "favorite_ids": list(ordered_favorites),
        "visible_count": len(result),
        "visible_favorites": sum(x["is_favorite"] for x in result),
        "entries": result,
    }


def toggle_ephemeral_favorite(mission_rows, favorite_ids, mission_id):
    """Pure on/off bookmark suggestion; caller owns the returned list.

    A toggle does NOT update an in-process singleton or on-disk account.
    Repeated favorite IDs in caller input are deduplicated consistently.
    """
    _rows, known = _catalog(mission_rows)
    current = _favorites(favorite_ids, known)
    target = _id(mission_id, "mission ID")
    if target not in known:
        raise ValueError("cannot bookmark an unknown mission ID")
    if target in current:
        return [mid for mid in current if mid != target]
    return current + [target]
