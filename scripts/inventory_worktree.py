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
READ_NOFOLLOW_FLAGS = (
    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
)
DIRECTORY_NOFOLLOW_FLAGS = READ_NOFOLLOW_FLAGS | os.O_DIRECTORY


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    """One path and its independent worktree/index evidence."""

    path: str
    category: str
    git_status: str | None
    kind: str
    worktree_size: int | None
    worktree_sha256: str | None
    index_object_id: str | None
    index_mode: str | None
    index_type: str | None
    index_sha256: str | None


@dataclass(frozen=True, slots=True)
class IndexRecord:
    """One stage-zero path recorded in the Git index."""

    object_id: str
    mode: str


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


def read_index_records(repo: Path) -> dict[str, IndexRecord]:
    """Read mode and object identity for every stage-zero tracked path."""
    payload = git_output(repo, "ls-files", "--stage", "-z")
    records: dict[str, IndexRecord] = {}
    for record in payload.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", maxsplit=1)
        mode, object_id, stage = metadata.split()
        if stage != b"0":
            raise RuntimeError("cannot inventory an unmerged Git index")
        records[decode_path(raw_path)] = IndexRecord(
            object_id=object_id.decode("ascii"),
            mode=mode.decode("ascii"),
        )
    return records


def index_entries(repo: Path) -> dict[str, str]:
    """Map every stage-zero tracked path to its Git object ID."""
    return {
        path: record.object_id
        for path, record in read_index_records(repo).items()
    }


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


def index_object_type(mode: str) -> str:
    """Map a Git index mode to its object type."""
    return "commit" if mode == "160000" else "blob"


def file_identity(
    info: os.stat_result,
) -> tuple[int, int, int, int, int, int]:
    """Return fields that must remain stable during hashing."""
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_mode,
    )


def read_descriptor_sha256(descriptor: int) -> str:
    """Hash all bytes available from one open descriptor."""
    digest = hashlib.sha256()
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
    return digest.hexdigest()


def hash_regular_stable(path: Path) -> tuple[int, str]:
    """Hash a regular file through a no-follow descriptor or abort on change."""
    try:
        descriptor = os.open(path, READ_NOFOLLOW_FLAGS)
    except OSError as exc:
        raise RuntimeError(f"{path} changed while it was being hashed") from exc
    try:
        before = file_identity(os.fstat(descriptor))
        if not stat.S_ISREG(before[-1]):
            raise RuntimeError(f"{path} changed while it was being hashed")
        digest = read_descriptor_sha256(descriptor)
        after_descriptor = file_identity(os.fstat(descriptor))
        try:
            after_path = file_identity(path.lstat())
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"{path} changed while it was being hashed"
            ) from exc
        if before != after_descriptor or after_descriptor != after_path:
            raise RuntimeError(f"{path} changed while it was being hashed")
        return before[2], digest
    finally:
        os.close(descriptor)


def worktree_components(relative: str) -> list[str]:
    """Validate and split one repository-relative Git path."""
    components = relative.split("/")
    if (
        not relative
        or relative.startswith("/")
        or any(component in {"", ".", ".."} for component in components)
    ):
        raise RuntimeError(f"invalid worktree-relative path: {relative!r}")
    return components


def close_descriptors(descriptors: list[int]) -> None:
    """Close a descriptor chain from leaf to root."""
    for descriptor in reversed(descriptors):
        os.close(descriptor)


