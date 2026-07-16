# Cellpose Repository Preservation Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the dirty repository safely, lock the supported Python
development environment, create an explicitly release-blocked feature ledger,
and prove that clean build artifacts contain only intended package files.

**Architecture:** This phase adds only repository/release infrastructure beside
the current server. It inventories every tracked, modified, and non-ignored
untracked path before this implementation edits any pre-existing non-planning
project file, stages only new plan-owned hunks from already-dirty files, builds
from a clean committed clone, and keeps the
`0.2.0` release gate deliberately blocked until pinned CP4/CP3 probes define
the full required capability matrix in the next plan.

**Tech Stack:** Python 3.11/3.12, uv 0.10.4, Pydantic 2, standard-library Git
subprocesses/SHA-256/TOML/venv/archive readers, setuptools, build, pytest,
Ruff, mypy, GitHub Actions.

## Global Constraints

- Initial supported platform is macOS 14 or later on Apple Silicon.
- Initial supported client is Codex Desktop.
- Public wheel compatibility is Python 3.11 and 3.12; the managed controller
  will run Python 3.12 and the managed CP3 worker will run Python 3.11.
- Final published metadata is exactly `Requires-Python >=3.11,<3.13`.
- CP4 will be exactly `4.2.1.1`; CP3 will be exactly `3.1.1.3`.
- Final controller FastMCP is a hashed, explicitly upper-bounded stable 3.x
  release; final CP4/CP3 worker locks contain hashes and no model weights are
  bundled.
- Final metadata has no floating Cellpose range. This repository-only
  foundation temporarily preserves the legacy `fastmcp>=2.10.3,<3` and
  `cellpose>=3.0.0` lines so the current entrypoint is not broken before its
  tested proxy replacement; no intermediate artifact is published, and
  Phase 4 removes that exception.
- `cpsam_v2` is the default; `cpsam` is the other core CP4 built-in model.
- DINO and Zarr remain absent unless their independent full gates pass.
- MCP is canonical; the setup/doctor CLI and Codex skill support it, and there
  is no separate AI agent.
- Inputs are immutable and supported output writes are confined to managed run
  directories beneath approved roots.
- Workers are trusted same-user processes, not operating-system sandboxes.
- There is no telemetry or assistant-accessible general code execution.
  Hash-bound trusted-checkpoint import is a future explicit CLI-only exception.
- All 13 workflow tools are release-blocking core surface.
- No stable release occurs between internal gates.
- Work remains on `codex/cellpose-local-first`.
- Existing modified/untracked work belongs to the user. No broad add, cleanup,
  reset, checkout, move, deletion, or overwrite is permitted.
- Git-ignored caches/builds are outside this initial report and cannot be
  deleted or cleaned. Phase 12 inventories any ignored cleanup candidate
  separately before presenting an exact removal list.
- Existing dirty `pyproject.toml` and `.github/workflows/ci.yml` are staged by
  hunk only; their pre-existing CLI/install-test changes stay in the worktree.
- The current MCP entrypoint, tool registrations, scientific operations,
  demos, results, training data, and uncertain experiments are not changed.
- Ruff verification always uses `--no-fix`.

---

## File map

### Create

| Path | Responsibility |
| --- | --- |
| `scripts/inventory_worktree.py` | Read-only Git/worktree hashing and safe atomic inventory output |
| `tests/dev/test_inventory_worktree.py` | Real temporary-repository inventory tests |
| `tests/packaging/test_python_policy.py` | Python, dependency, tool, and package-data policy |
| `src/cellpose_mcp/release/__init__.py` | Export bootstrap release-ledger contracts |
| `src/cellpose_mcp/release/feature_manifest.py` | Strict schema and deliberately blocked release gate |
| `src/cellpose_mcp/features.toml` | Packaged bootstrap ledger with unresolved core matrix |
| `scripts/check_feature_manifest.py` | Development/release ledger command |
| `tests/contract/test_feature_manifest.py` | Bootstrap ledger cannot falsely become releasable |
| `tests/packaging/test_distribution_contents.py` | Clean-clone wheel/sdist and installed-metadata proof |
| `uv.lock` | Locked transitional root development environment |

### Modify

| Path | Exact scope |
| --- | --- |
| `.gitignore` | Add root-only `/local_archive/` after the first real inventory exists |
| `.python-version` | Change `3.10` to `3.12` |
| `pyproject.toml` | Python range/classifiers, Pydantic/build dependencies, package data, tool targets, Ruff `fix = false`; stage only these hunks |
| `MANIFEST.in` | Replace broad discovery with a true allowlist |
| `.github/workflows/ci.yml` | Locked uv foundation checks on 3.11/3.12; stage only these hunks |

### Do not modify

- `src/cellpose_mcp/tools.py`
- `src/cellpose_mcp/operations.py`
- `src/cellpose_mcp/server.py`
- `src/cellpose_mcp/mcp_instance.py`
- `src/cellpose_mcp/cli/app.py`
- `src/cellpose_mcp/cli/install.py`
- Existing tests outside the paths above
- Any demo, result, training, checkpoint, or experiment path

## Phase interface

This phase produces these exact callable contracts:

```text
build_inventory(repo: pathlib.Path) -> dict[str, object]
resolve_output(repo: pathlib.Path, supplied: str | None) -> pathlib.Path
write_new_atomic(path: pathlib.Path, document: dict[str, object]) -> None

load_feature_manifest(path: pathlib.Path | None = None) -> BootstrapFeatureManifest
release_gate_failures(
    manifest: BootstrapFeatureManifest,
) -> tuple[GateFailure, ...]
assert_release_ready(manifest: BootstrapFeatureManifest) -> None
```

The next plan replaces bootstrap manifest schema version 1 only after pinned
upstream probes define the complete required capability matrix. Schema version
1 rejects every stable feature record and can never pass release mode.

### Task 0: Verify the execution environment without changing the repository

**Files:** No repository files. A versioned execution copy is created only at
`/private/tmp/cellpose-mcp-foundation-uv-0.10.4`.

**Interfaces:**

- Consumes: current Git index, `python3`, and optional `uv`.
- Produces: empty staged index, a path-stable temporary execution copy of uv
  exactly `0.10.4`, and available controlled Python 3.11/3.12 interpreters
  before Task 1 writes a repository file.

- [ ] **Step 1: Prove the user has no pre-staged work**

Run:

```bash
git diff --cached --quiet
git diff --cached --name-only
```

Expected: the first command exits 0 and the second prints nothing. If either
condition fails, stop and ask the user how to preserve the staged work; do not
unstage or combine it automatically.

- [ ] **Step 2a: Verify or bootstrap exact uv**

Run:

```bash
UV_SOURCE="$(command -v uv)"
python3 -c 'import subprocess,sys; assert subprocess.check_output([sys.argv[1],"--version"],text=True).startswith("uv 0.10.4 ")' "$UV_SOURCE"
```

Expected: both commands exit 0. If `uv` is absent, request dependency-install
approval, run:

```bash
python3 -m pip install --user "uv==0.10.4"
UV_SOURCE="$(python3 -c 'import site; from pathlib import Path; print(Path(site.USER_BASE) / "bin" / "uv")')"
python3 -c 'import subprocess,sys; assert subprocess.check_output([sys.argv[1],"--version"],text=True).startswith("uv 0.10.4 ")' "$UV_SOURCE"
```

The recovery block verifies that absolute `UV_SOURCE`. A different uv version
is a blocker until exact `0.10.4` is installed.

- [ ] **Step 2b: Create one path-stable uv runner outside the repository**

