#!/usr/bin/env python3
"""Fail closed if a public FFBE-Custom branch tracks non-source game contents.

This is a conservative file/path guard, NOT a secret scanner, runtime test, or
copyright determination. The upstream import script filters full history first.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CODE_EXTENSIONS = {
    ".py", ".js", ".cjs", ".java", ".kt", ".rs", ".gradle",
    ".toml", ".lock", ".ps1", ".sh", ".bat", ".cmd", ".md",
    ".xml", ".properties", ".html", ".css", ".yml", ".yaml",
    ".ini", ".c", ".h", ".cpp", ".hpp",
}
MAX_FILE_BYTES = 2 * 1024 * 1024
BLOCKED_EXTENSIONS = {
    ".apk", ".aab", ".obb", ".cpk", ".so", ".png", ".jpg", ".jpeg",
    ".webp", ".gif", ".wav", ".ogg", ".mp3", ".flac", ".mp4",
    ".zip", ".7z", ".rar", ".pak", ".keystore", ".jks",
    ".pem", ".key", ".p12", ".pfx", ".sav", ".sqlite", ".db", ".json",
}
SENSITIVE_PATH_PARTS = {
    "release", "data", "game-assets", "client", "private", "saves",
    "shared_prefs", "cpk_extract", "mst_decoded", "text_decoded",
    "downloaded-data", "certs",
}


def run(repo: Path, *command: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *command])


def permitted(path: str) -> bool:
    parts = Path(path).parts
    if not parts or path.startswith("/") or ".." in parts:
        return False
    if any(part.lower() in SENSITIVE_PATH_PARTS for part in parts):
        return False
    if Path(path).suffix.lower() in BLOCKED_EXTENSIONS:
        return False
    if path in {"README.md", ".gitignore"}:
        return True
    if path.startswith("source/"):
        return Path(path).suffix.lower() in CODE_EXTENSIONS
    if path.startswith("scripts/"):
        return Path(path).suffix.lower() in {".py", ".sh"}
    if path.startswith("docs/"):
        return Path(path).suffix.lower() in {".md", ".txt"}
    if path.startswith(".github/workflows/"):
        return Path(path).suffix.lower() in {".yml", ".yaml"}
    return False


def inspect_current(repo: Path) -> tuple[int, list[str]]:
    failures: list[str] = []
    count = 0
    for entry in run(repo, "ls-files", "-s", "-z").split(b"\0"):
        if not entry:
            continue
        try:
            metadata, raw_path = entry.split(b"\t", 1)
            mode, sha, _stage = metadata.decode().split()
            path = raw_path.decode("utf-8", errors="replace")
        except ValueError:
            failures.append("unparseable Git index entry")
            continue
        count += 1
        if not permitted(path):
            failures.append(f"disallowed tracked path: {path}")
        if mode != "100644" and mode != "100755":
            failures.append(f"non-regular file mode {mode}: {path}")
        try:
            size = int(run(repo, "cat-file", "-s", sha).strip())
            if size > MAX_FILE_BYTES:
                failures.append(f"tracked file exceeds {MAX_FILE_BYTES} bytes: {path}")
        except (subprocess.CalledProcessError, ValueError):
            failures.append(f"cannot inspect tracked blob: {path}")
    return count, failures


def inspect_history(repo: Path) -> list[str]:
    # Covers paths deleted in a later commit as well as the current tree.
    names = run(repo, "log", "--all", "--name-only", "--format=", "--no-renames")
    failures = []
    for name in set(filter(None, names.decode("utf-8", "replace").splitlines())):
        if not permitted(name):
            failures.append(f"disallowed historical path: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--require-source", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        tracked, errors = inspect_current(repo)
        if args.history:
            errors += inspect_history(repo)
        if args.require_source and not run(repo, "ls-files", "--", "source/").strip():
            errors.append("no imported source files found")
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"Cannot complete Git tree audit: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {tracked} tracked text-source/infrastructure files; no disallowed paths")
    if args.history:
        print("PASS: historical filenames comply with the source-only allowlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