def open_worktree_parent(
    repo: Path,
    relative: str,
) -> tuple[list[int], list[str]]:
    """Open every descendant directory without following symbolic links."""
    components = worktree_components(relative)
    try:
        root_descriptor = os.open(repo, DIRECTORY_NOFOLLOW_FLAGS)
    except OSError as exc:
        raise RuntimeError(f"cannot safely open worktree root: {repo}") from exc
    descriptors = [root_descriptor]
    for component in components[:-1]:
        try:
            child_descriptor = os.open(
                component,
                DIRECTORY_NOFOLLOW_FLAGS,
                dir_fd=descriptors[-1],
            )
        except OSError as exc:
            close_descriptors(descriptors)
            raise RuntimeError(
                f"symbolic link in worktree path: {repo / relative}"
            ) from exc
        child_info = os.fstat(child_descriptor)
        if not stat.S_ISDIR(child_info.st_mode):
            os.close(child_descriptor)
            close_descriptors(descriptors)
            raise RuntimeError(
                f"symbolic link in worktree path: {repo / relative}"
            )
        descriptors.append(child_descriptor)
    return descriptors, components


def validate_worktree_ancestors(
    descriptors: list[int],
    components: list[str],
    path: Path,
) -> None:
    """Prove each opened directory is still named by its parent."""
    for parent, child, component in zip(
        descriptors[:-1],
        descriptors[1:],
        components[:-1],
        strict=True,
    ):
        try:
            named = file_identity(
                os.stat(component, dir_fd=parent, follow_symlinks=False)
            )
        except OSError as exc:
            raise RuntimeError(
                f"{path} changed while it was being hashed"
            ) from exc
        opened = file_identity(os.fstat(child))
        if named != opened or not stat.S_ISDIR(opened[-1]):
            raise RuntimeError(f"{path} changed while it was being hashed")