Run:

```bash
UV_SOURCE="$(python3 -c 'import shutil,site,subprocess; from pathlib import Path; candidates=[shutil.which("uv"),str(Path(site.USER_BASE) / "bin" / "uv")]; matches=[str(Path(candidate).resolve()) for candidate in candidates if candidate and Path(candidate).is_file() and subprocess.run([candidate,"--version"],check=False,capture_output=True,text=True).stdout.startswith("uv 0.10.4 ")]; assert matches, "exact uv 0.10.4 was not found"; print(matches[0])')"
UV_RUNNER=/private/tmp/cellpose-mcp-foundation-uv-0.10.4
if [ -e "$UV_RUNNER" ] || [ -L "$UV_RUNNER" ]; then
  python3 -c 'import os,stat,sys; info=os.lstat(sys.argv[1]); assert stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode); assert info.st_uid == os.getuid(); assert stat.S_IMODE(info.st_mode) == 0o700' "$UV_RUNNER"
else
  cp "$UV_SOURCE" "$UV_RUNNER"
  chmod 700 "$UV_RUNNER"
fi
python3 -c 'import subprocess,sys; version=subprocess.check_output([sys.argv[1],"--version"],text=True); assert version.startswith("uv 0.10.4 "); print(version,end="")' "$UV_RUNNER"
```

Expected: the final command prints `uv 0.10.4 (...)`. An existing path is
accepted only when it is a regular, non-symlinked, user-owned mode-`0700` file
that reports exact `0.10.4`; any assertion/version failure stops the plan and
requires review before that path is replaced. Every later local command uses
this absolute runner, so no later task depends on a transient `PATH` export.
If the execution sandbox denies uv's default cache, prefix the exact command
with `UV_CACHE_DIR=/private/tmp/cellpose-mcp-foundation-uv-cache`; this changes
no repository file.

- [ ] **Step 3: Verify or install controlled Python 3.11 and 3.12 without implicit downloads**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python find --no-python-downloads 3.11
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python find --no-python-downloads 3.12
```

Expected: each command prints an absolute interpreter path. If either is
absent, request dependency-download approval, run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python install 3.11 3.12
```

Then repeat both `python find --no-python-downloads` commands. Tasks 1–2 use
controlled Python 3.12 through `uv run --no-project`; no foundation test uses
host Python 3.13.

### Task 1: Build a read-only Git/worktree inventory core

**Files:**

- Create: `scripts/inventory_worktree.py`
- Create: `tests/dev/test_inventory_worktree.py`

**Interfaces:**

- Consumes: a Git worktree with a committed `HEAD`.
- Produces exact signatures:

```text
git_output(repo: pathlib.Path, *args: str) -> bytes
index_entries(repo: pathlib.Path) -> dict[str, str]
changed_paths(repo: pathlib.Path) -> dict[str, str]
hash_regular_stable(path: pathlib.Path) -> tuple[int, str]
build_inventory(repo: pathlib.Path) -> dict[str, object]
```

- Produces: `build_inventory(repo)` with path-sorted entries containing
  category, porcelain status, kind, worktree size/hash, and index-blob SHA-256.
- Safety: uses `GIT_OPTIONAL_LOCKS=0`, verifies the Git index bytes/stat did not
  change, never follows symlinks, and aborts if a regular file changes or its
  path is replaced while hashing.

- [ ] **Step 1a: Create the test imports and repository helpers**

Create `tests/dev/test_inventory_worktree.py` with:

```python
# ruff: noqa: S603

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts" / "inventory_worktree.py"
GIT = shutil.which("git")
if GIT is None:
    raise RuntimeError("Git is required for inventory tests")


def load_inventory_module():
    spec = importlib.util.spec_from_file_location("inventory_worktree", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load inventory script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        [GIT, "--no-optional-locks", "-C", str(repo), *args],
        check=True,
        capture_output=True,
    )


def create_dirty_repo(base: Path) -> Path:
    repo = base / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "inventory@example.invalid")
    git(repo, "config", "user.name", "Inventory Test")
    fixtures = {
        ".gitignore": b"/local_archive/\n",
        "clean.txt": b"clean\n",
        "modified.txt": b"before\n",
        "deleted.txt": b"deleted\n",
    }
    for relative, content in fixtures.items():
        (repo / relative).write_bytes(content)
    git(repo, "add", *fixtures)
    git(repo, "commit", "-m", "fixture")
    (repo / "modified.txt").write_bytes(b"after\n")
    (repo / "deleted.txt").unlink()
    (repo / "untracked.bin").write_bytes(b"\x00\x01\x02")
    (repo / "link").symlink_to("clean.txt")
    return repo
```

- [ ] **Step 1b: Add the worktree/index hash test**

Append:

```python


class InventoryCoreTests(unittest.TestCase):
    def test_build_inventory_records_worktree_and_index_hashes(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            repo = create_dirty_repo(Path(temporary))
            index = repo / ".git" / "index"
            index_before = (
                index.read_bytes(),
                index.stat().st_mtime_ns,
                index.stat().st_size,
            )
            document = inventory.build_inventory(repo)
            index_after = (
                index.read_bytes(),
                index.stat().st_mtime_ns,
                index.stat().st_size,
            )
            self.assertEqual(index_after, index_before)

            entries = {
                entry["path"]: entry
                for entry in document["entries"]
            }
            clean_hash = hashlib.sha256(b"clean\n").hexdigest()
            before_hash = hashlib.sha256(b"before\n").hexdigest()
            after_hash = hashlib.sha256(b"after\n").hexdigest()
            deleted_hash = hashlib.sha256(b"deleted\n").hexdigest()
            self.assertEqual(entries["clean.txt"]["category"], "tracked")
            self.assertEqual(entries["clean.txt"]["worktree_sha256"], clean_hash)
            self.assertEqual(entries["clean.txt"]["index_sha256"], clean_hash)
            self.assertEqual(entries["modified.txt"]["category"], "modified")
            self.assertEqual(
                entries["modified.txt"]["worktree_sha256"],
                after_hash,
            )
            self.assertEqual(
                entries["modified.txt"]["index_sha256"],
                before_hash,
            )
            self.assertEqual(entries["deleted.txt"]["kind"], "missing")
            self.assertIsNone(entries["deleted.txt"]["worktree_sha256"])
            self.assertEqual(
                entries["deleted.txt"]["index_sha256"],
                deleted_hash,
            )
            self.assertEqual(entries["untracked.bin"]["category"], "untracked")
            self.assertIsNone(entries["untracked.bin"]["index_sha256"])
            self.assertEqual(entries["link"]["kind"], "symlink")
            self.assertEqual(
                entries["link"]["worktree_sha256"],
                hashlib.sha256(b"clean.txt").hexdigest(),
            )
            self.assertEqual(
                document["totals"],
                {"modified": 2, "tracked": 2, "untracked": 2},
            )
```

- [ ] **Step 1c: Add the concurrent-change test and test runner**

Append the second method to `InventoryCoreTests`, then append the runner after
the class:

```python

    def test_hashing_aborts_when_a_regular_file_changes(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "changing.bin"
            path.write_bytes(b"content")
            with (
                mock.patch.object(
                    inventory,
                    "file_identity",
                    side_effect=[
                        (1, 2, 7, 10, stat.S_IFREG),
                        (1, 2, 7, 10, stat.S_IFREG),
                        (1, 3, 8, 11, stat.S_IFREG),
                    ],
                ),
                self.assertRaisesRegex(
                    RuntimeError,
                    "changed while it was being hashed",
                ),
            ):
                inventory.hash_regular_stable(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify the script is absent**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 python tests/dev/test_inventory_worktree.py
```

