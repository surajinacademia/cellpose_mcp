#!/usr/bin/env python3
"""Inventory a Git worktree without modifying user files or the Git index."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


def require_executable(name: str) -> str:
    """Resolve one required executable to an absolute path."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} is required to inventory this repository")
    return executable


GIT: str = require_executable("git")


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    """One path and its independent worktree/index evidence."""

    path: str
    category: str
    git_status: str | None
    kind: str
    worktree_size: int | None
    worktree_sha256: str | None
    index_sha256: str | None


def git_output(repo: Path, *args: str) -> bytes:
    """Run one fixed read-only Git query with optional locks disabled."""
    environment = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    completed = subprocess.run(  # noqa: S603
        [GIT, "--no-optional-locks", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env=environment,
    )
    return completed.stdout


def decode_path(raw: bytes) -> str:
    """Decode a path while preserving undecodable filesystem bytes."""
    return raw.decode("utf-8", errors="surrogateescape")


def index_entries(repo: Path) -> dict[str, str]:
    """Map every stage-zero tracked path to its Git object ID."""
    payload = git_output(repo, "ls-files", "--stage", "-z")
    entries: dict[str, str] = {}
    for record in payload.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", maxsplit=1)
        _mode, object_id, stage = metadata.split()
        if stage != b"0":
            raise RuntimeError("cannot inventory an unmerged Git index")
        entries[decode_path(raw_path)] = object_id.decode("ascii")
    return entries


def changed_paths(repo: Path) -> dict[str, str]:
    """Map changed/untracked paths to two-character porcelain status."""
    payload = git_output(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--no-renames",
    )
    changed: dict[str, str] = {}
    for record in payload.split(b"\0"):
        if not record:
            continue
        if len(record) < 4 or record[2:3] != b" ":
            raise RuntimeError("unexpected Git porcelain record")
        changed[decode_path(record[3:])] = record[:2].decode("ascii")
    return changed


def sha256_bytes(content: bytes) -> str:
    """Return a SHA-256 digest for bytes."""
    return hashlib.sha256(content).hexdigest()


def index_sha256(repo: Path, object_id: str) -> str:
    """Hash the exact blob currently recorded by the Git index."""
    return sha256_bytes(git_output(repo, "cat-file", "blob", object_id))


def file_identity(
    info: os.stat_result,
) -> tuple[int, int, int, int, int]:
    """Return fields that must remain stable during hashing."""
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_mode,
    )


def hash_regular_stable(path: Path) -> tuple[int, str]:
    """Hash a regular file through a no-follow descriptor or abort on change."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = file_identity(os.fstat(descriptor))
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after_descriptor = file_identity(os.fstat(descriptor))
    finally:
        os.close(descriptor)
    try:
        after_path = file_identity(path.lstat())
    except FileNotFoundError as exc:
        raise RuntimeError(f"{path} changed while it was being hashed") from exc
    if before != after_descriptor or after_descriptor != after_path:
        raise RuntimeError(f"{path} changed while it was being hashed")
    return before[2], digest.hexdigest()


def inspect_worktree(
    repo: Path,
    relative: str,
) -> tuple[str, int | None, str | None]:
    """Inspect one path without following symbolic links."""
    path = repo / relative
    try:
        before = path.lstat()
    except FileNotFoundError:
        return "missing", None, None
    if stat.S_ISLNK(before.st_mode):
        target = os.readlink(path).encode("utf-8", errors="surrogateescape")
        after = path.lstat()
        if file_identity(before) != file_identity(after):
            raise RuntimeError(f"{path} changed while it was being hashed")
        return "symlink", len(target), sha256_bytes(target)
    if stat.S_ISREG(before.st_mode):
        size, digest = hash_regular_stable(path)
        return "file", size, digest
    kind = "directory" if stat.S_ISDIR(before.st_mode) else "other"
    return kind, before.st_size, None


def index_file(repo: Path) -> Path:
    """Resolve the Git index path without assuming a standard `.git` layout."""
    raw = git_output(repo, "rev-parse", "--git-path", "index").rstrip(b"\n")
    path = Path(decode_path(raw))
    return path if path.is_absolute() else repo / path


def index_identity(path: Path) -> tuple[int, int, int, str]:
    """Capture index size, timestamp, inode, and content hash."""
    info = path.stat()
    return (
        info.st_size,
        info.st_mtime_ns,
        info.st_ino,
        sha256_bytes(path.read_bytes()),
    )


def build_inventory(repo: Path) -> dict[str, object]:
    """Build a path-sorted inventory and prove Git left its index untouched."""
    index_path = index_file(repo)
    before_index = index_identity(index_path)
    tracked = index_entries(repo)
    changed = changed_paths(repo)
    entries: list[InventoryEntry] = []
    for relative in sorted(set(tracked) | set(changed)):
        status_code = changed.get(relative)
        category = (
            "tracked"
            if status_code is None
            else "untracked"
            if status_code == "??"
            else "modified"
        )
        kind, size, worktree_digest = inspect_worktree(repo, relative)
        object_id = tracked.get(relative)
        entries.append(
            InventoryEntry(
                path=relative,
                category=category,
                git_status=status_code,
                kind=kind,
                worktree_size=size,
                worktree_sha256=worktree_digest,
                index_sha256=(
                    index_sha256(repo, object_id)
                    if object_id is not None
                    else None
                ),
            )
        )
    after_index = index_identity(index_path)
    if after_index != before_index:
        raise RuntimeError("Git index changed during read-only inventory")
    totals = Counter(entry.category for entry in entries)
    commit = git_output(repo, "rev-parse", "HEAD").decode("ascii").strip()
    return {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "commit": commit,
        "entries": [asdict(entry) for entry in entries],
        "totals": dict(sorted(totals.items())),
    }