def inspect_worktree(
    repo: Path,
    relative: str,
) -> tuple[str, int | None, str | None]:
    """Inspect one path without following symbolic links."""
    path = repo / relative
    descriptors, components = open_worktree_parent(repo, relative)
    parent_descriptor = descriptors[-1]
    leaf = components[-1]
    try:
        try:
            before_info = os.stat(
                leaf,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            validate_worktree_ancestors(descriptors, components, path)
            return "missing", None, None
        before = file_identity(before_info)
        if stat.S_ISLNK(before_info.st_mode):
            try:
                raw_target = os.readlink(leaf, dir_fd=parent_descriptor)
                after = file_identity(
                    os.stat(
                        leaf,
                        dir_fd=parent_descriptor,
                        follow_symlinks=False,
                    )
                )
            except OSError as exc:
                raise RuntimeError(
                    f"{path} changed while it was being hashed"
                ) from exc
            validate_worktree_ancestors(descriptors, components, path)
            if before != after:
                raise RuntimeError(f"{path} changed while it was being hashed")
            target = raw_target.encode(
                "utf-8",
                errors="surrogateescape",
            )
            return "symlink", len(target), sha256_bytes(target)
        if stat.S_ISREG(before_info.st_mode):
            try:
                descriptor = os.open(
                    leaf,
                    READ_NOFOLLOW_FLAGS,
                    dir_fd=parent_descriptor,
                )
            except OSError as exc:
                raise RuntimeError(
                    f"{path} changed while it was being hashed"
                ) from exc
            try:
                opened = file_identity(os.fstat(descriptor))
                if opened != before or not stat.S_ISREG(opened[-1]):
                    raise RuntimeError(
                        f"{path} changed while it was being hashed"
                    )
                digest = read_descriptor_sha256(descriptor)
                after_descriptor = file_identity(os.fstat(descriptor))
                try:
                    after_path = file_identity(
                        os.stat(
                            leaf,
                            dir_fd=parent_descriptor,
                            follow_symlinks=False,
                        )
                    )
                except OSError as exc:
                    raise RuntimeError(
                        f"{path} changed while it was being hashed"
                    ) from exc
                validate_worktree_ancestors(
                    descriptors,
                    components,
                    path,
                )
                if (
                    before != opened
                    or opened != after_descriptor
                    or after_descriptor != after_path
                ):
                    raise RuntimeError(
                        f"{path} changed while it was being hashed"
                    )
                return "file", opened[2], digest
            finally:
                os.close(descriptor)
        try:
            after = file_identity(
                os.stat(
                    leaf,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            )
        except OSError as exc:
            raise RuntimeError(
                f"{path} changed while it was being hashed"
            ) from exc
        validate_worktree_ancestors(descriptors, components, path)
        if before != after:
            raise RuntimeError(f"{path} changed while it was being hashed")
        kind = "directory" if stat.S_ISDIR(before_info.st_mode) else "other"
        return kind, before_info.st_size, None
    finally:
        close_descriptors(descriptors)


def index_file(repo: Path) -> Path:
    """Resolve the Git index path without assuming a standard `.git` layout."""
    raw = git_output(repo, "rev-parse", "--git-path", "index").rstrip(b"\n")
    path = Path(decode_path(raw))
    return path if path.is_absolute() else repo / path


def index_identity(
    path: Path,
) -> tuple[int, int, int, int, int, int, str]:
    """Capture one stable, no-follow identity and hash for the Git index."""
    try:
        descriptor = os.open(path, READ_NOFOLLOW_FLAGS)
    except OSError as exc:
        raise RuntimeError(
            f"Git index path is not a stable regular file: {path}"
        ) from exc
    try:
        before = file_identity(os.fstat(descriptor))
        if not stat.S_ISREG(before[-1]):
            raise RuntimeError(
                f"Git index path is not a stable regular file: {path}"
            )
        digest = read_descriptor_sha256(descriptor)
        after_descriptor = file_identity(os.fstat(descriptor))
        try:
            after_path = file_identity(path.lstat())
        except OSError as exc:
            raise RuntimeError(
                f"Git index changed while it was being read: {path}"
            ) from exc
        if before != after_descriptor or after_descriptor != after_path:
            raise RuntimeError(
                f"Git index changed while it was being read: {path}"
            )
        return (*before, digest)
    finally:
        os.close(descriptor)


def head_commit(repo: Path) -> str:
    """Return the currently checked-out commit object ID."""
    return git_output(repo, "rev-parse", "HEAD").decode("ascii").strip()


def build_inventory(repo: Path) -> dict[str, object]:
    """Build a path-sorted inventory and prove Git left its index untouched."""
    index_path = index_file(repo)
    before_index = index_identity(index_path)
    before_head = head_commit(repo)
    tracked = read_index_records(repo)
    before_changed = changed_paths(repo)
    entries: list[InventoryEntry] = []
    for relative in sorted(set(tracked) | set(before_changed)):
        status_code = before_changed.get(relative)
        category = (
            "tracked"
            if status_code is None
            else "untracked"
            if status_code == "??"
            else "modified"
        )
        kind, size, worktree_digest = inspect_worktree(repo, relative)
        index_record = tracked.get(relative)
        object_type = (
            index_object_type(index_record.mode)
            if index_record is not None
            else None
        )
        entries.append(
            InventoryEntry(
                path=relative,
                category=category,
                git_status=status_code,
                kind=kind,
                worktree_size=size,
                worktree_sha256=worktree_digest,
                index_object_id=(
                    index_record.object_id
                    if index_record is not None
                    else None
                ),
                index_mode=(
                    index_record.mode
                    if index_record is not None
                    else None
                ),
                index_type=object_type,
                index_sha256=(
                    index_sha256(repo, index_record.object_id)
                    if index_record is not None
                    and object_type == "blob"
                    else None
                ),
            )
        )
    after_changed = changed_paths(repo)
    after_head = head_commit(repo)
    after_index = index_identity(index_path)
    if after_index != before_index:
        raise RuntimeError("Git index changed during read-only inventory")
    if after_changed != before_changed:
        raise RuntimeError("worktree status changed during inventory")
    if after_head != before_head:
        raise RuntimeError("HEAD changed during inventory")
    totals = Counter(entry.category for entry in entries)
    return {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "commit": before_head,
        "entries": [asdict(entry) for entry in entries],
        "totals": dict(sorted(totals.items())),
    }