Expected: ERROR because `scripts/inventory_worktree.py` does not exist.

- [ ] **Step 3a: Create the inventory types and Git parsers**

Create `scripts/inventory_worktree.py` with:

```python
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
```

- [ ] **Step 3b: Add stable worktree and index hashing**

Append:

```python


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
```

- [ ] **Step 3c: Add deterministic document assembly**

Append:

```python


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
```

- [ ] **Step 4: Run the core tests**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 python tests/dev/test_inventory_worktree.py
```

Expected: `Ran 2 tests` and `OK`.

- [ ] **Step 5: Commit only the two new files**

```bash
git add scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py
git diff --cached --check
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={"scripts/inventory_worktree.py","tests/dev/test_inventory_worktree.py"}; assert actual == expected, sorted(actual)'
git commit -m "chore: add read-only worktree inventory core"
```

This commit adds new files only; it does not stage any pre-existing dirty path.

### Task 2: Add safe inventory output and capture the real baseline

**Files:**

- Modify: `scripts/inventory_worktree.py`
- Modify: `tests/dev/test_inventory_worktree.py`
- Modify: `.gitignore`

**Interfaces:**

- Consumes: `build_inventory(repo)` from Task 1.
- Produces exact signatures:

```text
resolve_output(
    repo: pathlib.Path,
    supplied: str | None,
) -> pathlib.Path
write_new_atomic(
    path: pathlib.Path,
    document: dict[str, object],
) -> None
main() -> int
```

- Produces: `resolve_output`, `write_new_atomic`, and a CLI that writes exactly
  one new mode-`0600` JSON file under a real, non-symlinked
  `local_archive/`.
- Refuses: output outside the archive, archive symlinks, existing destinations,
  non-root repository paths, and invalid repositories.

- [ ] **Step 1a: Add the atomic-output CLI test**

Insert `import json` immediately after `import importlib.util`, then append this
method to `InventoryCoreTests`:

```python
import json
```

```python

    def test_cli_writes_once_without_changing_fixture_or_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = create_dirty_repo(Path(temporary))
            index = repo / ".git" / "index"
            index_before = (
                index.read_bytes(),
                index.stat().st_mtime_ns,
                index.stat().st_size,
            )
            before = {
                "clean.txt": (repo / "clean.txt").read_bytes(),
                "modified.txt": (repo / "modified.txt").read_bytes(),
                "untracked.bin": (repo / "untracked.bin").read_bytes(),
                "link": os.readlink(repo / "link"),
            }
            command = [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(repo),
                "--output",
                "local_archive/inventory.json",
            ]
            first = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            output = repo / "local_archive" / "inventory.json"
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            document = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(document["schema_version"], 1)
            self.assertNotIn(
                "local_archive/inventory.json",
                {entry["path"] for entry in document["entries"]},
            )
            self.assertEqual((repo / "clean.txt").read_bytes(), before["clean.txt"])
            self.assertEqual(
                (repo / "modified.txt").read_bytes(),
                before["modified.txt"],
            )
            self.assertEqual(
                (repo / "untracked.bin").read_bytes(),
                before["untracked.bin"],
            )
            self.assertEqual(os.readlink(repo / "link"), before["link"])
            self.assertEqual(
                (
                    index.read_bytes(),
                    index.stat().st_mtime_ns,
                    index.stat().st_size,
                ),
                index_before,
            )

            second = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 2)
            self.assertIn("refusing to overwrite inventory", second.stderr)

            outside = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--output",
                    "outside.json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(outside.returncode, 2)
            self.assertIn("must be inside local_archive", outside.stderr)
            self.assertFalse((repo / "outside.json").exists())
```

- [ ] **Step 1b: Add the symlinked-archive CLI test**

Append this method to `InventoryCoreTests` before the test runner:

```python

    def test_cli_refuses_a_symlinked_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo = base / "repo"
            outside = base / "outside"
            repo.mkdir()
            outside.mkdir()
            git(repo, "init")
            (repo / "local_archive").symlink_to(
                outside,
                target_is_directory=True,
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--output",
                    "local_archive/inventory.json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn(
                "local_archive must not be a symbolic link",
                completed.stderr,
            )
            self.assertFalse((outside / "inventory.json").exists())
```

- [ ] **Step 1c: Add the default-output CLI test**

Append this method to `InventoryCoreTests` before the test runner:

```python

    def test_cli_creates_default_timestamped_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = create_dirty_repo(Path(temporary))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            reports = list(
                (repo / "local_archive").glob(
                    "worktree-inventory-*.json"
                )
            )
            self.assertEqual(len(reports), 1)
            document = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertEqual(document["schema_version"], 1)
```

- [ ] **Step 1d: Add the repository-root boundary test**

Append this method to `InventoryCoreTests` before the test runner:

```python

    def test_cli_refuses_nested_repository_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = create_dirty_repo(Path(temporary))
            nested = repo / "nested"
            nested.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(nested),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn(
                "--repo must be the Git worktree root",
                completed.stderr,
            )
            self.assertFalse((nested / "local_archive").exists())
```

- [ ] **Step 1e: Add the invalid-repository boundary test**

Append this method to `InventoryCoreTests` before the test runner:

```python

    def test_cli_refuses_non_git_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(directory),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("rev-parse", completed.stderr)
            self.assertFalse((directory / "local_archive").exists())
```

- [ ] **Step 2: Run the expanded tests and verify the CLI is absent**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 python tests/dev/test_inventory_worktree.py
```

Expected: `Ran 7 tests` followed by
`FAILED (failures=4, errors=1)`: the output file is missing in the first CLI
test, while the other four CLI tests demonstrate that default generation and
the three refusal boundaries are not implemented yet.

- [ ] **Step 3a: Add the sorted imports and output resolver**

Replace the standard-library import block in
`scripts/inventory_worktree.py` with this complete sorted block:

```python
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
```

Append:

```python


def resolve_output(repo: Path, supplied: str | None) -> Path:
    """Resolve one new output strictly beneath a non-symlinked archive."""
    archive_path = repo / "local_archive"
    if archive_path.is_symlink():
        raise ValueError("local_archive must not be a symbolic link")
    archive = archive_path.resolve(strict=False)
    if supplied is None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        candidate = archive / f"worktree-inventory-{stamp}.json"
    else:
        raw = Path(supplied)
        candidate = (
            raw if raw.is_absolute() else repo / raw
        ).resolve(strict=False)
    if candidate == archive or not candidate.is_relative_to(archive):
        raise ValueError("inventory output must be inside local_archive")
    if candidate.exists() or candidate.is_symlink():
        raise FileExistsError(f"refusing to overwrite inventory: {candidate}")
    return candidate
```

- [ ] **Step 3b: Add the no-overwrite atomic writer**

Append:

```python


def write_new_atomic(path: Path, document: dict[str, object]) -> None:
    """Atomically link a complete mode-0600 file without overwriting."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".inventory-",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(document, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        temporary.unlink()
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()
```

- [ ] **Step 3c: Add argument parsing and deterministic exit behavior**

Append:

