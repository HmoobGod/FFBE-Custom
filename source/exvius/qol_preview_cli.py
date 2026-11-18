"""Standalone, read-only CLI for existing FFBE-Custom QoL previews.

Reads ONE caller-supplied JSON object on stdin (max 1 MiB) and prints
a human-readable report or --json object. This is deliberately NOT an
Android UI, native hook, running server endpoint, or save-file reader.
No file paths, PlayerState imports, writes, network, or game assets.

Only delegates to already-tested pure, source-only preview helpers.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Resolve only the checked-in pure preview modules. Never import player_state,
# ffbe_state, offline_menu, or any gameplay/credit entry point.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from unit_roster_view import SORTS, STORAGE_FILTERS, select_roster_view
from party_preset_preview import PARTY_SLOTS, preview_party_preset
from quest_favorites_view import preview_quest_favorites
from reward_receipt_summary import summarize_challenge_reward_receipts

MAX_STDIN_CHARS = 1_048_576


def _read_payload(stream):
    raw = stream.read(MAX_STDIN_CHARS + 1)
    if len(raw) > MAX_STDIN_CHARS:
        raise ValueError("input exceeds one MiB preview limit")
    if not raw.strip():
        raise ValueError("expected one JSON object on stdin")

    def reject_constant(name):
        raise ValueError("non-finite JSON value is not supported")

    payload = json.loads(raw, parse_constant=reject_constant)
    if not isinstance(payload, dict):
        raise ValueError("preview input must be a JSON object")
    return payload


def _require(payload, required, optional=()):
    unknown = set(payload) - set(required) - set(optional)
    missing = set(required) - set(payload)
    if unknown or missing:
        raise ValueError("invalid preview fields (unknown or missing keys)")


def _dispatch(args, payload):
    if args.view == "roster":
        _require(payload, ("roster",))
        return select_roster_view(
            payload["roster"], sort=args.sort,
            favorites_only=args.favorites_only, storage=args.storage
        )
    if args.view == "party":
        _require(payload, ("roster", "party", "preset"))
        return preview_party_preset(
            payload["roster"], payload["party"], payload["preset"], mode=args.mode
        )
    if args.view == "quests":
        _require(payload, ("missions",), ("favorite_ids",))
        return preview_quest_favorites(
            payload["missions"], payload.get("favorite_ids", []),
            favorites_only=args.favorites_only, favorites_first=args.favorites_first,
            mode=args.mode, dungeon=args.dungeon
        )
    if args.view == "rewards":
        _require(payload, ("attempt_snapshots",))
        return summarize_challenge_reward_receipts(payload["attempt_snapshots"])
    raise ValueError("unknown preview")


def _text_result(args, result):
    lines = ["FFBE-Custom SOURCE-ONLY PREVIEW (no gameplay or save changes)"]
    if args.view == "roster":
        lines.append(f"Roster: {len(result)} unit(s)")
        for row in result:
            lines.append(
                f"  Unit {row.get('instance_id', '?')} "
                f"level={row.get('level', '?')} "
                f"favorite={row.get('favourite', 0)} "
                f"storage={row.get('storage_state', 0)}"
            )
    elif args.view == "party":
        lines.append(
            f"Deck {result['target_deck_id']} (active={result['active_deck_id']}): "
            f"{result['before']['name']} -> {result['proposed']['name']}"
        )
        lines.append(
            f"  {len(result['slot_changes'])} changed slot(s); "
            f"slot limit={result['slot_limit']}"
        )
        for change in result["slot_changes"]:
            before = change["before"]
            after = change["after"]
            lines.append(
                f"  Slot {change['slot'] + 1}: "
                f"{before['instance_id'] if before else '-'} -> "
                f"{after['instance_id'] if after else '-'}"
            )
        lines.append("  NOT APPLIED: active party and saved decks unchanged")
    elif args.view == "quests":
        lines.append(
            f"Quest catalog: {result['visible_count']} visible; "
            f"{result['visible_favorites']} marked favorite"
        )
        for entry in result["entries"]:
            lines.append(
                f"  {'*' if entry['is_favorite'] else ' '} "
                f"Mission {entry['mission_id']}"
            )
        lines.append("  Favorites are temporary; navigation and progress unchanged")
    else:
        lines.append(
            f"Challenge receipts: {result['receipt_count']} unique; "
            f"{result['duplicate_snapshots_ignored']} duplicate copies ignored; "
            f"{len(result['skipped'])} excluded"
        )
        lines.append("  Recorded challenge payouts only; not full mission rewards")
        for item in result["totals"]:
            lines.append(
                f"  Reward kind={item['kind']} id={item['id']} count={item['count']}"
            )
        lines.append("  NO CREDIT: wallet, inventory and saves unchanged")
    return "\n".join(lines)


def main(argv=None, *, stdin=None, stdout=None, stderr=None):
    parser = argparse.ArgumentParser(
        description="Read-only FFBE-Custom QoL previews from caller-supplied JSON stdin"
    )
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    sub = parser.add_subparsers(dest="view", required=True)
    roster = sub.add_parser("roster", help="sort/filter a decoded unit roster")
    roster.add_argument("--sort", choices=sorted(SORTS), default="original")
    roster.add_argument("--storage", choices=sorted(STORAGE_FILTERS), default="all")
    roster.add_argument("--favorites-only", action="store_true")
    party = sub.add_parser("party", help="compare an owned party to a proposed preset")
    party.add_argument("--mode", choices=list(PARTY_SLOTS), default="normal")
    quests = sub.add_parser("quests", help="show temporary quest favorites")
    quests.add_argument("--favorites-only", action="store_true")
    quests.add_argument("--favorites-first", action="store_true")
    quests.add_argument("--mode", help="source-backed mission mode ID")
    quests.add_argument("--dungeon", help="source-backed dungeon ID")
    sub.add_parser("rewards", help="summarize saved challenge payout receipt copies")

    args = parser.parse_args(argv)
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr
    try:
        payload = _read_payload(stdin)
        result = _dispatch(args, payload)
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False), file=stdout)
        else:
            print(_text_result(args, result), file=stdout)
        return 0
    except (ValueError, TypeError, OverflowError) as exc:
        print(f"Preview rejected: {exc}", file=stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