```python


def main() -> int:
    """Inventory one repository and write one new local report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        repo = args.repo.expanduser().resolve(strict=True)
        top_level = Path(
            decode_path(
                git_output(repo, "rev-parse", "--show-toplevel").rstrip(b"\n")
            )
        ).resolve(strict=True)
        if top_level != repo:
            raise ValueError("--repo must be the Git worktree root")
        output = resolve_output(repo, args.output)
        document = build_inventory(repo)
        write_new_atomic(output, document)
    except (
        OSError,
        RuntimeError,
        subprocess.CalledProcessError,
        ValueError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"inventory written to {output.relative_to(repo)}: {document['totals']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run all inventory tests**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 python tests/dev/test_inventory_worktree.py
```

Expected: `Ran 7 tests` and `OK`.

- [ ] **Step 5: Capture the real worktree before editing existing files**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 python scripts/inventory_worktree.py
```

Expected: exit 0 and a new
`local_archive/worktree-inventory-<timestamp>.json`. The report includes every
tracked, modified, and non-ignored untracked path plus the plan-owned inventory
files; it precedes changes to `pyproject.toml`, CI, Python policy, or packaging.
It does not authorize any operation on ignored paths.

Inspect only the summary and path metadata, not user file contents:

```bash
git status --short
python3 -c 'import glob,json; p=sorted(glob.glob("local_archive/worktree-inventory-*.json"))[-1]; d=json.load(open(p)); print(d["commit"], d["totals"], len(d["entries"]))'
```

Expected: all pre-existing paths remain and the report has a 40-character
commit ID, category totals, and a nonzero entry count.

- [ ] **Step 6: Ignore the archive and mark the script executable**

Append to `.gitignore`:

```gitignore
# Local preservation and inventory reports
/local_archive/
```

Run:

```bash
chmod +x scripts/inventory_worktree.py
git status --short --ignored local_archive
```

Expected: `local_archive/` is ignored; no report is staged.

- [ ] **Step 7: Commit only inventory-owned files**

```bash
git add .gitignore scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py
git diff --cached --check
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={".gitignore","scripts/inventory_worktree.py","tests/dev/test_inventory_worktree.py"}; assert actual == expected, sorted(actual)'
git commit -m "chore: persist safe worktree inventories"
```

Expected: the commit contains only the three listed paths. No existing user
source, test, result, or configuration hunk is staged.

### Task 3: Lock Python policy and the transitional development environment

**Files:**

- Create: `tests/packaging/test_python_policy.py`
- Create: `uv.lock`
- Modify: `.python-version`
- Modify by hunk only: `pyproject.toml`

**Interfaces:**

- Consumes: the real inventory from Task 2.
- Produces no Python API. Later tasks consume these exact committed metadata
  keys: `project.requires-python`, `project.dependencies`,
  `project.optional-dependencies.test`, `tool.setuptools.package-data`,
  `tool.ruff.target-version`, `tool.ruff.fix`,
  `tool.black.target-version`, and `tool.mypy.python_version`, plus `uv.lock`.
- Produces: public Python `>=3.11,<3.13`, Python 3.12 development default,
  direct Pydantic/build dependencies, explicit package data, non-mutating Ruff,
  and a checked root development lock.
- Transitional constraint: the current base FastMCP/Cellpose dependency ranges
  remain until the Phase 4 proxy replaces the legacy entrypoint. No artifact
  from this intermediate phase is published.

- [ ] **Step 1: Write the failing policy contract**

Create `tests/packaging/test_python_policy.py`:

```python
from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[2]


def config() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_public_python_range_and_classifiers_are_exact() -> None:
    project = config()["project"]
    assert isinstance(project, dict)
    assert project["requires-python"] == ">=3.11,<3.13"
    classifiers = project["classifiers"]
    assert "Operating System :: MacOS" in classifiers
    assert "Operating System :: OS Independent" not in classifiers
    assert "Programming Language :: Python :: 3.10" not in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert "Programming Language :: Python :: 3.12" in classifiers


def test_foundation_dependencies_are_direct() -> None:
    project = config()["project"]
    assert isinstance(project, dict)
    assert "pydantic>=2.11,<3" in project["dependencies"]
    optional = project["optional-dependencies"]
    assert isinstance(optional, dict)
    assert "build>=1.2,<2" in optional["test"]


def test_package_data_contains_only_current_foundation_assets() -> None:
    package_data = config()["tool"]["setuptools"].get("package-data")
    assert package_data == {
        "cellpose_mcp": ["features.toml", "py.typed"],
    }


def test_static_tools_target_python_311_without_mutating_checks() -> None:
    tools = config()["tool"]
    assert tools["ruff"]["target-version"] == "py311"
    assert tools["ruff"]["fix"] is False
    assert "TC003" in tools["ruff"]["lint"]["ignore"]
    assert "TCH003" not in tools["ruff"]["lint"]["ignore"]
    assert tools["black"]["target-version"] == ["py311", "py312"]
    assert tools["mypy"]["python_version"] == "3.11"


def test_development_python_is_312() -> None:
    assert (ROOT / ".python-version").read_text(encoding="utf-8") == "3.12\n"
```

- [ ] **Step 2: Run the policy contract and verify it fails**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 --with "pytest>=8.4,<9" pytest tests/packaging/test_python_policy.py -q
```

Expected: `5 failed`. The isolated command supplies its own bounded pytest and
does not resolve the project or assume a host test runner.

- [ ] **Step 3: Apply only the approved metadata changes**

Preserve every unrelated existing `pyproject.toml` hunk. Change the exact
values below:

```toml
[project]
requires-python = ">=3.11,<3.13"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: MacOS",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Image Processing",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    "fastmcp>=2.10.3,<3",
    "cellpose>=3.0.0",
    "numpy>=1.26.0",
    "imageio>=2.34.0",
    "tifffile>=2021.0.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pydantic>=2.11,<3",
]

[project.optional-dependencies]
test = [
    "pytest>=8.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "pytest-timeout>=2.2.0",
    "pytest-mock>=3.12.0",
    "build>=1.2,<2",
]

[tool.setuptools.package-data]
cellpose_mcp = ["features.toml", "py.typed"]

[tool.ruff]
target-version = "py311"
fix = false

[tool.black]
target-version = ["py311", "py312"]

[tool.mypy]
python_version = "3.11"
```

In `[tool.ruff.lint].ignore`, replace `"TCH003"` with `"TC003"`.

Set `.python-version` to:

```text
3.12
```

- [ ] **Step 4a: Verify the exact uv bootstrap and both interpreters**

Run:

```bash
python3 -c 'import subprocess; assert subprocess.check_output(["/private/tmp/cellpose-mcp-foundation-uv-0.10.4","--version"],text=True).startswith("uv 0.10.4 ")'
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python find --no-python-downloads 3.11
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python find --no-python-downloads 3.12
```

Expected: the version assertion exits 0 and each
`python find --no-python-downloads` command prints one absolute interpreter
path without mutating interpreter state. If either interpreter is absent,
request dependency-download approval, run
`/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python install 3.11 3.12`,
and repeat all three checks before continuing.

- [ ] **Step 4b: Resolve and sync the locked environment**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 lock --python 3.12
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 lock --check
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 sync --locked --python 3.12 --extra test --extra dev
```

Expected: uv 0.10.4 exits 0, creates `uv.lock`, and synchronizes all test/dev
tools without changing the selected dependency solution afterward.

- [ ] **Step 5: Run the policy tests on both public Python versions**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.11 --extra test --extra dev pytest tests/packaging/test_python_policy.py -q
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/packaging/test_python_policy.py -q
```

Expected: `5 passed` on Python 3.11 and `5 passed` on Python 3.12.

- [ ] **Step 6: Run non-mutating static checks on inventory code**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev ruff check --no-fix scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py tests/packaging/test_python_policy.py
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev mypy scripts/inventory_worktree.py
```

Expected: Ruff and mypy exit 0 without modifying any file.

- [ ] **Step 7: Stage the dirty metadata by hunk, never by whole file**

Stage the clean/new paths normally:

```bash
git add .python-version tests/packaging/test_python_policy.py uv.lock
```

Stage `pyproject.toml` interactively:

```bash
git add -p pyproject.toml
```

Select only the Python range/classifier, Pydantic/build, package-data, Ruff
target/fix/`TC003`, Black target, and mypy target hunks from Step 3. Split a
combined hunk before selecting it. If Git cannot split adjacent planned and
user-owned lines, choose `e` to edit only the proposed index patch and remove
the user-owned `+`/`-` lines before applying it; do not edit the working file.
Do not stage the pre-existing description, keyword, `cellpose-mcp-cli`,
napari-plugin, `install_e2e`, or `cli/app.py`-ignore additions.

Verify the cached patch mechanically:

```bash
python3 -c 'import subprocess; d=subprocess.check_output(["git","diff","--cached","--","pyproject.toml"],text=True); required=[">=3.11,<3.13","pydantic>=2.11,<3","build>=1.2,<2","package-data","fix = false","TC003"]; forbidden=["MCP server and CLI","cellpose-mcp-cli","no:napari","install_e2e","src/cellpose_mcp/cli/app.py"]; assert all(x in d for x in required); assert all(x not in d for x in forbidden)'
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={".python-version","pyproject.toml","tests/packaging/test_python_policy.py","uv.lock"}; assert actual == expected, sorted(actual)'
git diff --cached --check
```

Expected: both commands exit 0. If the assertion fails, unstage only
`pyproject.toml` and repeat hunk selection; do not commit a mixed patch.

- [ ] **Step 8: Commit and prove the user hunks remain**

```bash
git commit -m "build: lock repository foundation environment"
```

Verify the pre-existing working changes are still outside the commit:

```bash
python3 -c 'import subprocess; d=subprocess.check_output(["git","diff","HEAD","--","pyproject.toml"],text=True); expected=["MCP server and CLI","cellpose-mcp-cli","no:napari","install_e2e","src/cellpose_mcp/cli/app.py"]; assert all(x in d for x in expected)'
```

Expected: exit 0. The clean committed tree has the foundation policy, while
the user’s paired untracked CLI/install work remains preserved in the working
tree.

### Task 4: Add an explicitly blocked bootstrap feature ledger

**Files:**

- Create: `src/cellpose_mcp/release/__init__.py`
- Create: `src/cellpose_mcp/release/feature_manifest.py`
- Create: `src/cellpose_mcp/features.toml`
- Create: `scripts/check_feature_manifest.py`
- Create: `tests/contract/test_feature_manifest.py`

**Interfaces:**

- Consumes: Pydantic and package-data declaration from Task 3.
- Produces exact fields/signatures:

```text
BootstrapFeatureManifest(
    schema_version: Literal[1],
    target_release: Literal["0.2.0"],
    release_blockers: tuple[
        Literal["core_capability_matrix_unresolved"],
        ...,
    ],
    required_core_tools: tuple[str, ...],
    stable_features: tuple[dict[str, object], ...],
)
load_feature_manifest(
    path: pathlib.Path | None = None,
) -> BootstrapFeatureManifest
release_gate_failures(
    manifest: BootstrapFeatureManifest,
) -> tuple[GateFailure, ...]
assert_release_ready(manifest: BootstrapFeatureManifest) -> None
```

- Produces: strict bootstrap schema version 1 and deterministic development/
  release checks.
- Safety invariant: schema version 1 requires
  `core_capability_matrix_unresolved`, requires the exact 13 tool names, rejects
  every `stable_features` entry, and therefore cannot be tricked into release
  readiness with fabricated evidence strings.

- [ ] **Step 1a: Create the manifest fixture and structural tests**

Create `tests/contract/test_feature_manifest.py` with:

```python
# ruff: noqa: S603

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from cellpose_mcp.release.feature_manifest import (
    BOOTSTRAP_BLOCKER,
    CORE_TOOLS,
    BootstrapFeatureManifest,
    FeatureBootstrapGateError,
    assert_release_ready,
    load_feature_manifest,
    release_gate_failures,
)
from pydantic import ValidationError

ROOT = Path(__file__).parents[2]


def valid_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "target_release": "0.2.0",
        "release_blockers": [BOOTSTRAP_BLOCKER],
        "required_core_tools": list(CORE_TOOLS),
        "stable_features": [],
    }


def test_packaged_bootstrap_manifest_is_structurally_valid() -> None:
    manifest = load_feature_manifest()
    assert manifest.schema_version == 1
    assert manifest.target_release == "0.2.0"
    assert manifest.release_blockers == (BOOTSTRAP_BLOCKER,)
    assert manifest.required_core_tools == CORE_TOOLS
    assert manifest.stable_features == ()


def test_unknown_manifest_field_is_rejected() -> None:
    data = valid_data()
    data["invented"] = True
    with pytest.raises(ValidationError, match="extra_forbidden"):
        BootstrapFeatureManifest.model_validate(data)


def test_core_tool_sequence_cannot_shrink() -> None:
    data = valid_data()
    data["required_core_tools"] = list(CORE_TOOLS[:-1])
    with pytest.raises(ValidationError, match="approved 13-tool sequence"):
        BootstrapFeatureManifest.model_validate(data)
```

- [ ] **Step 1b: Add the premature-promotion and release-block tests**

Append:

```python


def test_bootstrap_schema_rejects_fabricated_stable_features() -> None:
    data = valid_data()
    data["stable_features"] = [
        {
            "feature_id": "fake.segment",
            "tool": "segment",
            "evidence": ["tests/fake.py::test_fake"],
        }
    ]
    with pytest.raises(
        ValidationError,
        match="schema version 1 forbids stable feature records",
    ):
        BootstrapFeatureManifest.model_validate(data)


def test_release_gate_is_blocked_by_matrix_and_every_core_tool() -> None:
    manifest = load_feature_manifest()
    failures = release_gate_failures(manifest)
    assert len(failures) == 14
    assert failures[0].code == "unresolved_core_matrix"
    assert failures[0].subject == BOOTSTRAP_BLOCKER
    assert {failure.subject for failure in failures[1:]} == set(CORE_TOOLS)
    assert {failure.code for failure in failures[1:]} == {"missing_stable_tool"}
    with pytest.raises(FeatureBootstrapGateError) as caught:
        assert_release_ready(manifest)
    assert caught.value.failures == failures
```

- [ ] **Step 1c: Add the development/release command test**

Append:

```python


def test_check_command_distinguishes_development_and_release() -> None:
    development = subprocess.run(
        [sys.executable, "scripts/check_feature_manifest.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert development.returncode == 0
    assert "bootstrap manifest valid; release blockers: 14" in development.stdout

    release = subprocess.run(
        [sys.executable, "scripts/check_feature_manifest.py", "--release"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert release.returncode == 1
    assert "unresolved_core_matrix" in release.stdout
    assert release.stdout.count("missing_stable_tool") == 13
```

- [ ] **Step 2: Run the contract and verify the module is absent**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/contract/test_feature_manifest.py -q
```

Expected: collection ERROR because `cellpose_mcp.release` does not exist.

- [ ] **Step 3a: Implement the manifest schema and validators**

Create `src/cellpose_mcp/release/feature_manifest.py`:

```python
"""Bootstrap feature ledger that cannot authorize a release."""

from __future__ import annotations

import tomllib
from importlib.resources import files
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

CORE_TOOLS = (
    "get_capabilities",
    "inspect_image",
    "list_models",
    "prepare_model",
    "segment",
    "refine_segmentation",
    "measure_masks",
    "evaluate_segmentation",
    "export_segmentation",
    "train_model",
    "restore_image",
    "get_job",
    "cancel_job",
)
BOOTSTRAP_BLOCKER = "core_capability_matrix_unresolved"


class BootstrapFeatureManifest(BaseModel):
    """Schema used only until pinned upstream probes resolve feature granularity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    target_release: Literal["0.2.0"]
    release_blockers: tuple[Literal["core_capability_matrix_unresolved"], ...]
    required_core_tools: tuple[str, ...]
    stable_features: tuple[dict[str, object], ...] = ()

    @model_validator(mode="after")
    def enforce_bootstrap_block(self) -> Self:
        """Prevent core shrinkage or premature stable records."""
        if self.release_blockers != (BOOTSTRAP_BLOCKER,):
            raise ValueError("bootstrap blocker must remain active")
        if self.required_core_tools != CORE_TOOLS:
            raise ValueError("required_core_tools must match approved 13-tool sequence")
        if self.stable_features:
            raise ValueError("schema version 1 forbids stable feature records")
        return self


class GateFailure(BaseModel):
    """One deterministic reason the bootstrap ledger cannot ship."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: Literal["unresolved_core_matrix", "missing_stable_tool"]
    subject: str
    message: str
```

- [ ] **Step 3b: Implement deterministic failure reporting**

Append:

```python


class FeatureBootstrapGateError(RuntimeError):
    """Raised whenever release mode is attempted during bootstrap."""

    def __init__(self, failures: tuple[GateFailure, ...]) -> None:
        """Retain every failure in deterministic order."""
        self.failures = failures
        summary = "; ".join(
            f"{failure.code}:{failure.subject}" for failure in failures
        )
        super().__init__(f"bootstrap feature manifest blocks release: {summary}")


def load_feature_manifest(
    path: Path | None = None,
) -> BootstrapFeatureManifest:
    """Load the packaged bootstrap ledger or an explicit test file."""
    if path is None:
        content = files("cellpose_mcp").joinpath("features.toml").read_text(
            encoding="utf-8"
        )
    else:
        content = path.read_text(encoding="utf-8")
    return BootstrapFeatureManifest.model_validate(tomllib.loads(content))


def release_gate_failures(
    manifest: BootstrapFeatureManifest,
) -> tuple[GateFailure, ...]:
    """Return the matrix blocker followed by all missing core tools."""
    failures = [
        GateFailure(
            code="unresolved_core_matrix",
            subject=manifest.release_blockers[0],
            message="Pinned CP4/CP3 probes have not resolved the core matrix.",
        )
    ]
    failures.extend(
        GateFailure(
            code="missing_stable_tool",
            subject=tool,
            message=f"{tool} has no stable feature record.",
        )
        for tool in manifest.required_core_tools
    )
    return tuple(failures)


def assert_release_ready(manifest: BootstrapFeatureManifest) -> None:
    """Always raise for bootstrap schema version 1."""
    raise FeatureBootstrapGateError(release_gate_failures(manifest))
```

- [ ] **Step 3c: Export the complete release-ledger API**

Create `src/cellpose_mcp/release/__init__.py`:

```python
"""Release evidence contracts for Cellpose MCP."""

from cellpose_mcp.release.feature_manifest import (
    BOOTSTRAP_BLOCKER,
    CORE_TOOLS,
    BootstrapFeatureManifest,
    FeatureBootstrapGateError,
    GateFailure,
    assert_release_ready,
    load_feature_manifest,
    release_gate_failures,
)

__all__ = [
    "BOOTSTRAP_BLOCKER",
    "CORE_TOOLS",
    "BootstrapFeatureManifest",
    "FeatureBootstrapGateError",
    "GateFailure",
    "assert_release_ready",
    "load_feature_manifest",
    "release_gate_failures",
]
```

- [ ] **Step 3d: Add the packaged blocked ledger**

Create `src/cellpose_mcp/features.toml`:

```toml
schema_version = 1
target_release = "0.2.0"
release_blockers = ["core_capability_matrix_unresolved"]
required_core_tools = [
  "get_capabilities",
  "inspect_image",
  "list_models",
  "prepare_model",
  "segment",
  "refine_segmentation",
  "measure_masks",
  "evaluate_segmentation",
  "export_segmentation",
  "train_model",
  "restore_image",
  "get_job",
  "cancel_job",
]
stable_features = []
```

- [ ] **Step 4: Add the check command**

Create `scripts/check_feature_manifest.py`:

```python
#!/usr/bin/env python3
"""Validate bootstrap structure or report deterministic release blockers."""

from __future__ import annotations

import argparse

from cellpose_mcp.release.feature_manifest import (
    load_feature_manifest,
    release_gate_failures,
)


def main() -> int:
    """Run development validation or intentionally blocked release mode."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    manifest = load_feature_manifest()
    failures = release_gate_failures(manifest)
    if args.release:
        for failure in failures:
            print(f"{failure.code}: {failure.subject}: {failure.message}")
        return 1
    print(f"bootstrap manifest valid; release blockers: {len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests and non-mutating static checks**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/contract/test_feature_manifest.py -q
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev ruff check --no-fix src/cellpose_mcp/release scripts/check_feature_manifest.py tests/contract/test_feature_manifest.py
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev mypy src/cellpose_mcp/release scripts/check_feature_manifest.py
```

Expected: `6 passed`; Ruff and mypy exit 0 without edits.

- [ ] **Step 6: Verify development green and release red**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev python scripts/check_feature_manifest.py
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev python scripts/check_feature_manifest.py --release
```

Expected: development exits 0 with 14 blockers; release exits 1 with one
`unresolved_core_matrix` and 13 `missing_stable_tool` lines.

- [ ] **Step 7: Commit only new ledger files**

```bash
git add scripts/check_feature_manifest.py src/cellpose_mcp/features.toml src/cellpose_mcp/release/__init__.py src/cellpose_mcp/release/feature_manifest.py tests/contract/test_feature_manifest.py
git diff --cached --check
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={"scripts/check_feature_manifest.py","src/cellpose_mcp/features.toml","src/cellpose_mcp/release/__init__.py","src/cellpose_mcp/release/feature_manifest.py","tests/contract/test_feature_manifest.py"}; assert actual == expected, sorted(actual)'
git commit -m "feat: add release-blocked feature ledger"
```

### Task 5: Build only from a clean committed clone and allowlist artifacts

**Files:**

- Create: `tests/packaging/test_distribution_contents.py`
- Replace: `MANIFEST.in`

**Interfaces:**

- Consumes: committed Tasks 1–4 plus the working `MANIFEST.in` under test.
- Produces test-only exact signatures:

```text
build_from_clean_clone(
    tmp_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path]
stripped_sdist_paths(sdist: pathlib.Path) -> set[str]
```

- Produces: a clean-clone build that excludes all untracked runtime modules and
  a true source-distribution allowlist.
- Installed proof: a genuinely clean venv installs the product wheel with
  `--no-deps`, reads the packaged manifest through distribution metadata under
  `-I`, and imports no package initializer or scientific/controller framework.

- [ ] **Step 1a: Add clean-clone build helpers**

Create `tests/packaging/test_distribution_contents.py` with:

```python
# ruff: noqa: S603

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
GIT = shutil.which("git")
if GIT is None:
    raise RuntimeError("Git is required for clean-clone package tests")


def build_from_clean_clone(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    subprocess.run(
        [GIT, "clone", "--quiet", "--no-hardlinks", str(ROOT), str(source)],
        check=True,
        capture_output=True,
    )
    assert not (source / "src/cellpose_mcp/operations.py").exists()
    assert not (source / "src/cellpose_mcp/cli/app.py").exists()
    shutil.copy2(ROOT / "MANIFEST.in", source / "MANIFEST.in")
    output = tmp_path / "dist"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--sdist",
            "--outdir",
            str(output),
        ],
        cwd=source,
        check=True,
        env={**os.environ, "PYTHONPATH": ""},
    )
    return next(output.glob("*.whl")), next(output.glob("*.tar.gz"))


def stripped_sdist_paths(sdist: Path) -> set[str]:
    with tarfile.open(sdist, mode="r:gz") as archive:
        members = {
            member.name
            for member in archive.getmembers()
            if member.name and not member.isdir()
        }
    return {
        "/".join(Path(path).parts[1:])
        for path in members
        if len(Path(path).parts) > 1
    }
```

- [ ] **Step 1b: Add wheel/sdist allowlist assertions**

Append:

```python


@pytest.mark.integration
def test_clean_wheel_sdist_and_installed_manifest_metadata(
    tmp_path: Path,
) -> None:
    wheel, sdist = build_from_clean_clone(tmp_path)
    with zipfile.ZipFile(wheel) as archive:
        wheel_paths = set(archive.namelist())
    assert "cellpose_mcp/features.toml" in wheel_paths
    assert "cellpose_mcp/py.typed" in wheel_paths
    assert "cellpose_mcp/operations.py" not in wheel_paths
    assert "cellpose_mcp/cli/app.py" not in wheel_paths
    assert all(
        path.startswith("cellpose_mcp/") or ".dist-info/" in path
        for path in wheel_paths
    )
    assert not any(
        path.endswith((".pyc", ".pyo", ".DS_Store"))
        or "__pycache__" in Path(path).parts
        for path in wheel_paths
    )

    sdist_paths = stripped_sdist_paths(sdist)
    assert "CHANGELOG.md" not in sdist_paths
    assert "src/cellpose_mcp/features.toml" in sdist_paths
    assert "src/cellpose_mcp/py.typed" in sdist_paths
    assert "src/cellpose_mcp/operations.py" not in sdist_paths
    assert "src/cellpose_mcp/cli/app.py" not in sdist_paths
    assert "uv.lock" not in sdist_paths
    assert {Path(path).parts[0] for path in sdist_paths} <= {
        "LICENSE",
        "MANIFEST.in",
        "PKG-INFO",
        "README.md",
        "pyproject.toml",
        "setup.cfg",
        "src",
    }
    assert all(
        not path.startswith("src/")
        or path.startswith(
            ("src/cellpose_mcp/", "src/cellpose_mcp.egg-info/")
        )
        for path in sdist_paths
    )
    forbidden_roots = {
        ".github",
        "demo_images",
        "docs",
        "examples",
        "local_archive",
        "poster",
        "results",
        "scripts",
        "tests",
        "train_data",
        "untitled folder",
    }
    assert not {
        Path(path).parts[0]
        for path in sdist_paths
    }.intersection(forbidden_roots)
```

- [ ] **Step 1c: Add the installed-metadata proof**

Append the rest of
`test_clean_wheel_sdist_and_installed_manifest_metadata`:

```python
    environment = tmp_path / "installed"
    venv.EnvBuilder(
        with_pip=True,
        symlinks=True,
        system_site_packages=False,
    ).create(environment)
    python = environment / "bin" / "python"
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            str(wheel),
        ],
        check=True,
    )
    code = """
import importlib.metadata
import sys
import tomllib
from pathlib import Path

distribution = importlib.metadata.distribution("cellpose-mcp")
manifest_path = Path(distribution.locate_file("cellpose_mcp/features.toml"))
assert manifest_path.is_relative_to(Path(sys.prefix))
with manifest_path.open("rb") as stream:
    manifest = tomllib.load(stream)
assert manifest["target_release"] == "0.2.0"
assert manifest["release_blockers"] == ["core_capability_matrix_unresolved"]
assert "cellpose_mcp" not in sys.modules
forbidden = {
    "cellpose",
    "cellpose_mcp",
    "fastmcp",
    "rich",
    "torch",
    "typer",
}
loaded = {name.split(".", 1)[0] for name in sys.modules}
assert forbidden.isdisjoint(loaded), sorted(forbidden.intersection(loaded))
"""
    subprocess.run(
        [str(python), "-I", "-c", code],
        cwd=tmp_path,
        check=True,
        env={**os.environ, "PYTHONPATH": ""},
    )
```

- [ ] **Step 2: Run the clean-build test and prove the old manifest leaks**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/packaging/test_distribution_contents.py -q
```

Expected: FAIL at `assert "CHANGELOG.md" not in sdist_paths` because the current
manifest explicitly includes that tracked top-level file. The clean clone
proves the failure without packaging untracked `operations.py` or
`cli/app.py`.

- [ ] **Step 3: Replace the manifest with a true allowlist**

Replace `MANIFEST.in` with exactly:

```text
global-exclude *

include LICENSE
include MANIFEST.in
include README.md
include pyproject.toml
recursive-include src/cellpose_mcp *.py
include src/cellpose_mcp/py.typed
include src/cellpose_mcp/features.toml
```

This foundation allowlist intentionally excludes the root development
`uv.lock`. Later worker plans may add only their exact packaged lock paths and
extend the artifact test for those paths; the test does not globally forbid
files named `uv.lock`.

- [ ] **Step 4: Run artifact and installed-metadata proof**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/packaging/test_distribution_contents.py -q
```

Expected: `1 passed`. The source is a clean committed clone with only the
candidate `MANIFEST.in` overlaid; the isolated venv does not inherit host site
packages or repository `PYTHONPATH`, and it inspects installed package data
without importing the still-legacy package initializer.

- [ ] **Step 5: Run non-mutating static checks**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev ruff check --no-fix tests/packaging/test_distribution_contents.py
git diff --check -- MANIFEST.in tests/packaging/test_distribution_contents.py
```

Expected: both commands exit 0 without modifying files.

- [ ] **Step 6: Commit the artifact boundary**

```bash
git add MANIFEST.in tests/packaging/test_distribution_contents.py
git diff --cached --check
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={"MANIFEST.in","tests/packaging/test_distribution_contents.py"}; assert actual == expected, sorted(actual)'
git commit -m "build: allowlist clean distribution contents"
```

### Task 6: Enforce the locked foundation gate in CI and locally

**Files:**

- Modify: `tests/packaging/test_python_policy.py`
- Modify by hunk only: `.github/workflows/ci.yml`

**Interfaces:**

- Consumes: the checked lock and all foundation tests.
- Produces no Python API. It produces the exact `lint-test` CI contract:
  Python matrix `["3.11", "3.12"]`, uv `0.10.4`, `uv sync --locked` with
  `test`/`dev` extras, development manifest validation, Ruff `--no-fix`, mypy,
  and the locked non-slow pytest suite.
- Produces: Python 3.11/3.12 CI that bootstraps exact uv `0.10.4`, synchronizes
  the lock with test/dev extras, validates the bootstrap ledger, runs Ruff
  without fixes, runs mypy, and runs the non-slow suite.
- Does not claim Apple Silicon product verification; real macOS 14+ Apple
  Silicon worker and user-journey gates remain release-candidate requirements.

- [ ] **Step 1: Add the failing CI policy test**

Append to `tests/packaging/test_python_policy.py`:

```python


def test_ci_uses_locked_uv_on_both_supported_versions() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(workflow.split())
    assert 'python-version: ["3.11", "3.12"]' in normalized
    assert 'python-version: ["3.10", "3.11", "3.12"]' not in normalized
    assert 'python -m pip install "uv==0.10.4"' in normalized
    assert "uv sync --locked" in normalized
    assert 'echo "$PWD/.venv/bin" >> "$GITHUB_PATH"' in normalized
    assert "uv lock --check" in normalized
    assert "python scripts/check_feature_manifest.py" in normalized
    assert "ruff check --no-fix" in normalized
    assert "mypy src/cellpose_mcp/release" in normalized
```

- [ ] **Step 2: Run the test and verify current CI is unlocked**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/packaging/test_python_policy.py::test_ci_uses_locked_uv_on_both_supported_versions -q
```

Expected: FAIL because CI still includes Python 3.10 and resolves with pip
instead of the checked uv lock.

- [ ] **Step 3a: Update the Python matrix and locked environment step**

Change the `lint-test` matrix to:

```yaml
matrix:
  python-version: ["3.11", "3.12"]
```

Replace the existing dependency-install step with:

```yaml
      - name: Install locked environment
        run: |
          python -m pip install "uv==0.10.4"
          uv sync --locked --python "${{ matrix.python-version }}" --extra test --extra dev
          echo "$PWD/.venv/bin" >> "$GITHUB_PATH"
```

- [ ] **Step 3b: Add the development foundation contract step**

Add immediately afterward:

```yaml
      - name: Foundation contract
        run: |
          uv lock --check
          uv run --locked --python "${{ matrix.python-version }}" --extra test --extra dev python scripts/check_feature_manifest.py
          uv run --locked --python "${{ matrix.python-version }}" --extra test --extra dev pytest tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py -q
```

- [ ] **Step 3c: Make Ruff non-mutating**

Replace the existing Ruff step with:

```yaml
      - name: Ruff
        run: >
          uv run --locked --python "${{ matrix.python-version }}"
          --extra test --extra dev ruff check --no-fix
          src/ tests/ scripts/check_feature_manifest.py
          scripts/inventory_worktree.py
```

- [ ] **Step 3d: Add foundation type checking**

Add:

```yaml
      - name: Mypy foundation
        run: >
          uv run --locked --python "${{ matrix.python-version }}"
          --extra test --extra dev mypy
          src/cellpose_mcp/release scripts/check_feature_manifest.py
          scripts/inventory_worktree.py
```

- [ ] **Step 3e: Verify the existing regression step remains untouched**

Leave the existing committed Pytest step unchanged:

```yaml
      - name: Pytest
        run: pytest -m "not slow" --tb=short
```

The locked `.venv/bin` is on `GITHUB_PATH` for that step. Do not stage the
pre-existing working-tree change that adds
`not install_e2e`, the `install-e2e` job, or its reference to the untracked
`tests/test_installation.py`.

- [ ] **Step 4: Run the CI policy and complete foundation tests locally**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.11 --extra test --extra dev pytest tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q
```

Expected: `20 passed` on Python 3.11 and `20 passed` on Python 3.12.

- [ ] **Step 5: Run every non-mutating static and lock check**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 lock --check
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev ruff check --no-fix src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev mypy src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py
git diff --check
```

Expected: all commands exit 0 and no file changes as a side effect.

- [ ] **Step 6: Run the existing safe local regression suite**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest -m "not slow and not install_e2e" --tb=short
```

Expected: exit 0. Any failure blocks staging and the Task 6 commit. Invoke
`superpowers:systematic-debugging`, rerun the first failure with
`pytest -x -vv <exact-node-id>`, and fix the demonstrated regression or report
the reproducible blocker; no old test is removed or rewritten merely to make
this phase green.

- [ ] **Step 7: Reconfirm the deliberate release block**

Run:

```bash
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev python scripts/check_feature_manifest.py
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev python scripts/check_feature_manifest.py --release
```

Expected: development exits 0; release exits 1 with exactly one unresolved
matrix failure and 13 missing stable tool failures.

- [ ] **Step 8: Stage CI by hunk and verify user work is excluded**

Stage the policy test normally:

```bash
git add tests/packaging/test_python_policy.py
git add -p .github/workflows/ci.yml
```

Select only the matrix, exact uv install/sync/path, foundation, Ruff, and mypy
hunks from Step 3. Leave the existing Pytest hunk unselected. If planned and
user-owned lines cannot be split, choose `e` and remove the user-owned lines
from the proposed index patch before applying it; do not edit the working
file. Verify:

```bash
python3 -c 'import subprocess; d=subprocess.check_output(["git","diff","--cached","--",".github/workflows/ci.yml"],text=True); required=["3.11\", \"3.12","uv==0.10.4","uv sync --locked","uv lock --check","ruff check --no-fix","Mypy foundation"]; forbidden=["not slow and not install_e2e","install-e2e:","test_fresh_venv_wheel_install_segment_e2e"]; assert all(x in d for x in required); assert all(x not in d for x in forbidden)'
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={".github/workflows/ci.yml","tests/packaging/test_python_policy.py"}; assert actual == expected, sorted(actual)'
git diff --cached --check
```

Expected: both commands exit 0. If the assertion fails, run
`git restore --staged .github/workflows/ci.yml` and repeat hunk selection.

- [ ] **Step 9: Commit CI and prove its paired user files remain unstaged**

```bash
git commit -m "ci: enforce locked repository foundation"
```

Run:

```bash
python3 -c 'import subprocess; d=subprocess.check_output(["git","diff","HEAD","--",".github/workflows/ci.yml"],text=True); expected=["not slow and not install_e2e","install-e2e:","test_fresh_venv_wheel_install_segment_e2e"]; assert all(x in d for x in expected)'
git status --short
git status --short --ignored local_archive
git diff --cached --name-only
```

Expected:

- The user’s install job remains a working-tree change with its untracked test.
- `local_archive/` is ignored.
- No generated image, result, training data, model, CLI input, or uncertain
  experiment is staged.
- The index is empty after the commit.

- [ ] **Step 10: Stop at the Phase 0 boundary**

Run:

```bash
git log --oneline -8
```

Expected: narrow commits for inventory core/output, Python policy, blocked
ledger, artifact allowlist, and CI. Do not switch the MCP entrypoint, delete
legacy code, tag a version, publish GitHub artifacts, or upload to PyPI.

## Phase 0 definition of done

- [ ] A real ignored report records tracked, modified, and non-ignored
  untracked worktree/index SHA-256 evidence before any existing project file
  was edited.
- [ ] Existing user source/tests/config/results remain present and unstaged.
- [ ] Python 3.11 and 3.12 pass the foundation tests from the checked lock.
- [ ] Ruff checks are non-mutating and all foundation static checks pass.
- [ ] Bootstrap manifest schema 1 is structurally valid and impossible to mark
  release-ready.
- [ ] A clean committed clone excludes untracked runtime modules.
- [ ] Wheel/sdist contents pass the explicit foundation allowlist.
- [ ] An isolated venv reads the packaged manifest through distribution
  metadata without importing Cellpose, torch, FastMCP, Typer, Rich, or the
  still-legacy package initializer.
- [ ] The current MCP/scientific path remains unchanged.
- [ ] No intermediate artifact is published.
