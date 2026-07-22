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

> **Revision — 2026-07-21:** Tasks 0–5 were completed in commits
> `0bd7aec` through `45021a2`. The approved stable-Cellpose amendment
> supersedes the former Task 6: Phase 0 CI is a repository-foundation gate,
> not evidence that the legacy mixed Cellpose wrapper works. The revised
> Tasks 6–7 below are the only authoritative completion steps for this plan.
> Tasks 0–5 are retained as historical evidence of work already committed.
> Their command fences are non-rerunnable and MUST NOT be executed;
> a fresh or resumed execution starts at authoritative Task 6.

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
- Every `bash` fence is an independent `/bin/bash` process whose first command
  is `set -euo pipefail`. Derived values are assigned and validated before a
  separate export; `export NAME=$(...)` is forbidden because it masks command
  substitution failures.
- Git-ignored caches/builds are outside this initial report and cannot be
  deleted or cleaned. Phase 12 inventories any ignored cleanup candidate
  separately before presenting an exact removal list.
- Existing dirty `pyproject.toml` changes are staged by hunk only. The CI
  foundation blob is staged from an exact clean-candidate patch while its
  pre-existing install-test suffix stays byte-identical in the worktree.
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
| `.github/workflows/ci.yml` | Locked uv foundation-only checks on 3.11/3.12; stage the exact clean-candidate blob and preserve the user suffix in the worktree |

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

### Task 0 (historical; completed — do not rerun): Verify the execution environment without changing the repository

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
set -euo pipefail
git diff --cached --quiet
git diff --cached --name-only
```

Expected: the first command exits 0 and the second prints nothing. If either
condition fails, stop and ask the user how to preserve the staged work; do not
unstage or combine it automatically.

- [ ] **Step 2a: Verify or bootstrap exact uv**

Run:

```bash
set -euo pipefail
UV_SOURCE="$(command -v uv)"
python3 -c 'import subprocess,sys; assert subprocess.check_output([sys.argv[1],"--version"],text=True).startswith("uv 0.10.4 ")' "$UV_SOURCE"
```

Expected: both commands exit 0. If `uv` is absent, request dependency-install
approval, run:

```bash
set -euo pipefail
python3 -m pip install --user "uv==0.10.4"
UV_SOURCE="$(python3 -c 'import site; from pathlib import Path; print(Path(site.USER_BASE) / "bin" / "uv")')"
python3 -c 'import subprocess,sys; assert subprocess.check_output([sys.argv[1],"--version"],text=True).startswith("uv 0.10.4 ")' "$UV_SOURCE"
```

The recovery block verifies that absolute `UV_SOURCE`. A different uv version
is a blocker until exact `0.10.4` is installed.

- [ ] **Step 2b: Create one path-stable uv runner outside the repository**

Run:

```bash
set -euo pipefail
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
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python find --no-python-downloads 3.11
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python find --no-python-downloads 3.12
```

Expected: each command prints an absolute interpreter path. If either is
absent, request dependency-download approval, run:

```bash
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 python install 3.11 3.12
```

Then repeat both `python find --no-python-downloads` commands. Tasks 1–2 use
controlled Python 3.12 through `uv run --no-project`; no foundation test uses
host Python 3.13.

### Task 1 (historical; completed — do not rerun): Build a read-only Git/worktree inventory core

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
set -euo pipefail
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
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 python tests/dev/test_inventory_worktree.py
```

Expected: `Ran 2 tests` and `OK`.

- [ ] **Step 5: Commit only the two new files**

```bash
set -euo pipefail
git add scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py
git diff --cached --check
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={"scripts/inventory_worktree.py","tests/dev/test_inventory_worktree.py"}; assert actual == expected, sorted(actual)'
git commit -m "chore: add read-only worktree inventory core"
```

This commit adds new files only; it does not stage any pre-existing dirty path.

### Task 2 (historical; completed — do not rerun): Add safe inventory output and capture the real baseline

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
set -euo pipefail
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
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 python tests/dev/test_inventory_worktree.py
```

Expected: `Ran 7 tests` and `OK`.

- [ ] **Step 5: Capture the real worktree before editing existing files**

Run:

```bash
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --no-project --python 3.12 python scripts/inventory_worktree.py
```

Expected: exit 0 and a new
`local_archive/worktree-inventory-<timestamp>.json`. The report includes every
tracked, modified, and non-ignored untracked path plus the plan-owned inventory
files; it precedes changes to `pyproject.toml`, CI, Python policy, or packaging.
It does not authorize any operation on ignored paths.

Inspect only the summary and path metadata, not user file contents:

```bash
set -euo pipefail
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
set -euo pipefail
chmod +x scripts/inventory_worktree.py
git status --short --ignored local_archive
```

Expected: `local_archive/` is ignored; no report is staged.

- [ ] **Step 7: Commit only inventory-owned files**

```bash
set -euo pipefail
git add .gitignore scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py
git diff --cached --check
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={".gitignore","scripts/inventory_worktree.py","tests/dev/test_inventory_worktree.py"}; assert actual == expected, sorted(actual)'
git commit -m "chore: persist safe worktree inventories"
```

Expected: the commit contains only the three listed paths. No existing user
source, test, result, or configuration hunk is staged.

### Task 3 (historical; completed — do not rerun): Lock Python policy and the transitional development environment

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
set -euo pipefail
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
set -euo pipefail
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
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 lock --python 3.12
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 lock --check
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 sync --locked --python 3.12 --extra test --extra dev
```

Expected: uv 0.10.4 exits 0, creates `uv.lock`, and synchronizes all test/dev
tools without changing the selected dependency solution afterward.

- [ ] **Step 5: Run the policy tests on both public Python versions**

Run:

```bash
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.11 --extra test --extra dev pytest tests/packaging/test_python_policy.py -q
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/packaging/test_python_policy.py -q
```

Expected: `5 passed` on Python 3.11 and `5 passed` on Python 3.12.

- [ ] **Step 6: Run non-mutating static checks on inventory code**

Run:

```bash
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev ruff check --no-fix scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py tests/packaging/test_python_policy.py
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev mypy scripts/inventory_worktree.py
```

Expected: Ruff and mypy exit 0 without modifying any file.

- [ ] **Step 7: Stage the dirty metadata by hunk, never by whole file**

Stage the clean/new paths normally:

```bash
set -euo pipefail
git add .python-version tests/packaging/test_python_policy.py uv.lock
```

Stage `pyproject.toml` interactively:

```bash
set -euo pipefail
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
set -euo pipefail
python3 -c 'import subprocess; d=subprocess.check_output(["git","diff","--cached","--","pyproject.toml"],text=True); required=[">=3.11,<3.13","pydantic>=2.11,<3","build>=1.2,<2","package-data","fix = false","TC003"]; forbidden=["MCP server and CLI","cellpose-mcp-cli","no:napari","install_e2e","src/cellpose_mcp/cli/app.py"]; assert all(x in d for x in required); assert all(x not in d for x in forbidden)'
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={".python-version","pyproject.toml","tests/packaging/test_python_policy.py","uv.lock"}; assert actual == expected, sorted(actual)'
git diff --cached --check
```

Expected: both commands exit 0. If the assertion fails, unstage only
`pyproject.toml` and repeat hunk selection; do not commit a mixed patch.

- [ ] **Step 8: Commit and prove the user hunks remain**

```bash
set -euo pipefail
git commit -m "build: lock repository foundation environment"
```

Verify the pre-existing working changes are still outside the commit:

```bash
set -euo pipefail
python3 -c 'import subprocess; d=subprocess.check_output(["git","diff","HEAD","--","pyproject.toml"],text=True); expected=["MCP server and CLI","cellpose-mcp-cli","no:napari","install_e2e","src/cellpose_mcp/cli/app.py"]; assert all(x in d for x in expected)'
```

Expected: exit 0. The clean committed tree has the foundation policy, while
the user’s paired untracked CLI/install work remains preserved in the working
tree.

### Task 4 (historical; completed — do not rerun): Add an explicitly blocked bootstrap feature ledger

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
set -euo pipefail
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
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/contract/test_feature_manifest.py -q
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev ruff check --no-fix src/cellpose_mcp/release scripts/check_feature_manifest.py tests/contract/test_feature_manifest.py
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev mypy src/cellpose_mcp/release scripts/check_feature_manifest.py
```

Expected: `6 passed`; Ruff and mypy exit 0 without edits.

- [ ] **Step 6: Verify development green and release red**

Run:

```bash
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev python scripts/check_feature_manifest.py
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev python scripts/check_feature_manifest.py --release
```

Expected: development exits 0 with 14 blockers; release exits 1 with one
`unresolved_core_matrix` and 13 `missing_stable_tool` lines.

- [ ] **Step 7: Commit only new ledger files**

```bash
set -euo pipefail
git add scripts/check_feature_manifest.py src/cellpose_mcp/features.toml src/cellpose_mcp/release/__init__.py src/cellpose_mcp/release/feature_manifest.py tests/contract/test_feature_manifest.py
git diff --cached --check
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={"scripts/check_feature_manifest.py","src/cellpose_mcp/features.toml","src/cellpose_mcp/release/__init__.py","src/cellpose_mcp/release/feature_manifest.py","tests/contract/test_feature_manifest.py"}; assert actual == expected, sorted(actual)'
git commit -m "feat: add release-blocked feature ledger"
```

### Task 5 (historical; completed — do not rerun): Build only from a clean committed clone and allowlist artifacts

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
set -euo pipefail
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
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev pytest tests/packaging/test_distribution_contents.py -q
```

Expected at the initial GREEN commit: `1 passed`. Review commits `03bd178` and
`45021a2` then expanded the same committed file to 17 focused adversarial
tests. Because Tasks 0–5 are complete, executors do not recreate the one-test
intermediate. Task 6 adds two offline-boundary tests, so the authoritative
expectation after Task 6 Step 8 is `19 passed`. The source is a clean committed
clone, and the isolated venv does not inherit host site packages or repository
`PYTHONPATH`.

- [ ] **Step 5: Run non-mutating static checks**

Run:

```bash
set -euo pipefail
/private/tmp/cellpose-mcp-foundation-uv-0.10.4 run --locked --python 3.12 --extra test --extra dev ruff check --no-fix tests/packaging/test_distribution_contents.py
git diff --check -- MANIFEST.in tests/packaging/test_distribution_contents.py
```

Expected: both commands exit 0 without modifying files.

- [ ] **Step 6: Commit the artifact boundary**

```bash
set -euo pipefail
git add MANIFEST.in tests/packaging/test_distribution_contents.py
git diff --cached --check
python3 -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={"MANIFEST.in","tests/packaging/test_distribution_contents.py"}; assert actual == expected, sorted(actual)'
git commit -m "build: allowlist clean distribution contents"
```

### Task 6: Correct diagnostics, offline packaging, and the CI contract

**Files:**

- Modify: `scripts/inventory_worktree.py`
- Modify: `tests/dev/test_inventory_worktree.py`
- Modify by approved hunk only: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `tests/packaging/test_distribution_contents.py`
- Modify: `tests/packaging/test_python_policy.py`
- Modify: `scripts/check_feature_manifest.py`
- Modify: `tests/contract/test_feature_manifest.py`
- Modify in the plan-owned prefix only: `.github/workflows/ci.yml`

**Interfaces:**

- `archive_object_error(repo_descriptor: int) -> ValueError | RuntimeError`
  continues to classify a symlink or non-directory as user input errors, but
  reports a directory that could not be opened safely as a runtime failure.
- Python metadata classifiers are an exact ordered list. Root dependencies are
  intentionally checked only for the required transitional minimums because
  the approved migration removes Cellpose from the controller in a later
  phase; this root lock is not worker evidence.
- CI exposes exactly one job named `foundation`. It runs only the inventory,
  bootstrap-ledger, Python-policy, and distribution-content tests on Python
  3.11 and 3.12 from the checked lock. It never collects the legacy wrapper or
  the unapproved install/segmentation experiment.
- The manifest checker imports `cellpose_mcp.release.feature_manifest` through
  one shared synthetic-package loader. It creates a `cellpose_mcp` package
  spec whose `submodule_search_locations` is the real source package, inserts
  that unexecuted synthetic package in `sys.modules`, and then executes only
  `feature_manifest.py` under its real fully-qualified module name. The
  contract tests load the checker once, alias its shared module/classes, prove
  instances pickle with that real module identity, and assert that the legacy
  runtime (`cellpose`, server/tools, FastMCP, Rich, Torch, and Typer) was never
  imported.
- The existing user-owned CI suffix beginning with `- name: Pytest` remains
  byte-identical in the dirty worktree but is absent from the committed blob.
- No current MCP, Cellpose, training, installation, or scientific code is
  changed or claimed as passing.
- Distribution builds run `python -m build --no-isolation` without
  `--skip-dependency-check`, so the frontend verifies every declared build
  requirement but cannot provision an isolated environment.
- The test extra directly contains `build>=1.2,<2` and every exact
  `[build-system].requires` entry; the checked root lock carries them.
- Build, wheel-install, and installed-metadata subprocesses receive a copied
  environment that disables pip indexes/version checks/config, removes
  inherited proxy/index/trust/certificate settings, clears `PYTHONPATH`, and
  disables user-site imports. Wheel installation uses both `--no-index` and
  `--no-deps`.
- Every uv environment is dependency-only: synchronization uses both
  `--no-install-project` and `--no-build`. The checked source tree is exposed
  only through an exact absolute `PYTHONPATH` during tests, so uv cannot update
  repository-local egg-info, build, or distribution metadata.
- Every pytest command disables `cacheprovider`, every Ruff command uses
  `--no-cache`, Python bytecode writes are disabled, and mypy caches live only
  in the run-specific temporary directory. A clean candidate must have none of
  `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `build`, `dist`,
  `src/cellpose_mcp.egg-info`, or a source-tree `__pycache__` after execution.
- Before any approved package-index call, the project dependency declarations
  and input lock are parsed. Direct dependency URLs and uv source/index
  overrides are forbidden; the only registry is exactly
  `https://pypi.org/simple`, and every artifact URL is HTTPS on exactly
  `files.pythonhosted.org`. A refreshed lock is validated before synchronization.

- [ ] **Step 1: Gate the exact repository and provision fresh pinned execution environments**

Obtain approval for this one package-index boundary before running the block.
It may contact only `https://pypi.org/simple` and artifact URLs beneath
`https://files.pythonhosted.org/`. The inherited shell environment, user
configuration, proxies, credentials, keyrings, and automatic Python downloads
are not available to uv.

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
[[ $FOUNDATION_ROOT == /* ]]
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git -C "$FOUNDATION_ROOT" branch --show-current)" = codex/cellpose-local-first
git -C "$FOUNDATION_ROOT" cat-file -e '45021a2^{commit}'
git -C "$FOUNDATION_ROOT" merge-base --is-ancestor 45021a2 HEAD
git -C "$FOUNDATION_ROOT" diff --cached --quiet
export FOUNDATION_ROOT

UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
test -x "$UV"
test -x "$PY311"
test -x "$PY312"
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
test "$("$UV" --version)" = 'uv 0.10.4 (079e3fd05 2026-02-17)'
test "$("$PY311" -I -c 'import platform; print(platform.python_version())')" = 3.11.14
test "$("$PY312" -I -c 'import platform; print(platform.python_version())')" = 3.12.12
export UV PY311 PY312

validate_network_sources() {
  "$PY312" -I - "$1" "$2" <<'PY'
from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

INDEX = "https://pypi.org/simple"
FILES_HOST = "files.pythonhosted.org"
project_path, lock_path = map(Path, sys.argv[1:])
project = tomllib.loads(project_path.read_text(encoding="utf-8"))
requirements = list(project["project"].get("dependencies", []))
for group in project["project"].get("optional-dependencies", {}).values():
    requirements.extend(group)
requirements.extend(project["build-system"].get("requires", []))
assert requirements
assert all(isinstance(item, str) for item in requirements)
assert all("@" not in item and "://" not in item for item in requirements)
assert "dependency-groups" not in project
uv_config = project.get("tool", {}).get("uv", {})
assert isinstance(uv_config, dict)
assert uv_config == {}


def check_url(value: str) -> None:
    parsed = urlsplit(value)
    assert parsed.scheme == "https", value
    assert parsed.username is None and parsed.password is None, value
    assert parsed.port is None and parsed.query == "" and parsed.fragment == "", value
    if value == INDEX:
        return
    assert parsed.hostname == FILES_HOST, value
    assert parsed.path.startswith("/packages/"), value


lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
for package in lock["package"]:
    source = package["source"]
    assert source in ({"registry": INDEX}, {"editable": "."}), source
    if "sdist" in package:
        check_url(package["sdist"]["url"])
    for wheel in package.get("wheels", []):
        check_url(wheel["url"])
PY
}

assert_environment_binding() {
  local environment=$1
  local base_python=$2
  local expected_minor=$3
  test -x "$environment/bin/python"
  "$environment/bin/python" -I -c 'from pathlib import Path; import sys; environment=Path(sys.argv[1]); base=Path(sys.argv[2]); expected=tuple(map(int,sys.argv[3].split("."))); assert Path(sys.executable)==environment/"bin/python",(sys.executable,environment); assert Path(sys.prefix)==environment,(sys.prefix,environment); assert Path(sys.executable).resolve()==base.resolve(); assert Path(sys._base_executable).resolve()==base.resolve(); assert sys.version_info[:2]==expected' "$environment" "$base_python" "$expected_minor"
}

FOUNDATION_ROOT_LOCK_SHA=$(hash_file "$FOUNDATION_ROOT/uv.lock")
[[ $FOUNDATION_ROOT_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
FOUNDATION_ROOT_CACHE=/private/tmp/cellpose-mcp-foundation-root-cache-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_ENV_311=/private/tmp/cellpose-mcp-foundation-root-py311-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_ENV_312=/private/tmp/cellpose-mcp-foundation-root-py312-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_HOME=/private/tmp/cellpose-mcp-foundation-root-home-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_TMP=/private/tmp/cellpose-mcp-foundation-root-tmp-${FOUNDATION_ROOT_LOCK_SHA}
[[ $FOUNDATION_ROOT_CACHE == /private/tmp/cellpose-mcp-foundation-root-cache-[0-9a-f]* ]]
[[ $FOUNDATION_ROOT_ENV_311 == /private/tmp/cellpose-mcp-foundation-root-py311-[0-9a-f]* ]]
[[ $FOUNDATION_ROOT_ENV_312 == /private/tmp/cellpose-mcp-foundation-root-py312-[0-9a-f]* ]]
assert_private_directory() {
  local directory=$1
  test -d "$directory"
  test ! -L "$directory"
  test -O "$directory"
  test "$(/usr/bin/stat -f '%Lp' "$directory")" = 700
}
for private_directory in "$FOUNDATION_ROOT_CACHE" "$FOUNDATION_ROOT_HOME" "$FOUNDATION_ROOT_TMP"; do
  if test -e "$private_directory"; then
    assert_private_directory "$private_directory"
  else
    install -d -m 700 "$private_directory"
  fi
done
export FOUNDATION_ROOT_LOCK_SHA FOUNDATION_ROOT_CACHE
export FOUNDATION_ROOT_ENV_311 FOUNDATION_ROOT_ENV_312
export FOUNDATION_ROOT_HOME FOUNDATION_ROOT_TMP

validate_network_sources "$FOUNDATION_ROOT/pyproject.toml" "$FOUNDATION_ROOT/uv.lock"
if test -e "$FOUNDATION_ROOT_ENV_311"; then
  assert_environment_binding "$FOUNDATION_ROOT_ENV_311" "$PY311" 3.11
else
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ROOT_HOME" TMPDIR="$FOUNDATION_ROOT_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_ROOT_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ROOT_ENV_311" UV_DEFAULT_INDEX=https://pypi.org/simple UV_KEYRING_PROVIDER=disabled UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ROOT" --project "$FOUNDATION_ROOT" --no-config sync --frozen --no-install-project --no-build --python "$PY311" --extra test --extra dev --default-index https://pypi.org/simple --keyring-provider disabled --no-python-downloads
fi
if test -e "$FOUNDATION_ROOT_ENV_312"; then
  assert_environment_binding "$FOUNDATION_ROOT_ENV_312" "$PY312" 3.12
else
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ROOT_HOME" TMPDIR="$FOUNDATION_ROOT_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_ROOT_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ROOT_ENV_312" UV_DEFAULT_INDEX=https://pypi.org/simple UV_KEYRING_PROVIDER=disabled UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ROOT" --project "$FOUNDATION_ROOT" --no-config sync --frozen --no-install-project --no-build --python "$PY312" --extra test --extra dev --default-index https://pypi.org/simple --keyring-provider disabled --no-python-downloads
fi

validate_network_sources "$FOUNDATION_ROOT/pyproject.toml" "$FOUNDATION_ROOT/uv.lock"
test "$(hash_file "$FOUNDATION_ROOT/uv.lock")" = "$FOUNDATION_ROOT_LOCK_SHA"
assert_environment_binding "$FOUNDATION_ROOT_ENV_311" "$PY311" 3.11
assert_environment_binding "$FOUNDATION_ROOT_ENV_312" "$PY312" 3.12
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: every repository/ancestor assertion passes; the index is empty; all
three executable hashes are unchanged before and after provisioning; and two
previously absent, lock-keyed environments are realized from the explicit
package boundary. Any mismatch is a blocker, never permission to replace a
tool, environment, cache, or user file.

- [ ] **Step 2: Add the failing archive diagnostic test**

Add this method to `InventoryCoreTests` in
`tests/dev/test_inventory_worktree.py`:

```python
    def test_archive_directory_open_failure_is_not_a_type_error(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            (repo / "local_archive").mkdir()
            repo_descriptor = os.open(
                repo,
                inventory.DIRECTORY_NOFOLLOW_FLAGS,
            )
            try:
                error = inventory.archive_object_error(repo_descriptor)
            finally:
                os.close(repo_descriptor)

            self.assertIsInstance(error, RuntimeError)
            self.assertEqual(
                str(error),
                "local_archive cannot be opened safely",
            )
```

This directly exercises the classifier after the caller's directory-open
operation has failed; it avoids unreliable permission tests on privileged or
platform-dependent filesystems.

- [ ] **Step 3: Run RED for the archive diagnostic**

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_ROOT/uv.lock" | /usr/bin/awk '{print $1}')
FOUNDATION_ROOT_CACHE=/private/tmp/cellpose-mcp-foundation-root-cache-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_ENV_311=/private/tmp/cellpose-mcp-foundation-root-py311-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_ENV_312=/private/tmp/cellpose-mcp-foundation-root-py312-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_HOME=/private/tmp/cellpose-mcp-foundation-root-home-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_TMP=/private/tmp/cellpose-mcp-foundation-root-tmp-${FOUNDATION_ROOT_LOCK_SHA}
test -d "$FOUNDATION_ROOT_CACHE"
test -x "$FOUNDATION_ROOT_ENV_311/bin/python"
test -x "$FOUNDATION_ROOT_ENV_312/bin/python"
test -d "$FOUNDATION_ROOT_HOME"
test -d "$FOUNDATION_ROOT_TMP"
"$FOUNDATION_ROOT_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_ROOT_ENV_311" "$PY311"
"$FOUNDATION_ROOT_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_ROOT_ENV_312" "$PY312"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ROOT_HOME" TMPDIR="$FOUNDATION_ROOT_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_ROOT/src" UV_CACHE_DIR="$FOUNDATION_ROOT_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ROOT_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ROOT" --project "$FOUNDATION_ROOT" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev pytest -p no:cacheprovider tests/dev/test_inventory_worktree.py::InventoryCoreTests::test_archive_directory_open_failure_is_not_a_type_error -q
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: one failure because the current function returns
`ValueError("local_archive must be a directory")` for the existing directory.

- [ ] **Step 4: Correct the diagnostic and remove the duplicate dead line**

Replace the end of `archive_object_error` in
`scripts/inventory_worktree.py` with:

```python
    if stat.S_ISLNK(info.st_mode):
        return ValueError("local_archive must not be a symbolic link")
    if not stat.S_ISDIR(info.st_mode):
        return ValueError("local_archive must be a directory")
    return RuntimeError("local_archive cannot be opened safely")
```

In `resolve_output`, retain exactly one copy of this branch:

```python
        if not stat.S_ISDIR(archive_info.st_mode):
            raise ValueError("local_archive must be a directory")
```

- [ ] **Step 5: Run GREEN and commit the bounded inventory correction**

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_ROOT/uv.lock" | /usr/bin/awk '{print $1}')
FOUNDATION_ROOT_CACHE=/private/tmp/cellpose-mcp-foundation-root-cache-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_ENV_311=/private/tmp/cellpose-mcp-foundation-root-py311-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_ENV_312=/private/tmp/cellpose-mcp-foundation-root-py312-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_HOME=/private/tmp/cellpose-mcp-foundation-root-home-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_TMP=/private/tmp/cellpose-mcp-foundation-root-tmp-${FOUNDATION_ROOT_LOCK_SHA}
test -d "$FOUNDATION_ROOT_CACHE"
test -x "$FOUNDATION_ROOT_ENV_311/bin/python"
test -x "$FOUNDATION_ROOT_ENV_312/bin/python"
"$FOUNDATION_ROOT_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_ROOT_ENV_311" "$PY311"
"$FOUNDATION_ROOT_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_ROOT_ENV_312" "$PY312"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ROOT_HOME" TMPDIR="$FOUNDATION_ROOT_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_ROOT/src" UV_CACHE_DIR="$FOUNDATION_ROOT_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ROOT_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ROOT" --project "$FOUNDATION_ROOT" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev pytest -p no:cacheprovider tests/dev/test_inventory_worktree.py -q
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ROOT_HOME" TMPDIR="$FOUNDATION_ROOT_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_ROOT/src" UV_CACHE_DIR="$FOUNDATION_ROOT_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ROOT_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ROOT" --project "$FOUNDATION_ROOT" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev ruff check --no-fix --no-cache scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py
git diff --check -- scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py
git add -- scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py
git diff --cached --check
"$PY312" -I -c 'import subprocess; actual=set(subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()); expected={"scripts/inventory_worktree.py","tests/dev/test_inventory_worktree.py"}; assert actual == expected, sorted(actual)'
git commit -m "fix: clarify inventory archive failures"
test "$(git diff-tree --no-commit-id --name-only -r HEAD)" = $'scripts/inventory_worktree.py\ntests/dev/test_inventory_worktree.py'
git diff --cached --quiet
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: `28 passed`, Ruff and diff checks exit 0, and the commit contains
exactly the two named files.

- [ ] **Step 6: Add RED tests for dependency-checked offline builds**

Create a clean candidate from the new inventory commit:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_FULL_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_FULL_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_FULL_SHA:0:12}
[[ $FOUNDATION_RUN_SHA =~ ^[0-9a-f]{12}$ ]]
export FOUNDATION_RUN_SHA
FOUNDATION_OFFLINE_CANDIDATE=/private/tmp/cellpose-mcp-foundation-offline-candidate-${FOUNDATION_RUN_SHA}
export FOUNDATION_OFFLINE_CANDIDATE
if test -e "$FOUNDATION_OFFLINE_CANDIDATE"; then
  test -d "$FOUNDATION_OFFLINE_CANDIDATE"
  test ! -L "$FOUNDATION_OFFLINE_CANDIDATE"
  test "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" rev-parse HEAD)" = "$FOUNDATION_FULL_SHA"
else
  git clone --no-hardlinks --local . "$FOUNDATION_OFFLINE_CANDIDATE"
fi
test "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" rev-parse HEAD)" = "$FOUNDATION_FULL_SHA"
test -z "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" status --porcelain)"
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

In the candidate, strengthen
`test_required_foundation_dependencies_are_direct` to require the exact
`[build-system].requires` list below and require every item in the test extra:

```python
def test_required_foundation_dependencies_are_direct() -> None:
    document = config()
    project = document["project"]
    assert isinstance(project, dict)
    assert "pydantic>=2.11,<3" in project["dependencies"]

    optional = project["optional-dependencies"]
    assert isinstance(optional, dict)
    test_dependencies = optional["test"]
    assert isinstance(test_dependencies, list)
    assert "build>=1.2,<2" in test_dependencies

    build_system = document["build-system"]
    assert isinstance(build_system, dict)
    build_requirements = [
        "setuptools>=64",
        "setuptools_scm>=8.0",
        "wheel",
    ]
    assert build_system["requires"] == build_requirements
    assert all(item in test_dependencies for item in build_requirements)
```

After `_write_synthetic_wheel`, add these exact adversarial helpers and tests
to `test_distribution_contents.py`:

```python
def _poison_network_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, str]:
    poisoned = dict.fromkeys(
        _NETWORK_ENVIRONMENT_VARIABLES,
        "https://poison.invalid/simple",
    )
    poisoned.update(
        {
            "PIP_CONFIG_FILE": "/poison/pip.conf",
            "PIP_DISABLE_PIP_VERSION_CHECK": "0",
            "PIP_NO_INDEX": "0",
            "PYTHONNOUSERSITE": "0",
            "PYTHONPATH": "/poison/pythonpath",
        }
    )
    for name, value in poisoned.items():
        monkeypatch.setenv(name, value)
    return poisoned


def _assert_offline_environment(
    environment: object,
    poisoned: dict[str, str],
) -> None:
    assert isinstance(environment, dict)
    assert _NETWORK_ENVIRONMENT_VARIABLES.isdisjoint(environment)
    assert environment["PIP_CONFIG_FILE"] == os.devnull
    assert environment["PIP_DISABLE_PIP_VERSION_CHECK"] == "1"
    assert environment["PIP_NO_INDEX"] == "1"
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["PYTHONPATH"] == ""
    assert all(
        os.environ[name] == value
        for name, value in poisoned.items()
    )


def test_clean_clone_build_is_dependency_checked_and_offline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    poisoned = _poison_network_environment(monkeypatch)
    source = tmp_path / "source"
    output = tmp_path / "dist"
    expected_wheel = output / "cellpose_mcp-0.1.4-py3-none-any.whl"
    expected_sdist = output / "cellpose_mcp-0.1.4.tar.gz"
    calls: list[tuple[list[str], dict[str, object]]] = []

    def record_run(command: list[str], **kwargs: object) -> None:
        calls.append((command, kwargs))
        if command[0] == GIT:
            source.mkdir()
            return
        output.mkdir()
        expected_wheel.write_bytes(b"")
        expected_sdist.write_bytes(b"")

    monkeypatch.setattr(subprocess, "run", record_run)

    wheel, sdist = build_from_clean_clone(tmp_path)

    assert (wheel, sdist) == (expected_wheel, expected_sdist)
    assert len(calls) == 2
    build_command, build_kwargs = calls[1]
    assert build_command == [
        sys.executable,
        "-m",
        "build",
        "--no-isolation",
        "--wheel",
        "--sdist",
        "--outdir",
        str(output),
    ]
    assert "--skip-dependency-check" not in build_command
    assert set(build_kwargs) == {"check", "cwd", "env"}
    assert build_kwargs["check"] is True
    assert build_kwargs["cwd"] == source
    _assert_offline_environment(build_kwargs["env"], poisoned)


def test_wheel_install_is_no_index_and_offline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    poisoned = _poison_network_environment(monkeypatch)
    python = tmp_path / "installed/bin/python"
    wheel = tmp_path / "cellpose_mcp-0.1.4-py3-none-any.whl"
    calls: list[tuple[list[str], dict[str, object]]] = []

    def record_run(command: list[str], **kwargs: object) -> None:
        calls.append((command, kwargs))

    monkeypatch.setattr(subprocess, "run", record_run)

    _install_wheel(python, wheel)

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == [
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-index",
        "--no-deps",
        str(wheel),
    ]
    assert set(kwargs) == {"check", "env"}
    assert kwargs["check"] is True
    _assert_offline_environment(kwargs["env"], poisoned)
```

The first test requires dependency checking and the exact sanitized build
argv. The second requires the exact no-index/no-dependency install argv. Both
prove that the caller's poisoned environment remains unchanged.

Run only the three affected tests from the old checked environment:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_FULL_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_FULL_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_FULL_SHA:0:12}
[[ $FOUNDATION_RUN_SHA =~ ^[0-9a-f]{12}$ ]]
FOUNDATION_OFFLINE_CANDIDATE=/private/tmp/cellpose-mcp-foundation-offline-candidate-${FOUNDATION_RUN_SHA}
export FOUNDATION_OFFLINE_CANDIDATE
test -d "$FOUNDATION_OFFLINE_CANDIDATE/.git"
FOUNDATION_ROOT_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_ROOT/uv.lock" | /usr/bin/awk '{print $1}')
FOUNDATION_ROOT_CACHE=/private/tmp/cellpose-mcp-foundation-root-cache-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_ENV_311=/private/tmp/cellpose-mcp-foundation-root-py311-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_ENV_312=/private/tmp/cellpose-mcp-foundation-root-py312-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_HOME=/private/tmp/cellpose-mcp-foundation-root-home-${FOUNDATION_ROOT_LOCK_SHA}
FOUNDATION_ROOT_TMP=/private/tmp/cellpose-mcp-foundation-root-tmp-${FOUNDATION_ROOT_LOCK_SHA}
test -d "$FOUNDATION_ROOT_CACHE"
test -x "$FOUNDATION_ROOT_ENV_311/bin/python"
test -x "$FOUNDATION_ROOT_ENV_312/bin/python"
"$FOUNDATION_ROOT_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_ROOT_ENV_311" "$PY311"
"$FOUNDATION_ROOT_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_ROOT_ENV_312" "$PY312"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ROOT_HOME" TMPDIR="$FOUNDATION_ROOT_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_OFFLINE_CANDIDATE/src" UV_CACHE_DIR="$FOUNDATION_ROOT_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ROOT_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_OFFLINE_CANDIDATE" --project "$FOUNDATION_OFFLINE_CANDIDATE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev pytest -p no:cacheprovider tests/packaging/test_python_policy.py::test_required_foundation_dependencies_are_direct tests/packaging/test_distribution_contents.py::test_clean_clone_build_is_dependency_checked_and_offline tests/packaging/test_distribution_contents.py::test_wheel_install_is_no_index_and_offline -q
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: exactly three failures for missing mirrored backend requirements,
missing `--no-isolation`/sanitization, and missing `_install_wheel`.

- [ ] **Step 7: Implement the offline subprocess boundary**

Append these exact test-extra entries in candidate `pyproject.toml`, preserving
their order:

```toml
    "build>=1.2,<2",
    "setuptools>=64",
    "setuptools_scm>=8.0",
    "wheel",
```

Immediately after the `GIT` check in
`tests/packaging/test_distribution_contents.py`, add:

```python
_NETWORK_ENVIRONMENT_VARIABLES = frozenset(
    {
        "ALL_PROXY",
        "CURL_CA_BUNDLE",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "PIP_CERT",
        "PIP_CLIENT_CERT",
        "PIP_EXTRA_INDEX_URL",
        "PIP_FIND_LINKS",
        "PIP_INDEX_URL",
        "PIP_PROXY",
        "PIP_TRUSTED_HOST",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "all_proxy",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)


def _offline_subprocess_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in _NETWORK_ENVIRONMENT_VARIABLES:
        environment.pop(name, None)
    environment.update(
        {
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": "",
        }
    )
    return environment


def _install_wheel(python: Path, wheel: Path) -> None:
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-index",
            "--no-deps",
            str(wheel),
        ],
        check=True,
        env=_offline_subprocess_environment(),
    )
```

Change the build subprocess to add `--no-isolation` immediately after
`"build"`, retain the dependency check by omitting
`--skip-dependency-check`, and pass `env=_offline_subprocess_environment()`.
Replace the inline pip install with `_install_wheel(python, wheel)` and give
the final installed-metadata subprocess the same sanitized environment.

The two RED tests define `_poison_network_environment` and
`_assert_offline_environment`. The latter requires the network-variable set
to be disjoint from the child mapping and exactly:

```python
assert environment["PIP_CONFIG_FILE"] == os.devnull
assert environment["PIP_DISABLE_PIP_VERSION_CHECK"] == "1"
assert environment["PIP_NO_INDEX"] == "1"
assert environment["PYTHONNOUSERSITE"] == "1"
assert environment["PYTHONPATH"] == ""
```

It also proves every poisoned value is unchanged in `os.environ`.

- [ ] **Step 8: Refresh the lock, prove GREEN offline, and commit**

Under the single approved package-index boundary, refresh the candidate lock
and realize both candidate environments. This block may contact only
`https://pypi.org/simple` and artifact URLs beneath
`https://files.pythonhosted.org/`; it has no model-host authority. It rechecks
the exact root, branch, Phase 0 ancestor, candidate base commit, pinned
executables, and fresh path absence before provisioning:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_BASE_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_BASE_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_BASE_SHA:0:12}
FOUNDATION_OFFLINE_CANDIDATE=/private/tmp/cellpose-mcp-foundation-offline-candidate-${FOUNDATION_RUN_SHA}
export FOUNDATION_OFFLINE_CANDIDATE
test -d "$FOUNDATION_OFFLINE_CANDIDATE/.git"
test "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" rev-parse HEAD)" = "$FOUNDATION_BASE_SHA"
git -C "$FOUNDATION_OFFLINE_CANDIDATE" diff --cached --quiet

UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483

validate_network_sources() {
  "$PY312" -I - "$1" "$2" <<'PY'
from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

INDEX = "https://pypi.org/simple"
FILES_HOST = "files.pythonhosted.org"
project_path, lock_path = map(Path, sys.argv[1:])
project = tomllib.loads(project_path.read_text(encoding="utf-8"))
requirements = list(project["project"].get("dependencies", []))
for group in project["project"].get("optional-dependencies", {}).values():
    requirements.extend(group)
requirements.extend(project["build-system"].get("requires", []))
assert requirements and all(isinstance(item, str) for item in requirements)
assert all("@" not in item and "://" not in item for item in requirements)
assert "dependency-groups" not in project
uv_config = project.get("tool", {}).get("uv", {})
assert isinstance(uv_config, dict)
assert uv_config == {}


def check_url(value: str) -> None:
    parsed = urlsplit(value)
    assert parsed.scheme == "https", value
    assert parsed.username is None and parsed.password is None, value
    assert parsed.port is None and parsed.query == "" and parsed.fragment == "", value
    if value == INDEX:
        return
    assert parsed.hostname == FILES_HOST, value
    assert parsed.path.startswith("/packages/"), value


lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
for package in lock["package"]:
    source = package["source"]
    assert source in ({"registry": INDEX}, {"editable": "."}), source
    if "sdist" in package:
        check_url(package["sdist"]["url"])
    for wheel in package.get("wheels", []):
        check_url(wheel["url"])
PY
}

assert_no_repo_generated_state() {
  local repository=$1
  for relative in .pytest_cache .ruff_cache .mypy_cache build dist src/cellpose_mcp.egg-info; do
    test ! -e "$repository/$relative"
  done
  test -z "$(find "$repository" -type d -name __pycache__ -print -quit)"
}

validate_network_sources "$FOUNDATION_OFFLINE_CANDIDATE/pyproject.toml" "$FOUNDATION_OFFLINE_CANDIDATE/uv.lock"
assert_no_repo_generated_state "$FOUNDATION_OFFLINE_CANDIDATE"

FOUNDATION_RESOLVE_CACHE=/private/tmp/cellpose-mcp-foundation-resolve-cache-${FOUNDATION_BASE_SHA}
FOUNDATION_RESOLVE_HOME=/private/tmp/cellpose-mcp-foundation-resolve-home-${FOUNDATION_BASE_SHA}
FOUNDATION_RESOLVE_TMP=/private/tmp/cellpose-mcp-foundation-resolve-tmp-${FOUNDATION_BASE_SHA}
for private_directory in "$FOUNDATION_RESOLVE_CACHE" "$FOUNDATION_RESOLVE_HOME" "$FOUNDATION_RESOLVE_TMP"; do
  if test -e "$private_directory"; then test -d "$private_directory" && test ! -L "$private_directory" && test -O "$private_directory" && test "$(/usr/bin/stat -f '%Lp' "$private_directory")" = 700; else install -d -m 700 "$private_directory"; fi
done
if git -C "$FOUNDATION_OFFLINE_CANDIDATE" diff --quiet -- uv.lock; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_RESOLVE_HOME" TMPDIR="$FOUNDATION_RESOLVE_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_RESOLVE_CACHE" UV_DEFAULT_INDEX=https://pypi.org/simple UV_KEYRING_PROVIDER=disabled UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_OFFLINE_CANDIDATE" --project "$FOUNDATION_OFFLINE_CANDIDATE" --no-config lock --no-build --python "$PY312" --default-index https://pypi.org/simple --keyring-provider disabled --no-python-downloads
fi

FOUNDATION_CANDIDATE_LOCK_SHA=$(hash_file "$FOUNDATION_OFFLINE_CANDIDATE/uv.lock")
[[ $FOUNDATION_CANDIDATE_LOCK_SHA =~ ^[0-9a-f]{64}$ ]]
validate_network_sources "$FOUNDATION_OFFLINE_CANDIDATE/pyproject.toml" "$FOUNDATION_OFFLINE_CANDIDATE/uv.lock"
FOUNDATION_CANDIDATE_CACHE=/private/tmp/cellpose-mcp-foundation-offline-cache-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_ENV_311=/private/tmp/cellpose-mcp-foundation-offline-py311-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_ENV_312=/private/tmp/cellpose-mcp-foundation-offline-py312-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_HOME=/private/tmp/cellpose-mcp-foundation-offline-home-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_TMP=/private/tmp/cellpose-mcp-foundation-offline-tmp-${FOUNDATION_CANDIDATE_LOCK_SHA}
for private_directory in "$FOUNDATION_CANDIDATE_CACHE" "$FOUNDATION_CANDIDATE_HOME" "$FOUNDATION_CANDIDATE_TMP"; do
  if test -e "$private_directory"; then test -d "$private_directory" && test ! -L "$private_directory" && test -O "$private_directory" && test "$(/usr/bin/stat -f '%Lp' "$private_directory")" = 700; else install -d -m 700 "$private_directory"; fi
done
if ! test -e "$FOUNDATION_CANDIDATE_ENV_311"; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CANDIDATE_HOME" TMPDIR="$FOUNDATION_CANDIDATE_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_CANDIDATE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CANDIDATE_ENV_311" UV_DEFAULT_INDEX=https://pypi.org/simple UV_KEYRING_PROVIDER=disabled UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_OFFLINE_CANDIDATE" --project "$FOUNDATION_OFFLINE_CANDIDATE" --no-config sync --frozen --no-install-project --no-build --python "$PY311" --extra test --extra dev --default-index https://pypi.org/simple --keyring-provider disabled --no-python-downloads
fi
if ! test -e "$FOUNDATION_CANDIDATE_ENV_312"; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CANDIDATE_HOME" TMPDIR="$FOUNDATION_CANDIDATE_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_CANDIDATE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CANDIDATE_ENV_312" UV_DEFAULT_INDEX=https://pypi.org/simple UV_KEYRING_PROVIDER=disabled UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_OFFLINE_CANDIDATE" --project "$FOUNDATION_OFFLINE_CANDIDATE" --no-config sync --frozen --no-install-project --no-build --python "$PY312" --extra test --extra dev --default-index https://pypi.org/simple --keyring-provider disabled --no-python-downloads
fi

validate_network_sources "$FOUNDATION_OFFLINE_CANDIDATE/pyproject.toml" "$FOUNDATION_OFFLINE_CANDIDATE/uv.lock"
test "$(hash_file "$FOUNDATION_OFFLINE_CANDIDATE/uv.lock")" = "$FOUNDATION_CANDIDATE_LOCK_SHA"
"$FOUNDATION_CANDIDATE_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_CANDIDATE_ENV_311" "$PY311"
"$FOUNDATION_CANDIDATE_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_CANDIDATE_ENV_312" "$PY312"
assert_no_repo_generated_state "$FOUNDATION_OFFLINE_CANDIDATE"
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Then revoke network use. Every subsequent uv execution is frozen, offline,
non-syncing, config-free, and unable to download Python:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_FULL_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_FULL_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_FULL_SHA:0:12}
[[ $FOUNDATION_RUN_SHA =~ ^[0-9a-f]{12}$ ]]
FOUNDATION_OFFLINE_CANDIDATE=/private/tmp/cellpose-mcp-foundation-offline-candidate-${FOUNDATION_RUN_SHA}
export FOUNDATION_OFFLINE_CANDIDATE
test -d "$FOUNDATION_OFFLINE_CANDIDATE/.git"
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_CANDIDATE_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_OFFLINE_CANDIDATE/uv.lock" | /usr/bin/awk '{print $1}')
FOUNDATION_CANDIDATE_CACHE=/private/tmp/cellpose-mcp-foundation-offline-cache-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_ENV_311=/private/tmp/cellpose-mcp-foundation-offline-py311-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_ENV_312=/private/tmp/cellpose-mcp-foundation-offline-py312-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_HOME=/private/tmp/cellpose-mcp-foundation-offline-home-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_TMP=/private/tmp/cellpose-mcp-foundation-offline-tmp-${FOUNDATION_CANDIDATE_LOCK_SHA}
test -d "$FOUNDATION_CANDIDATE_CACHE"
test -x "$FOUNDATION_CANDIDATE_ENV_311/bin/python"
test -x "$FOUNDATION_CANDIDATE_ENV_312/bin/python"
"$FOUNDATION_CANDIDATE_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_CANDIDATE_ENV_311" "$PY311"
"$FOUNDATION_CANDIDATE_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_CANDIDATE_ENV_312" "$PY312"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CANDIDATE_HOME" TMPDIR="$FOUNDATION_CANDIDATE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_OFFLINE_CANDIDATE/src" UV_CACHE_DIR="$FOUNDATION_CANDIDATE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CANDIDATE_ENV_311" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_OFFLINE_CANDIDATE" --project "$FOUNDATION_OFFLINE_CANDIDATE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY311" --extra test --extra dev pytest -p no:cacheprovider tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CANDIDATE_HOME" TMPDIR="$FOUNDATION_CANDIDATE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_OFFLINE_CANDIDATE/src" UV_CACHE_DIR="$FOUNDATION_CANDIDATE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CANDIDATE_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_OFFLINE_CANDIDATE" --project "$FOUNDATION_OFFLINE_CANDIDATE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev pytest -p no:cacheprovider tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CANDIDATE_HOME" TMPDIR="$FOUNDATION_CANDIDATE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_OFFLINE_CANDIDATE/src" UV_CACHE_DIR="$FOUNDATION_CANDIDATE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CANDIDATE_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_OFFLINE_CANDIDATE" --project "$FOUNDATION_OFFLINE_CANDIDATE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev ruff check --no-fix --no-cache tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py
for relative in .pytest_cache .ruff_cache .mypy_cache build dist src/cellpose_mcp.egg-info; do
  test ! -e "$FOUNDATION_OFFLINE_CANDIDATE/$relative"
done
test -z "$(find "$FOUNDATION_OFFLINE_CANDIDATE" -type d -name __pycache__ -print -quit)"
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: `24 passed` on each version (5 policy plus 19 distribution), then
Ruff passes. Transfer the candidate with this no-overwrite, exact-four-file
patch gate. It proves the candidate has no fifth path, the dirty root has no
pre-existing lock or distribution-test delta, the patch destination is new,
and the staged blob for every path exactly matches the candidate worktree:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_FULL_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_FULL_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_FULL_SHA:0:12}
[[ $FOUNDATION_RUN_SHA =~ ^[0-9a-f]{12}$ ]]
FOUNDATION_OFFLINE_CANDIDATE=/private/tmp/cellpose-mcp-foundation-offline-candidate-${FOUNDATION_RUN_SHA}
test "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" rev-parse HEAD)" = "$(git rev-parse HEAD)"
git -C "$FOUNDATION_OFFLINE_CANDIDATE" diff --cached --quiet
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
EXPECTED_PATHS=$'pyproject.toml\ntests/packaging/test_distribution_contents.py\ntests/packaging/test_python_policy.py\nuv.lock'
test "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" diff --name-only)" = "$EXPECTED_PATHS"
git diff --quiet -- uv.lock tests/packaging/test_distribution_contents.py
FOUNDATION_CANDIDATE_LOCK_SHA=$(hash_file "$FOUNDATION_OFFLINE_CANDIDATE/uv.lock")
FOUNDATION_CANDIDATE_ENV_311=/private/tmp/cellpose-mcp-foundation-offline-py311-${FOUNDATION_CANDIDATE_LOCK_SHA}
FOUNDATION_CANDIDATE_ENV_312=/private/tmp/cellpose-mcp-foundation-offline-py312-${FOUNDATION_CANDIDATE_LOCK_SHA}
"$FOUNDATION_CANDIDATE_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_CANDIDATE_ENV_311" "$PY311"
"$FOUNDATION_CANDIDATE_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_CANDIDATE_ENV_312" "$PY312"

FOUNDATION_PATCH=/private/tmp/cellpose-mcp-phase0-offline-${FOUNDATION_RUN_SHA}.patch
[[ $FOUNDATION_PATCH == /private/tmp/cellpose-mcp-phase0-offline-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f].patch ]]
if test -e "$FOUNDATION_PATCH"; then
  test -f "$FOUNDATION_PATCH" && test ! -L "$FOUNDATION_PATCH" && test -O "$FOUNDATION_PATCH"
else
  git -C "$FOUNDATION_OFFLINE_CANDIDATE" diff --binary --output="$FOUNDATION_PATCH" -- pyproject.toml tests/packaging/test_distribution_contents.py tests/packaging/test_python_policy.py uv.lock
fi
test -s "$FOUNDATION_PATCH"
FOUNDATION_PATCH_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_PATCH" | /usr/bin/awk '{print $1}')
[[ $FOUNDATION_PATCH_SHA =~ ^[0-9a-f]{64}$ ]]
FOUNDATION_EXPECTED=/private/tmp/cellpose-mcp-phase0-offline-expected-${FOUNDATION_RUN_SHA}
if test -e "$FOUNDATION_EXPECTED"; then
  test -d "$FOUNDATION_EXPECTED" && test ! -L "$FOUNDATION_EXPECTED"
else
  git clone --no-hardlinks --local . "$FOUNDATION_EXPECTED"
fi
test "$(git -C "$FOUNDATION_EXPECTED" rev-parse HEAD)" = "$(git rev-parse HEAD)"
if git -C "$FOUNDATION_EXPECTED" apply --reverse --check "$FOUNDATION_PATCH"; then
  : # already contains the complete expected post-patch tree
else
  if test -z "$(git -C "$FOUNDATION_EXPECTED" status --porcelain)"; then
    /bin/cp "$FOUNDATION_ROOT/pyproject.toml" "$FOUNDATION_EXPECTED/pyproject.toml"
    /bin/cp "$FOUNDATION_ROOT/tests/packaging/test_python_policy.py" "$FOUNDATION_EXPECTED/tests/packaging/test_python_policy.py"
  fi
  git -C "$FOUNDATION_EXPECTED" apply --check "$FOUNDATION_PATCH"
  git -C "$FOUNDATION_EXPECTED" apply "$FOUNDATION_PATCH"
fi
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_PATCH" | /usr/bin/awk '{print $1}')" = "$FOUNDATION_PATCH_SHA"
git apply --check "$FOUNDATION_PATCH"
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_PATCH" | /usr/bin/awk '{print $1}')" = "$FOUNDATION_PATCH_SHA"
git apply "$FOUNDATION_PATCH"
test "$(git diff --name-only -- pyproject.toml tests/packaging/test_distribution_contents.py tests/packaging/test_python_policy.py uv.lock)" = "$EXPECTED_PATHS"
git apply --reverse --check "$FOUNDATION_PATCH"
for expected_path in pyproject.toml tests/packaging/test_python_policy.py; do
  test "$(git hash-object "$expected_path")" = "$(git -C "$FOUNDATION_EXPECTED" hash-object "$expected_path")"
done
for candidate_path in tests/packaging/test_distribution_contents.py uv.lock; do
  test "$(git hash-object "$candidate_path")" = "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" hash-object "$candidate_path")"
done
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_PATCH" | /usr/bin/awk '{print $1}')" = "$FOUNDATION_PATCH_SHA"
git apply --cached --check "$FOUNDATION_PATCH"
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_PATCH" | /usr/bin/awk '{print $1}')" = "$FOUNDATION_PATCH_SHA"
git apply --cached "$FOUNDATION_PATCH"
test "$(git diff --cached --name-only)" = "$EXPECTED_PATHS"
for staged_path in pyproject.toml tests/packaging/test_distribution_contents.py tests/packaging/test_python_policy.py uv.lock; do
  test "$(git rev-parse ":$staged_path")" = "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" hash-object "$staged_path")"
done
git diff --cached --check
git commit -m "test: make distribution proof offline"
test "$(git log -1 --format=%s)" = "test: make distribution proof offline"
test "$(git diff-tree --no-commit-id --name-only -r HEAD)" = "$EXPECTED_PATHS"
test "$(git rev-parse HEAD^)" = "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" rev-parse HEAD)"
for committed_path in pyproject.toml tests/packaging/test_distribution_contents.py tests/packaging/test_python_policy.py uv.lock; do
  test "$(git rev-parse "HEAD:$committed_path")" = "$(git -C "$FOUNDATION_OFFLINE_CANDIDATE" hash-object "$committed_path")"
done
git diff --quiet -- uv.lock tests/packaging/test_distribution_contents.py
git diff --cached --quiet
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: before commit, the index is exactly:

```text
pyproject.toml
tests/packaging/test_distribution_contents.py
tests/packaging/test_python_policy.py
uv.lock
```

After commit the two clean-root files are clean, while only the pre-existing
user hunks remain in `pyproject.toml` and the policy test.

- [ ] **Step 9: Tighten Python metadata and CI policy tests**

Add this constant immediately below `ROOT` in
`tests/packaging/test_python_policy.py`:

```python
EXPECTED_CLASSIFIERS = [
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
```

Replace the classifier assertions in
`test_public_python_range_and_classifiers_are_exact` with:

```python
    assert project["classifiers"] == EXPECTED_CLASSIFIERS
```

Leave the exact strengthened
`test_required_foundation_dependencies_are_direct` implementation from Step 6
unchanged. Root runtime dependencies remain transitional under the approved
stable-v4 amendment, while the build-system requirements and their mirrors in
the test extra are exact.

In the clean candidate, append these two CI tests exactly. In the dirty root,
replace the inventoried user-owned `test_ci_uses_locked_uv_on_both_supported_versions`
hunk with this validated version and append the truthfulness test; no other
policy-test bytes change:

```python
def test_ci_uses_locked_uv_on_both_supported_versions() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(workflow.split())
    foundation_tests = (
        "pytest -p no:cacheprovider tests/dev/test_inventory_worktree.py "
        "tests/contract/test_feature_manifest.py "
        "tests/packaging/test_python_policy.py "
        "tests/packaging/test_distribution_contents.py -q"
    )

    assert 'python-version: ["3.11", "3.12"]' in normalized
    assert 'python-version: ["3.10", "3.11", "3.12"]' not in normalized
    assert 'python -m pip install "uv==0.10.4"' in normalized
    assert "uv sync --locked" in normalized
    assert "--no-install-project --no-build" in normalized
    assert 'echo "$PWD/.venv/bin" >> "$GITHUB_PATH"' in normalized
    assert "uv lock --check" in normalized
    assert "uv run --frozen --offline --no-sync" in normalized
    assert "sys.version_info.major" in normalized
    assert "python scripts/check_feature_manifest.py" in normalized
    assert foundation_tests in normalized
    assert "- name: Ruff foundation" in normalized
    assert "ruff check --no-fix" in normalized
    assert "--no-cache" in normalized
    assert "-p no:cacheprovider" in normalized
    assert "src/cellpose_mcp/release" in normalized
    assert "scripts/check_feature_manifest.py" in normalized
    assert "scripts/inventory_worktree.py" in normalized
    assert "tests/dev/test_inventory_worktree.py" in normalized
    assert "tests/contract/test_feature_manifest.py" in normalized
    assert "tests/packaging" in normalized
    assert "ruff check --no-fix src/ tests/" not in normalized
    assert "mypy --cache-dir" in normalized


def test_ci_is_truthfully_foundation_only() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert workflow.startswith("name: Foundation CI\n")

    separator = "\njobs:\n"
    assert separator in workflow
    jobs = workflow.split(separator, maxsplit=1)[1]
    job_names = [
        line[2:-1]
        for line in jobs.splitlines()
        if line.startswith("  ")
        and not line.startswith("    ")
        and line.endswith(":")
    ]
    assert job_names == ["foundation"]

    forbidden = (
        "pytest -m ",
        "install-e2e:",
        "install_e2e",
        "tests/test_installation.py",
        "test_fresh_venv_wheel_install_segment_e2e",
    )
    assert not any(fragment in workflow for fragment in forbidden)
```

Also replace the checker's eager package import with the approved shared
loader below. The synthetic package is inserted but its loader is deliberately
not executed; only the release contract module is executed under its canonical
name:

```python
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

FEATURE_MANIFEST_MODULE_NAME = "cellpose_mcp.release.feature_manifest"


def load_feature_manifest_module() -> ModuleType:
    """Load the real release contract without running the legacy package."""
    loaded = sys.modules.get(FEATURE_MANIFEST_MODULE_NAME)
    if loaded is not None:
        return loaded
    root = Path(__file__).resolve().parents[1]
    package_dir = root / "src/cellpose_mcp"
    package_spec = importlib.util.spec_from_file_location(
        "cellpose_mcp",
        package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)],
    )
    if package_spec is None or package_spec.loader is None:
        raise RuntimeError("cannot create the cellpose_mcp package spec")
    sys.modules[package_spec.name] = importlib.util.module_from_spec(package_spec)
    module_spec = importlib.util.spec_from_file_location(
        FEATURE_MANIFEST_MODULE_NAME,
        package_dir / "release/feature_manifest.py",
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("cannot create the feature manifest module spec")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


FEATURE_MANIFEST = load_feature_manifest_module()
load_feature_manifest = FEATURE_MANIFEST.load_feature_manifest
release_gate_failures = FEATURE_MANIFEST.release_gate_failures
```

In `tests/contract/test_feature_manifest.py`, load that real checker with an
`importlib.util.spec_from_file_location` spec named
`_cellpose_mcp_check_feature_manifest`, insert it in `sys.modules`, execute it
once, and alias every manifest constant/class/function from
`CHECK_MODULE.FEATURE_MANIFEST`. Extend the structural test with:

```python
    assert manifest.__class__ is BootstrapFeatureManifest
    serialized = pickle.dumps(manifest)
    assert b"cellpose_mcp.release.feature_manifest" in serialized
    assert_legacy_runtime_absent()
```

`assert_legacy_runtime_absent` rejects `cellpose`, `cellpose_mcp.server`,
`cellpose_mcp.tools`, `fastmcp`, `rich`, `torch`, and `typer` in
`sys.modules`. These two import-isolation edits are candidate-owned and are
part of the final four-path CI commit.

- [ ] **Step 10: Prove the new truthfulness assertion is RED**

Create a local clean candidate clone from the now-current commit; do not copy
untracked files or the dirty root worktree:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_BASE_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_BASE_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_BASE_SHA:0:12}
FOUNDATION_CANDIDATE=/private/tmp/cellpose-mcp-foundation-ci-candidate-${FOUNDATION_RUN_SHA}
export FOUNDATION_CANDIDATE
if test -e "$FOUNDATION_CANDIDATE"; then
  test -d "$FOUNDATION_CANDIDATE" && test ! -L "$FOUNDATION_CANDIDATE"
  test "$(git -C "$FOUNDATION_CANDIDATE" rev-parse HEAD)" = "$FOUNDATION_BASE_SHA"
  test -z "$(git -C "$FOUNDATION_CANDIDATE" status --porcelain)"
else
  git clone --no-hardlinks --local . "$FOUNDATION_CANDIDATE"
fi
test "$(git -C "$FOUNDATION_CANDIDATE" rev-parse HEAD)" = "$FOUNDATION_BASE_SHA"
test -z "$(git -C "$FOUNDATION_CANDIDATE" status --porcelain)"
test ! -e "$FOUNDATION_CANDIDATE/tests/test_installation.py"

UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_CI_LOCK_SHA=$(hash_file "$FOUNDATION_CANDIDATE/uv.lock")
FOUNDATION_SOURCE_CACHE=/private/tmp/cellpose-mcp-foundation-offline-cache-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_CACHE=/private/tmp/cellpose-mcp-foundation-ci-cache-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_ENV_311=/private/tmp/cellpose-mcp-foundation-ci-py311-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_ENV_312=/private/tmp/cellpose-mcp-foundation-ci-py312-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_HOME=/private/tmp/cellpose-mcp-foundation-ci-home-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_TMP=/private/tmp/cellpose-mcp-foundation-ci-tmp-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
test -d "$FOUNDATION_SOURCE_CACHE"
if test -e "$FOUNDATION_CI_CACHE"; then test -d "$FOUNDATION_CI_CACHE" && test ! -L "$FOUNDATION_CI_CACHE" && test -O "$FOUNDATION_CI_CACHE"; else /bin/cp -R "$FOUNDATION_SOURCE_CACHE" "$FOUNDATION_CI_CACHE"; fi
for private_directory in "$FOUNDATION_CI_HOME" "$FOUNDATION_CI_TMP"; do
  if test -e "$private_directory"; then test -d "$private_directory" && test ! -L "$private_directory" && test -O "$private_directory" && test "$(/usr/bin/stat -f '%Lp' "$private_directory")" = 700; else install -d -m 700 "$private_directory"; fi
done
if ! test -e "$FOUNDATION_CI_ENV_311"; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CI_HOME" TMPDIR="$FOUNDATION_CI_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_CI_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CI_ENV_311" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_CANDIDATE" --project "$FOUNDATION_CANDIDATE" --no-config sync --frozen --offline --no-install-project --no-build --python "$PY311" --extra test --extra dev --no-python-downloads
fi
if ! test -e "$FOUNDATION_CI_ENV_312"; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CI_HOME" TMPDIR="$FOUNDATION_CI_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_CI_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CI_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_CANDIDATE" --project "$FOUNDATION_CANDIDATE" --no-config sync --frozen --offline --no-install-project --no-build --python "$PY312" --extra test --extra dev --no-python-downloads
fi
"$FOUNDATION_CI_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_CI_ENV_311" "$PY311"
"$FOUNDATION_CI_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_CI_ENV_312" "$PY312"
for relative in .pytest_cache .ruff_cache .mypy_cache build dist src/cellpose_mcp.egg-info; do
  test ! -e "$FOUNDATION_CANDIDATE/$relative"
done
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Apply only the policy/CI assertions from Step 9 to the candidate with
`apply_patch`, then run:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_BASE_SHA=$(git rev-parse HEAD)
FOUNDATION_RUN_SHA=${FOUNDATION_BASE_SHA:0:12}
FOUNDATION_CANDIDATE=/private/tmp/cellpose-mcp-foundation-ci-candidate-${FOUNDATION_RUN_SHA}
export FOUNDATION_CANDIDATE
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_CI_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_CANDIDATE/uv.lock" | /usr/bin/awk '{print $1}')
FOUNDATION_CI_CACHE=/private/tmp/cellpose-mcp-foundation-ci-cache-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_ENV_312=/private/tmp/cellpose-mcp-foundation-ci-py312-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_HOME=/private/tmp/cellpose-mcp-foundation-ci-home-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_TMP=/private/tmp/cellpose-mcp-foundation-ci-tmp-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
test -x "$FOUNDATION_CI_ENV_312/bin/python"
"$FOUNDATION_CI_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_CI_ENV_312" "$PY312"
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CI_HOME" TMPDIR="$FOUNDATION_CI_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_CANDIDATE/src" UV_CACHE_DIR="$FOUNDATION_CI_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CI_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_CANDIDATE" --project "$FOUNDATION_CANDIDATE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev pytest -p no:cacheprovider tests/packaging/test_python_policy.py::test_ci_is_truthfully_foundation_only -q
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: one failure at
`workflow.startswith("name: Foundation CI\\n")`; the candidate still has the
committed legacy workflow at this point.

- [ ] **Step 11: Replace the candidate workflow with the exact foundation gate**

Use `apply_patch` in the clean candidate so
`.github/workflows/ci.yml` is exactly:

```yaml
name: Foundation CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  foundation:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]

    env:
      PYTHONDONTWRITEBYTECODE: "1"
      PYTHONPATH: ${{ github.workspace }}/src

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install locked environment
        run: |
          python -m pip install "uv==0.10.4"
          uv sync --locked --no-install-project --no-build --python "${{ matrix.python-version }}" --extra test --extra dev
          echo "$PWD/.venv/bin" >> "$GITHUB_PATH"

      - name: Foundation contract
        run: |
          uv lock --check --offline --no-python-downloads --no-config
          uv run --frozen --offline --no-sync --no-python-downloads --no-config --python "${{ matrix.python-version }}" --extra test --extra dev python -c "import sys; assert f'{sys.version_info.major}.{sys.version_info.minor}' == '${{ matrix.python-version }}'"
          uv run --frozen --offline --no-sync --no-python-downloads --no-config --python "${{ matrix.python-version }}" --extra test --extra dev python scripts/check_feature_manifest.py
          uv run --frozen --offline --no-sync --no-python-downloads --no-config --python "${{ matrix.python-version }}" --extra test --extra dev pytest -p no:cacheprovider tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q

      - name: Ruff foundation
        run: >
          uv run --frozen --offline --no-sync --no-python-downloads --no-config
          --python "${{ matrix.python-version }}"
          --extra test --extra dev ruff check --no-fix --no-cache
          src/cellpose_mcp/release
          scripts/check_feature_manifest.py
          scripts/inventory_worktree.py
          tests/dev/test_inventory_worktree.py
          tests/contract/test_feature_manifest.py
          tests/packaging

      - name: Mypy foundation
        run: >
          uv run --frozen --offline --no-sync --no-python-downloads --no-config
          --python "${{ matrix.python-version }}"
          --extra test --extra dev mypy
          --cache-dir "${{ runner.temp }}/mypy-${{ matrix.python-version }}"
          --python-version "${{ matrix.python-version }}"
          src/cellpose_mcp/release scripts/check_feature_manifest.py
          scripts/inventory_worktree.py
```

There is deliberately no broad Pytest step and no install-E2E job. Those
features are not deleted here; they remain preserved user work and cannot be
advertised until the replacement controller and real installed journeys pass.

- [ ] **Step 12: Verify GREEN in isolated Python 3.11 and 3.12 environments**

Run in the candidate clone. The two wrapper functions below are the only uv
execution boundary: both sanitize the process environment and always include
`--frozen --offline --no-sync --no-python-downloads --no-config`.
JUnit parsing mechanically proves the exact 60-test result instead of trusting
the terminal summary:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_BASE_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_BASE_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_BASE_SHA:0:12}
FOUNDATION_CANDIDATE=/private/tmp/cellpose-mcp-foundation-ci-candidate-${FOUNDATION_RUN_SHA}
export FOUNDATION_CANDIDATE
test "$(git -C "$FOUNDATION_CANDIDATE" rev-parse HEAD)" = "$FOUNDATION_BASE_SHA"
git -C "$FOUNDATION_CANDIDATE" diff --cached --quiet
test -z "$(git -C "$FOUNDATION_CANDIDATE" ls-files --others --exclude-standard)"
EXPECTED_CANDIDATE_PATHS=$'.github/workflows/ci.yml\nscripts/check_feature_manifest.py\ntests/contract/test_feature_manifest.py\ntests/packaging/test_python_policy.py'
test "$(git -C "$FOUNDATION_CANDIDATE" diff --name-only)" = "$EXPECTED_CANDIDATE_PATHS"

UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_CI_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_CANDIDATE/uv.lock" | /usr/bin/awk '{print $1}')
FOUNDATION_CI_CACHE=/private/tmp/cellpose-mcp-foundation-ci-cache-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_ENV_311=/private/tmp/cellpose-mcp-foundation-ci-py311-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_ENV_312=/private/tmp/cellpose-mcp-foundation-ci-py312-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_HOME=/private/tmp/cellpose-mcp-foundation-ci-home-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_TMP=/private/tmp/cellpose-mcp-foundation-ci-tmp-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
test -d "$FOUNDATION_CI_CACHE"
test -x "$FOUNDATION_CI_ENV_311/bin/python"
test -x "$FOUNDATION_CI_ENV_312/bin/python"
foundation_run_311() {
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CI_HOME" TMPDIR="$FOUNDATION_CI_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_CANDIDATE/src" UV_CACHE_DIR="$FOUNDATION_CI_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CI_ENV_311" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_CANDIDATE" --project "$FOUNDATION_CANDIDATE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY311" --extra test --extra dev "$@"
}
foundation_run_312() {
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_CI_HOME" TMPDIR="$FOUNDATION_CI_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_CANDIDATE/src" UV_CACHE_DIR="$FOUNDATION_CI_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_CI_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_CANDIDATE" --project "$FOUNDATION_CANDIDATE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev "$@"
}

JUNIT_311="$FOUNDATION_CI_TMP/foundation-60-py311.xml"
JUNIT_312="$FOUNDATION_CI_TMP/foundation-60-py312.xml"
foundation_run_311 "$FOUNDATION_CI_ENV_311/bin/python" -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_CI_ENV_311" "$PY311"
if test -e "$JUNIT_311"; then
  test -f "$JUNIT_311" && test ! -L "$JUNIT_311"; echo "reusing JUnit sha256=$(hash_file "$JUNIT_311")"
else
  set +e
  foundation_run_311 pytest -p no:cacheprovider tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q --junitxml="$JUNIT_311"
  JUNIT_STATUS=$?
  set -e
  if test "$JUNIT_STATUS" -ne 0; then FAILED_JUNIT_SHA=$(hash_file "$JUNIT_311"); JUNIT_RETRY="${JUNIT_311%.xml}.retry-${FAILED_JUNIT_SHA:0:12}.xml"; test ! -e "$JUNIT_RETRY"; echo "retained $FAILED_JUNIT_SHA; retry only at $JUNIT_RETRY" >&2; exit "$JUNIT_STATUS"; fi
fi
foundation_run_311 python -c 'import sys,xml.etree.ElementTree as ET; r=ET.parse(sys.argv[1]).getroot(); s=[r] if r.tag=="testsuite" else list(r.findall("testsuite")); actual={k:sum(int(x.get(k,"0")) for x in s) for k in ("tests","failures","errors","skipped")}; assert actual=={"tests":60,"failures":0,"errors":0,"skipped":0},actual' "$JUNIT_311"
foundation_run_312 "$FOUNDATION_CI_ENV_312/bin/python" -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_CI_ENV_312" "$PY312"
if test -e "$JUNIT_312"; then
  test -f "$JUNIT_312" && test ! -L "$JUNIT_312"; echo "reusing JUnit sha256=$(hash_file "$JUNIT_312")"
else
  set +e
  foundation_run_312 pytest -p no:cacheprovider tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q --junitxml="$JUNIT_312"
  JUNIT_STATUS=$?
  set -e
  if test "$JUNIT_STATUS" -ne 0; then FAILED_JUNIT_SHA=$(hash_file "$JUNIT_312"); JUNIT_RETRY="${JUNIT_312%.xml}.retry-${FAILED_JUNIT_SHA:0:12}.xml"; test ! -e "$JUNIT_RETRY"; echo "retained $FAILED_JUNIT_SHA; retry only at $JUNIT_RETRY" >&2; exit "$JUNIT_STATUS"; fi
fi
foundation_run_312 python -c 'import sys,xml.etree.ElementTree as ET; r=ET.parse(sys.argv[1]).getroot(); s=[r] if r.tag=="testsuite" else list(r.findall("testsuite")); actual={k:sum(int(x.get(k,"0")) for x in s) for k in ("tests","failures","errors","skipped")}; assert actual=={"tests":60,"failures":0,"errors":0,"skipped":0},actual' "$JUNIT_312"

foundation_run_311 ruff check --no-fix --no-cache src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging
foundation_run_311 mypy --cache-dir "$FOUNDATION_CI_TMP/mypy-py311" --python-version 3.11 src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py
foundation_run_312 ruff check --no-fix --no-cache src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging
foundation_run_312 mypy --cache-dir "$FOUNDATION_CI_TMP/mypy-py312" --python-version 3.12 src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py
foundation_run_312 python -c 'import subprocess,sys; result=subprocess.run([sys.executable,"scripts/check_feature_manifest.py"],check=False,capture_output=True,text=True); assert result.returncode==0; assert result.stdout=="bootstrap manifest valid; release blockers: 14\n"; assert result.stderr==""'
foundation_run_312 python -c 'import subprocess,sys; tools=["get_capabilities","inspect_image","list_models","prepare_model","segment","refine_segmentation","measure_masks","evaluate_segmentation","export_segmentation","train_model","restore_image","get_job","cancel_job"]; result=subprocess.run([sys.executable,"scripts/check_feature_manifest.py","--release"],check=False,capture_output=True,text=True); lines=result.stdout.splitlines(); assert result.returncode==1; assert result.stderr==""; assert len(lines)==14; assert lines[0].startswith("unresolved_core_matrix: core_capability_matrix_unresolved:"); assert [line.split(": ",2)[1] for line in lines[1:]]==tools'
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_CANDIDATE/uv.lock" | /usr/bin/awk '{print $1}')" = "$FOUNDATION_CI_LOCK_SHA"
git -C "$FOUNDATION_CANDIDATE" diff --quiet -- uv.lock
for relative in .pytest_cache .ruff_cache .mypy_cache build dist src/cellpose_mcp.egg-info; do
  test ! -e "$FOUNDATION_CANDIDATE/$relative"
done
test -z "$(find "$FOUNDATION_CANDIDATE" -type d -name __pycache__ -print -quit)"
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: the interpreter assertions and JUnit total assertions pass with
exactly 60 passed tests on each version (28 inventory, 6 manifest, 7 policy,
and 19 distribution). Ruff and mypy pass on both versions. Development mode
has the exact one-line output; the inner release command returns 1 with the
exact ordered 14 blockers. The lock hash remains unchanged.

- [ ] **Step 13: Preserve the user-owned CI suffix while aligning the prefix**

Before editing the dirty root, record the exact preserved bytes:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
"$PY312" -I -c 'from pathlib import Path; import hashlib; p=Path(".github/workflows/ci.yml").read_bytes(); marker=b"      - name: Pytest\n"; tail=p[p.index(marker):]; assert hashlib.sha256(tail).hexdigest()=="869a85e6af80aefddde2614d0953d96ed1fcbc688f3fb6aaea16ff0ace6ab790"'
"$PY312" -I -c 'from pathlib import Path; import hashlib; assert hashlib.sha256(Path("tests/test_installation.py").read_bytes()).hexdigest()=="3e4ef691dcb3b7f7f59c8cc5743626a5279d33b3fb848e09f3ff56206c52996d"'
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Use `apply_patch` to make only the workflow prefix match the candidate through
the `Mypy foundation` step. Retain the suffix beginning with
`      - name: Pytest` byte-for-byte. Apply the finalized policy-test edit from
the candidate to the dirty root, and apply the two manifest import-isolation
edits to `scripts/check_feature_manifest.py` and
`tests/contract/test_feature_manifest.py`. Then rerun both hash assertions
above. The candidate reverse-check in Step 14 must succeed for all four paths;
that is the proof that the dirty worktree contains the candidate bytes before
the patch is applied to the index only.

The dirty root's truthfulness test is expected to fail while this preserved
suffix exists. The clean candidate is the authoritative validation source.
The split invariant is: the worktree workflow equals the exact committed
candidate prefix followed by the inventoried suffix whose SHA-256 is
`869a85e6af80aefddde2614d0953d96ed1fcbc688f3fb6aaea16ff0ace6ab790`;
only the candidate prefix enters the index.

- [ ] **Step 14: Stage the exact clean candidate diff, never the dirty suffix**

Generate and validate a four-file binary patch:

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_BASE_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_BASE_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_BASE_SHA:0:12}
[[ $FOUNDATION_RUN_SHA =~ ^[0-9a-f]{12}$ ]]
FOUNDATION_CANDIDATE=/private/tmp/cellpose-mcp-foundation-ci-candidate-${FOUNDATION_RUN_SHA}
export FOUNDATION_CANDIDATE
test "$(git -C "$FOUNDATION_CANDIDATE" rev-parse HEAD)" = "$FOUNDATION_BASE_SHA"
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_CI_LOCK_SHA=$(hash_file "$FOUNDATION_CANDIDATE/uv.lock")
FOUNDATION_CI_ENV_311=/private/tmp/cellpose-mcp-foundation-ci-py311-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_ENV_312=/private/tmp/cellpose-mcp-foundation-ci-py312-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
test -x "$FOUNDATION_CI_ENV_311/bin/python"
test -x "$FOUNDATION_CI_ENV_312/bin/python"
"$FOUNDATION_CI_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_CI_ENV_311" "$PY311"
"$FOUNDATION_CI_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_CI_ENV_312" "$PY312"
EXPECTED_PATHS=$'.github/workflows/ci.yml\nscripts/check_feature_manifest.py\ntests/contract/test_feature_manifest.py\ntests/packaging/test_python_policy.py'
test "$(git -C "$FOUNDATION_CANDIDATE" diff --name-only)" = "$EXPECTED_PATHS"
FOUNDATION_PATCH=/private/tmp/cellpose-mcp-phase0-ci-${FOUNDATION_RUN_SHA}.patch
[[ $FOUNDATION_PATCH == /private/tmp/cellpose-mcp-phase0-ci-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f].patch ]]
export FOUNDATION_PATCH
if test -e "$FOUNDATION_PATCH"; then
  test -f "$FOUNDATION_PATCH" && test ! -L "$FOUNDATION_PATCH" && test -O "$FOUNDATION_PATCH"
else
  git -C "$FOUNDATION_CANDIDATE" diff --binary --output="$FOUNDATION_PATCH" -- .github/workflows/ci.yml scripts/check_feature_manifest.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py
fi
test -s "$FOUNDATION_PATCH"
FOUNDATION_PATCH_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_PATCH" | /usr/bin/awk '{print $1}')
[[ $FOUNDATION_PATCH_SHA =~ ^[0-9a-f]{64}$ ]]
git apply --reverse --check "$FOUNDATION_PATCH"
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_PATCH" | /usr/bin/awk '{print $1}')" = "$FOUNDATION_PATCH_SHA"
git apply --cached --check "$FOUNDATION_PATCH"
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_PATCH" | /usr/bin/awk '{print $1}')" = "$FOUNDATION_PATCH_SHA"
git apply --cached "$FOUNDATION_PATCH"
git diff --cached --check
test "$(git diff --cached --name-only)" = "$EXPECTED_PATHS"
for staged_path in .github/workflows/ci.yml scripts/check_feature_manifest.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py; do
  test "$(git rev-parse ":$staged_path")" = "$(git -C "$FOUNDATION_CANDIDATE" hash-object "$staged_path")"
done
"$PY312" -I -c 'import subprocess; w=subprocess.check_output(["git","show",":.github/workflows/ci.yml"],text=True); assert w.startswith("name: Foundation CI\n"); assert "\n  foundation:\n" in w; assert "pytest -m " not in w; assert "install-e2e:" not in w; assert "tests/test_installation.py" not in w'
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

The final assertion inspects the indexed workflow, not the dirty worktree
version.

Expected: exactly the four planned files are staged and the indexed workflow
is foundation-only. `git apply --reverse --check` proves that the dirty root's
approved prefix already matches the candidate before the index-only apply.

- [ ] **Step 15: Commit CI and prove the preserved work survived**

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
FOUNDATION_BASE_SHA=$(git rev-parse HEAD)
[[ $FOUNDATION_BASE_SHA =~ ^[0-9a-f]{40}$ ]]
FOUNDATION_RUN_SHA=${FOUNDATION_BASE_SHA:0:12}
FOUNDATION_CANDIDATE=/private/tmp/cellpose-mcp-foundation-ci-candidate-${FOUNDATION_RUN_SHA}
test "$(git -C "$FOUNDATION_CANDIDATE" rev-parse HEAD)" = "$FOUNDATION_BASE_SHA"
EXPECTED_PATHS=$'.github/workflows/ci.yml\nscripts/check_feature_manifest.py\ntests/contract/test_feature_manifest.py\ntests/packaging/test_python_policy.py'
test "$(git diff --cached --name-only)" = "$EXPECTED_PATHS"
for staged_path in .github/workflows/ci.yml scripts/check_feature_manifest.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py; do
  test "$(git rev-parse ":$staged_path")" = "$(git -C "$FOUNDATION_CANDIDATE" hash-object "$staged_path")"
done
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_CI_LOCK_SHA=$(hash_file "$FOUNDATION_CANDIDATE/uv.lock")
FOUNDATION_CI_ENV_311=/private/tmp/cellpose-mcp-foundation-ci-py311-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
FOUNDATION_CI_ENV_312=/private/tmp/cellpose-mcp-foundation-ci-py312-${FOUNDATION_BASE_SHA}-${FOUNDATION_CI_LOCK_SHA}
"$FOUNDATION_CI_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_CI_ENV_311" "$PY311"
"$FOUNDATION_CI_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve()' "$FOUNDATION_CI_ENV_312" "$PY312"
git commit -m "ci: enforce truthful repository foundation"
test "$(git rev-parse HEAD^)" = "$FOUNDATION_BASE_SHA"
test "$(git log -1 --format=%s)" = "ci: enforce truthful repository foundation"
test "$(git diff-tree --no-commit-id --name-only -r HEAD)" = "$EXPECTED_PATHS"
for committed_path in .github/workflows/ci.yml scripts/check_feature_manifest.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py; do
  test "$(git rev-parse "HEAD:$committed_path")" = "$(git -C "$FOUNDATION_CANDIDATE" hash-object "$committed_path")"
done
"$PY312" -I -c 'from pathlib import Path; import hashlib; p=Path(".github/workflows/ci.yml").read_bytes(); marker=b"      - name: Pytest\n"; tail=p[p.index(marker):]; assert hashlib.sha256(tail).hexdigest()=="869a85e6af80aefddde2614d0953d96ed1fcbc688f3fb6aaea16ff0ace6ab790"'
"$PY312" -I -c 'from pathlib import Path; import hashlib; assert hashlib.sha256(Path("tests/test_installation.py").read_bytes()).hexdigest()=="3e4ef691dcb3b7f7f59c8cc5743626a5279d33b3fb848e09f3ff56206c52996d"'
"$PY312" -I -c 'from pathlib import Path; import subprocess; p=Path(".github/workflows/ci.yml").read_bytes(); marker=b"      - name: Pytest\n"; tail=p[p.index(marker):]; committed=subprocess.check_output(["git","show","HEAD:.github/workflows/ci.yml"]); assert p==committed+tail'
git diff --quiet -- tests/packaging/test_python_policy.py
git diff --cached --quiet
test "$(hash_file "$FOUNDATION_ROOT/pyproject.toml")" = f2fec832c75baa77adacf62212e1d5b3f95893e7ff20961c82a71fc3b3a1ec17
FOUNDATION_INVENTORY="$FOUNDATION_ROOT/local_archive/worktree-inventory-20260716T132515.517507Z.json"
test -f "$FOUNDATION_INVENTORY"
test ! -L "$FOUNDATION_INVENTORY"
test "$(hash_file "$FOUNDATION_INVENTORY")" = 76b3704bfeb4fd75f2283d548625d63acd664b259ee3e946da34918fdb12f1c1
"$PY312" -I - "$FOUNDATION_ROOT" "$FOUNDATION_INVENTORY" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
inventory = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
authorized = {
    ".github/workflows/ci.yml",
    ".gitignore",
    ".python-version",
    "MANIFEST.in",
    "docs/superpowers/plans/2026-07-16-cellpose-local-first-roadmap.md",
    "docs/superpowers/plans/2026-07-16-cellpose-repository-foundation.md",
    "pyproject.toml",
    "scripts/inventory_worktree.py",
    "tests/dev/test_inventory_worktree.py",
}
entries = {entry["path"]: entry for entry in inventory["entries"]}
assert authorized <= entries.keys()
untouched = [entry for path, entry in entries.items() if path not in authorized]
assert len(untouched) == 102
for entry in untouched:
    path = root / entry["path"]
    if entry["kind"] == "file":
        assert path.is_file() and not path.is_symlink(), entry["path"]
        content = path.read_bytes()
    else:
        assert entry["kind"] == "symlink" and path.is_symlink(), entry["path"]
        content = os.readlink(path).encode()
    assert len(content) == entry["worktree_size"], entry["path"]
    assert hashlib.sha256(content).hexdigest() == entry["worktree_sha256"], entry["path"]
PY
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: the index is empty. The only `.github/workflows/ci.yml` working-tree
diff is the preserved legacy Pytest/install-E2E suffix; the untracked install
test and all unrelated user work remain present and unstaged.

### Task 7: Prove Phase 0 from a clean committed clone

**Files:** No repository files.

**Interfaces:** This is a validation-only gate. It proves the commit users and
GitHub receive, independently of preserved dirty-root experiments.

**Completed acceptance binding:** Phase 0 is permanently bound to commit
`c926877105873cd9e6c091bb849333800c5cc1ac`, parent
`d0039330718f4967eb4a023ebb8c463337de72f8`, and grandparent
`847e9f2dfd85568d29095e900861b828e01f3fc9`. Their subjects, newest first,
are `ci: enforce truthful repository foundation`,
`test: make distribution proof offline`, and
`fix: clarify inventory archive failures`. This historical proof is checked
with `git show` on those objects, never with the moving current `git log -3`.
The acceptance clone is
`/private/tmp/cellpose-mcp-foundation-acceptance-c92687710587`; its lock is
`aea5be18a2e96f348f618e835c3bdff2f54d0cbabb479ee84a5bc536144a74ec`.
Its interpreters are
`/private/tmp/cellpose-mcp-foundation-acceptance-py311-c926877105873cd9e6c091bb849333800c5cc1ac-aea5be18a2e96f348f618e835c3bdff2f54d0cbabb479ee84a5bc536144a74ec/bin/python`
and
`/private/tmp/cellpose-mcp-foundation-acceptance-py312-c926877105873cd9e6c091bb849333800c5cc1ac-aea5be18a2e96f348f618e835c3bdff2f54d0cbabb479ee84a5bc536144a74ec/bin/python`.
The acceptance temp root is
`/private/tmp/cellpose-mcp-foundation-acceptance-tmp-c926877105873cd9e6c091bb849333800c5cc1ac-aea5be18a2e96f348f618e835c3bdff2f54d0cbabb479ee84a5bc536144a74ec`;
the focused Python 3.11, focused Python 3.12, and distribution JUnit hashes are
respectively `c7fe743c44ad572132f8acee0faf0a887634586754bb7adeddbe1c6fd7ff06e7`,
`6a423a41df3af6598d59ffd3a4fc6fe0c48a26e076a783ffe0aa42e89b52411c`,
and `d3a56d27b00966319cb0fce66e33d7b889b5ce9a3eb20d784f4e2a2051d55a86`.

- [ ] **Step 1: Create a clean local acceptance clone**

Re-enter the same explicitly approved package boundary used in Task 6:
`https://pypi.org/simple` plus artifact URLs beneath
`https://files.pythonhosted.org/`. The acceptance cache, environments, home,
and temporary directory are keyed by the exact completed SHA and lock SHA.
Create an absent path; otherwise validate its type, ownership, mode, commit,
lock, and interpreter binding before reuse. Never delete or overwrite Phase 0
evidence.

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
EXPECTED_COMMITS=$'ci: enforce truthful repository foundation\ntest: make distribution proof offline\nfix: clarify inventory archive failures'
FOUNDATION_ACCEPTANCE_SHA=c926877105873cd9e6c091bb849333800c5cc1ac
FOUNDATION_ACCEPTANCE_PARENT=d0039330718f4967eb4a023ebb8c463337de72f8
FOUNDATION_ACCEPTANCE_GRANDPARENT=847e9f2dfd85568d29095e900861b828e01f3fc9
test "$(git rev-parse "${FOUNDATION_ACCEPTANCE_SHA}^")" = "$FOUNDATION_ACCEPTANCE_PARENT"
test "$(git rev-parse "${FOUNDATION_ACCEPTANCE_PARENT}^")" = "$FOUNDATION_ACCEPTANCE_GRANDPARENT"
test "$(git show -s --format=%s "$FOUNDATION_ACCEPTANCE_SHA")" = "ci: enforce truthful repository foundation"
test "$(git show -s --format=%s "$FOUNDATION_ACCEPTANCE_PARENT")" = "test: make distribution proof offline"
test "$(git show -s --format=%s "$FOUNDATION_ACCEPTANCE_GRANDPARENT")" = "fix: clarify inventory archive failures"
FOUNDATION_RUN_SHA=${FOUNDATION_ACCEPTANCE_SHA:0:12}
FOUNDATION_ACCEPTANCE=/private/tmp/cellpose-mcp-foundation-acceptance-${FOUNDATION_RUN_SHA}
test "$FOUNDATION_ACCEPTANCE" = /private/tmp/cellpose-mcp-foundation-acceptance-c92687710587
export FOUNDATION_ACCEPTANCE
if test -e "$FOUNDATION_ACCEPTANCE"; then
  test -d "$FOUNDATION_ACCEPTANCE"
  test ! -L "$FOUNDATION_ACCEPTANCE"
else
  git clone --no-hardlinks --local --no-checkout . "$FOUNDATION_ACCEPTANCE"
  git -C "$FOUNDATION_ACCEPTANCE" checkout --detach "$FOUNDATION_ACCEPTANCE_SHA"
fi
test "$(git -C "$FOUNDATION_ACCEPTANCE" rev-parse HEAD)" = "$FOUNDATION_ACCEPTANCE_SHA"
test -z "$(git -C "$FOUNDATION_ACCEPTANCE" status --porcelain)"
test ! -e "$FOUNDATION_ACCEPTANCE/src/cellpose_mcp/operations.py"
test ! -e "$FOUNDATION_ACCEPTANCE/src/cellpose_mcp/cli/app.py"
test ! -e "$FOUNDATION_ACCEPTANCE/tests/test_installation.py"

UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
validate_network_sources() {
  "$PY312" -I - "$1" "$2" <<'PY'
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

index = "https://pypi.org/simple"
project_path, lock_path = map(Path, sys.argv[1:])
project = tomllib.loads(project_path.read_text(encoding="utf-8"))
requirements = list(project["project"].get("dependencies", []))
for group in project["project"].get("optional-dependencies", {}).values():
    requirements.extend(group)
requirements.extend(project["build-system"].get("requires", []))
assert requirements and all(isinstance(item, str) for item in requirements)
assert all("@" not in item and "://" not in item for item in requirements)
assert "dependency-groups" not in project
uv_config = project.get("tool", {}).get("uv", {})
assert isinstance(uv_config, dict)
assert uv_config == {}
lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
for package in lock["package"]:
    assert package["source"] in ({"registry": index}, {"editable": "."})
    artifacts = ([package["sdist"]] if "sdist" in package else []) + package.get("wheels", [])
    for artifact in artifacts:
        parsed = urlsplit(artifact["url"])
        assert parsed.scheme == "https" and parsed.hostname == "files.pythonhosted.org", artifact
        assert parsed.username is None and parsed.password is None and parsed.port is None, artifact
        assert parsed.query == "" and parsed.fragment == "" and parsed.path.startswith("/packages/"), artifact
PY
}
FOUNDATION_ACCEPTANCE_LOCK_SHA=$(hash_file "$FOUNDATION_ACCEPTANCE/uv.lock")
test "$FOUNDATION_ACCEPTANCE_LOCK_SHA" = aea5be18a2e96f348f618e835c3bdff2f54d0cbabb479ee84a5bc536144a74ec
FOUNDATION_ACCEPTANCE_CACHE=/private/tmp/cellpose-mcp-foundation-acceptance-cache-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_ENV_311=/private/tmp/cellpose-mcp-foundation-acceptance-py311-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_ENV_312=/private/tmp/cellpose-mcp-foundation-acceptance-py312-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_HOME=/private/tmp/cellpose-mcp-foundation-acceptance-home-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_TMP=/private/tmp/cellpose-mcp-foundation-acceptance-tmp-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
assert_private_directory() {
  local directory=$1
  test -d "$directory" && test ! -L "$directory" && test -O "$directory"
  test "$(/usr/bin/stat -f '%Lp' "$directory")" = 700
}
for private_directory in "$FOUNDATION_ACCEPTANCE_CACHE" "$FOUNDATION_ACCEPTANCE_HOME" "$FOUNDATION_ACCEPTANCE_TMP"; do
  if test -e "$private_directory"; then assert_private_directory "$private_directory"; else install -d -m 700 "$private_directory"; fi
done
validate_network_sources "$FOUNDATION_ACCEPTANCE/pyproject.toml" "$FOUNDATION_ACCEPTANCE/uv.lock"
if ! test -e "$FOUNDATION_ACCEPTANCE_ENV_311"; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ACCEPTANCE_HOME" TMPDIR="$FOUNDATION_ACCEPTANCE_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_ACCEPTANCE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ACCEPTANCE_ENV_311" UV_DEFAULT_INDEX=https://pypi.org/simple UV_KEYRING_PROVIDER=disabled UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ACCEPTANCE" --project "$FOUNDATION_ACCEPTANCE" --no-config sync --frozen --no-install-project --no-build --python "$PY311" --extra test --extra dev --default-index https://pypi.org/simple --keyring-provider disabled --no-python-downloads
fi
if ! test -e "$FOUNDATION_ACCEPTANCE_ENV_312"; then
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ACCEPTANCE_HOME" TMPDIR="$FOUNDATION_ACCEPTANCE_TMP" PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR="$FOUNDATION_ACCEPTANCE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ACCEPTANCE_ENV_312" UV_DEFAULT_INDEX=https://pypi.org/simple UV_KEYRING_PROVIDER=disabled UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ACCEPTANCE" --project "$FOUNDATION_ACCEPTANCE" --no-config sync --frozen --no-install-project --no-build --python "$PY312" --extra test --extra dev --default-index https://pypi.org/simple --keyring-provider disabled --no-python-downloads
fi
validate_network_sources "$FOUNDATION_ACCEPTANCE/pyproject.toml" "$FOUNDATION_ACCEPTANCE/uv.lock"
test "$(hash_file "$FOUNDATION_ACCEPTANCE/uv.lock")" = "$FOUNDATION_ACCEPTANCE_LOCK_SHA"
"$FOUNDATION_ACCEPTANCE_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_ACCEPTANCE_ENV_311" "$PY311"
"$FOUNDATION_ACCEPTANCE_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_ACCEPTANCE_ENV_312" "$PY312"
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
for relative in .pytest_cache .ruff_cache .mypy_cache build dist src/cellpose_mcp.egg-info; do
  test ! -e "$FOUNDATION_ACCEPTANCE/$relative"
done
test -z "$(git -C "$FOUNDATION_ACCEPTANCE" status --porcelain)"
```

Expected: the root/branch/ancestor and exact three-commit chain pass; the clone
is clean; the named untracked legacy experiments are absent; all fresh-path
gates pass; and the three executable hashes are identical before and after
sanitized provisioning.

- [ ] **Step 2: Repeat the complete focused gate on both Python versions**

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_ACCEPTANCE_SHA=c926877105873cd9e6c091bb849333800c5cc1ac
FOUNDATION_RUN_SHA=${FOUNDATION_ACCEPTANCE_SHA:0:12}
FOUNDATION_ACCEPTANCE=/private/tmp/cellpose-mcp-foundation-acceptance-${FOUNDATION_RUN_SHA}
export FOUNDATION_ACCEPTANCE
test "$(git -C "$FOUNDATION_ACCEPTANCE" rev-parse HEAD)" = "$FOUNDATION_ACCEPTANCE_SHA"
test -z "$(git -C "$FOUNDATION_ACCEPTANCE" status --porcelain)"
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_ACCEPTANCE_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_ACCEPTANCE/uv.lock" | /usr/bin/awk '{print $1}')
FOUNDATION_ACCEPTANCE_CACHE=/private/tmp/cellpose-mcp-foundation-acceptance-cache-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_ENV_311=/private/tmp/cellpose-mcp-foundation-acceptance-py311-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_ENV_312=/private/tmp/cellpose-mcp-foundation-acceptance-py312-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_HOME=/private/tmp/cellpose-mcp-foundation-acceptance-home-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_TMP=/private/tmp/cellpose-mcp-foundation-acceptance-tmp-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
test -d "$FOUNDATION_ACCEPTANCE_CACHE"
test -x "$FOUNDATION_ACCEPTANCE_ENV_311/bin/python"
test -x "$FOUNDATION_ACCEPTANCE_ENV_312/bin/python"
"$FOUNDATION_ACCEPTANCE_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_ACCEPTANCE_ENV_311" "$PY311"
"$FOUNDATION_ACCEPTANCE_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_ACCEPTANCE_ENV_312" "$PY312"
acceptance_run_311() {
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ACCEPTANCE_HOME" TMPDIR="$FOUNDATION_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_ACCEPTANCE/src" UV_CACHE_DIR="$FOUNDATION_ACCEPTANCE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ACCEPTANCE_ENV_311" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ACCEPTANCE" --project "$FOUNDATION_ACCEPTANCE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY311" --extra test --extra dev "$@"
}
acceptance_run_312() {
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ACCEPTANCE_HOME" TMPDIR="$FOUNDATION_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_ACCEPTANCE/src" UV_CACHE_DIR="$FOUNDATION_ACCEPTANCE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ACCEPTANCE_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ACCEPTANCE" --project "$FOUNDATION_ACCEPTANCE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev "$@"
}

JUNIT_311="$FOUNDATION_ACCEPTANCE_TMP/foundation-60-py311.xml"
JUNIT_312="$FOUNDATION_ACCEPTANCE_TMP/foundation-60-py312.xml"
EXPECTED_JUNIT_311_SHA=c7fe743c44ad572132f8acee0faf0a887634586754bb7adeddbe1c6fd7ff06e7
EXPECTED_JUNIT_312_SHA=6a423a41df3af6598d59ffd3a4fc6fe0c48a26e076a783ffe0aa42e89b52411c
acceptance_run_311 "$FOUNDATION_ACCEPTANCE_ENV_311/bin/python" -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_ACCEPTANCE_ENV_311" "$PY311"
if test -e "$JUNIT_311"; then
  test -f "$JUNIT_311" && test ! -L "$JUNIT_311"
  test "$(hash_file "$JUNIT_311")" = "$EXPECTED_JUNIT_311_SHA"
else
  set +e
  acceptance_run_311 pytest -p no:cacheprovider tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q --junitxml="$JUNIT_311"
  JUNIT_STATUS=$?
  set -e
  if test "$JUNIT_STATUS" -ne 0; then
    test -f "$JUNIT_311"; FAILED_JUNIT_SHA=$(hash_file "$JUNIT_311")
    JUNIT_RETRY_311="${JUNIT_311%.xml}.retry-${FAILED_JUNIT_SHA:0:12}.xml"
    test ! -e "$JUNIT_RETRY_311"
    echo "retained failed JUnit $FAILED_JUNIT_SHA; retry only at $JUNIT_RETRY_311" >&2
    exit "$JUNIT_STATUS"
  fi
fi
acceptance_run_311 "$FOUNDATION_ACCEPTANCE_ENV_311/bin/python" -c 'import sys,xml.etree.ElementTree as ET; r=ET.parse(sys.argv[1]).getroot(); s=[r] if r.tag=="testsuite" else list(r.findall("testsuite")); actual={k:sum(int(x.get(k,"0")) for x in s) for k in ("tests","failures","errors","skipped")}; assert actual=={"tests":60,"failures":0,"errors":0,"skipped":0},actual' "$JUNIT_311"
acceptance_run_312 "$FOUNDATION_ACCEPTANCE_ENV_312/bin/python" -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_ACCEPTANCE_ENV_312" "$PY312"
if test -e "$JUNIT_312"; then
  test -f "$JUNIT_312" && test ! -L "$JUNIT_312"
  test "$(hash_file "$JUNIT_312")" = "$EXPECTED_JUNIT_312_SHA"
else
  set +e
  acceptance_run_312 pytest -p no:cacheprovider tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging/test_python_policy.py tests/packaging/test_distribution_contents.py -q --junitxml="$JUNIT_312"
  JUNIT_STATUS=$?
  set -e
  if test "$JUNIT_STATUS" -ne 0; then
    test -f "$JUNIT_312"; FAILED_JUNIT_SHA=$(hash_file "$JUNIT_312")
    JUNIT_RETRY_312="${JUNIT_312%.xml}.retry-${FAILED_JUNIT_SHA:0:12}.xml"
    test ! -e "$JUNIT_RETRY_312"
    echo "retained failed JUnit $FAILED_JUNIT_SHA; retry only at $JUNIT_RETRY_312" >&2
    exit "$JUNIT_STATUS"
  fi
fi
acceptance_run_312 "$FOUNDATION_ACCEPTANCE_ENV_312/bin/python" -c 'import sys,xml.etree.ElementTree as ET; r=ET.parse(sys.argv[1]).getroot(); s=[r] if r.tag=="testsuite" else list(r.findall("testsuite")); actual={k:sum(int(x.get(k,"0")) for x in s) for k in ("tests","failures","errors","skipped")}; assert actual=={"tests":60,"failures":0,"errors":0,"skipped":0},actual' "$JUNIT_312"
acceptance_run_311 ruff check --no-fix --no-cache src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging
acceptance_run_311 mypy --cache-dir "$FOUNDATION_ACCEPTANCE_TMP/mypy-py311" --python-version 3.11 src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py
acceptance_run_312 ruff check --no-fix --no-cache src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py tests/dev/test_inventory_worktree.py tests/contract/test_feature_manifest.py tests/packaging
acceptance_run_312 mypy --cache-dir "$FOUNDATION_ACCEPTANCE_TMP/mypy-py312" --python-version 3.12 src/cellpose_mcp/release scripts/check_feature_manifest.py scripts/inventory_worktree.py
acceptance_run_312 python -c 'import subprocess,sys; result=subprocess.run([sys.executable,"scripts/check_feature_manifest.py"],check=False,capture_output=True,text=True); assert result.returncode==0; assert result.stdout=="bootstrap manifest valid; release blockers: 14\n"; assert result.stderr==""'
acceptance_run_312 python -c 'import subprocess,sys; tools=["get_capabilities","inspect_image","list_models","prepare_model","segment","refine_segmentation","measure_masks","evaluate_segmentation","export_segmentation","train_model","restore_image","get_job","cancel_job"]; result=subprocess.run([sys.executable,"scripts/check_feature_manifest.py","--release"],check=False,capture_output=True,text=True); lines=result.stdout.splitlines(); assert result.returncode==1; assert result.stderr==""; assert len(lines)==14; assert lines[0].startswith("unresolved_core_matrix: core_capability_matrix_unresolved:"); assert [line.split(": ",2)[1] for line in lines[1:]]==tools'
test "$(/usr/bin/shasum -a 256 "$FOUNDATION_ACCEPTANCE/uv.lock" | /usr/bin/awk '{print $1}')" = "$FOUNDATION_ACCEPTANCE_LOCK_SHA"
for relative in .pytest_cache .ruff_cache .mypy_cache build dist src/cellpose_mcp.egg-info; do
  test ! -e "$FOUNDATION_ACCEPTANCE/$relative"
done
test -z "$(find "$FOUNDATION_ACCEPTANCE" -type d -name __pycache__ -print -quit)"
test -z "$(git -C "$FOUNDATION_ACCEPTANCE" status --porcelain)"
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: both JUnit files mechanically contain exactly 60 tests with zero
failures, errors, or skips; Ruff, mypy, and development mode pass; release
mode has the exact ordered 14-blocker failure; the lock hash and clone status
remain unchanged.

- [ ] **Step 3: Prove the distribution boundary again**

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
FOUNDATION_ACCEPTANCE_SHA=c926877105873cd9e6c091bb849333800c5cc1ac
FOUNDATION_RUN_SHA=${FOUNDATION_ACCEPTANCE_SHA:0:12}
FOUNDATION_ACCEPTANCE=/private/tmp/cellpose-mcp-foundation-acceptance-${FOUNDATION_RUN_SHA}
export FOUNDATION_ACCEPTANCE
test "$(git -C "$FOUNDATION_ACCEPTANCE" rev-parse HEAD)" = "$FOUNDATION_ACCEPTANCE_SHA"
test -z "$(git -C "$FOUNDATION_ACCEPTANCE" status --porcelain)"
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
FOUNDATION_ACCEPTANCE_LOCK_SHA=$(/usr/bin/shasum -a 256 "$FOUNDATION_ACCEPTANCE/uv.lock" | /usr/bin/awk '{print $1}')
FOUNDATION_ACCEPTANCE_CACHE=/private/tmp/cellpose-mcp-foundation-acceptance-cache-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_ENV_311=/private/tmp/cellpose-mcp-foundation-acceptance-py311-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_ENV_312=/private/tmp/cellpose-mcp-foundation-acceptance-py312-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_HOME=/private/tmp/cellpose-mcp-foundation-acceptance-home-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
FOUNDATION_ACCEPTANCE_TMP=/private/tmp/cellpose-mcp-foundation-acceptance-tmp-${FOUNDATION_ACCEPTANCE_SHA}-${FOUNDATION_ACCEPTANCE_LOCK_SHA}
test -d "$FOUNDATION_ACCEPTANCE_CACHE"
test -x "$FOUNDATION_ACCEPTANCE_ENV_311/bin/python"
test -x "$FOUNDATION_ACCEPTANCE_ENV_312/bin/python"
"$FOUNDATION_ACCEPTANCE_ENV_311/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,11)' "$FOUNDATION_ACCEPTANCE_ENV_311" "$PY311"
"$FOUNDATION_ACCEPTANCE_ENV_312/bin/python" -I -c 'from pathlib import Path; import sys; e=Path(sys.argv[1]); b=Path(sys.argv[2]); assert Path(sys.executable)==e/"bin/python"; assert Path(sys.prefix)==e; assert Path(sys.executable).resolve()==b.resolve(); assert Path(sys._base_executable).resolve()==b.resolve(); assert sys.version_info[:2]==(3,12)' "$FOUNDATION_ACCEPTANCE_ENV_312" "$PY312"
JUNIT_DISTRIBUTION="$FOUNDATION_ACCEPTANCE_TMP/foundation-distribution-19.xml"
EXPECTED_JUNIT_DISTRIBUTION_SHA=d3a56d27b00966319cb0fce66e33d7b889b5ce9a3eb20d784f4e2a2051d55a86
if test -e "$JUNIT_DISTRIBUTION"; then
  test -f "$JUNIT_DISTRIBUTION" && test ! -L "$JUNIT_DISTRIBUTION"
  test "$(hash_file "$JUNIT_DISTRIBUTION")" = "$EXPECTED_JUNIT_DISTRIBUTION_SHA"
else
  set +e
  /usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ACCEPTANCE_HOME" TMPDIR="$FOUNDATION_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_ACCEPTANCE/src" UV_CACHE_DIR="$FOUNDATION_ACCEPTANCE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ACCEPTANCE_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ACCEPTANCE" --project "$FOUNDATION_ACCEPTANCE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev pytest -p no:cacheprovider tests/packaging/test_distribution_contents.py -q --junitxml="$JUNIT_DISTRIBUTION"
  JUNIT_STATUS=$?
  set -e
  if test "$JUNIT_STATUS" -ne 0; then
    test -f "$JUNIT_DISTRIBUTION"; FAILED_JUNIT_SHA=$(hash_file "$JUNIT_DISTRIBUTION")
    JUNIT_RETRY_DISTRIBUTION="${JUNIT_DISTRIBUTION%.xml}.retry-${FAILED_JUNIT_SHA:0:12}.xml"
    test ! -e "$JUNIT_RETRY_DISTRIBUTION"
    echo "retained failed JUnit $FAILED_JUNIT_SHA; retry only at $JUNIT_RETRY_DISTRIBUTION" >&2
    exit "$JUNIT_STATUS"
  fi
fi
/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C HOME="$FOUNDATION_ACCEPTANCE_HOME" TMPDIR="$FOUNDATION_ACCEPTANCE_TMP" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$FOUNDATION_ACCEPTANCE/src" UV_CACHE_DIR="$FOUNDATION_ACCEPTANCE_CACHE" UV_PROJECT_ENVIRONMENT="$FOUNDATION_ACCEPTANCE_ENV_312" UV_NO_CONFIG=1 UV_NO_ENV_FILE=1 UV_PYTHON_DOWNLOADS=never "$UV" --directory "$FOUNDATION_ACCEPTANCE" --project "$FOUNDATION_ACCEPTANCE" --no-config run --frozen --offline --no-sync --no-python-downloads --python "$PY312" --extra test --extra dev python -c 'import sys,xml.etree.ElementTree as ET; r=ET.parse(sys.argv[1]).getroot(); s=[r] if r.tag=="testsuite" else list(r.findall("testsuite")); actual={k:sum(int(x.get(k,"0")) for x in s) for k in ("tests","failures","errors","skipped")}; assert actual=={"tests":19,"failures":0,"errors":0,"skipped":0},actual' "$JUNIT_DISTRIBUTION"
test "$(hash_file "$FOUNDATION_ACCEPTANCE/uv.lock")" = "$FOUNDATION_ACCEPTANCE_LOCK_SHA"
for relative in .pytest_cache .ruff_cache .mypy_cache build dist src/cellpose_mcp.egg-info; do
  test ! -e "$FOUNDATION_ACCEPTANCE/$relative"
done
test -z "$(find "$FOUNDATION_ACCEPTANCE" -type d -name __pycache__ -print -quit)"
test -z "$(git -C "$FOUNDATION_ACCEPTANCE" status --porcelain)"
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
```

Expected: the JUnit total is mechanically exactly 19 with zero failures,
errors, or skips, and the clone remains clean after verification.

- [ ] **Step 4: Reconfirm the dirty root is preserved and stop**

```bash
set -euo pipefail
FOUNDATION_ROOT=$(git rev-parse --show-toplevel)
test "$FOUNDATION_ROOT" = "$(pwd -P)"
test "$FOUNDATION_ROOT" = /Users/suraj/Documents/Tools/cellpose_mcp
test "$(git branch --show-current)" = codex/cellpose-local-first
git cat-file -e '45021a2^{commit}'
git merge-base --is-ancestor 45021a2 HEAD
git diff --cached --quiet
EXPECTED_COMMITS=$'ci: enforce truthful repository foundation\ntest: make distribution proof offline\nfix: clarify inventory archive failures'
FOUNDATION_ACCEPTANCE_SHA=c926877105873cd9e6c091bb849333800c5cc1ac
FOUNDATION_ACCEPTANCE_PARENT=d0039330718f4967eb4a023ebb8c463337de72f8
FOUNDATION_ACCEPTANCE_GRANDPARENT=847e9f2dfd85568d29095e900861b828e01f3fc9
ACTUAL_COMMITS="$(for commit_sha in "$FOUNDATION_ACCEPTANCE_SHA" "$FOUNDATION_ACCEPTANCE_PARENT" "$FOUNDATION_ACCEPTANCE_GRANDPARENT"; do git show -s --format=%s "$commit_sha"; done)"
test "$ACTUAL_COMMITS" = "$EXPECTED_COMMITS"
UV=/Users/suraj/.local/bin/uv
PY311=/Users/suraj/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3.11
PY312=/Users/suraj/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12
hash_file() {
  /usr/bin/shasum -a 256 "$1" | /usr/bin/awk '{print $1}'
}
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
test "$(hash_file "$FOUNDATION_ROOT/pyproject.toml")" = f2fec832c75baa77adacf62212e1d5b3f95893e7ff20961c82a71fc3b3a1ec17
"$PY312" -I -c 'from pathlib import Path; import hashlib; p=Path(".github/workflows/ci.yml").read_bytes(); marker=b"      - name: Pytest\n"; tail=p[p.index(marker):]; assert hashlib.sha256(tail).hexdigest()=="869a85e6af80aefddde2614d0953d96ed1fcbc688f3fb6aaea16ff0ace6ab790"'
"$PY312" -I -c 'from pathlib import Path; import hashlib; assert hashlib.sha256(Path("tests/test_installation.py").read_bytes()).hexdigest()=="3e4ef691dcb3b7f7f59c8cc5743626a5279d33b3fb848e09f3ff56206c52996d"'
"$PY312" -I -c 'from pathlib import Path; import subprocess; p=Path(".github/workflows/ci.yml").read_bytes(); marker=b"      - name: Pytest\n"; tail=p[p.index(marker):]; committed=subprocess.check_output(["git","show","c926877105873cd9e6c091bb849333800c5cc1ac:.github/workflows/ci.yml"]); assert p==committed+tail'
git diff --quiet -- tests/packaging/test_python_policy.py
FOUNDATION_INVENTORY="$FOUNDATION_ROOT/local_archive/worktree-inventory-20260716T132515.517507Z.json"
test -f "$FOUNDATION_INVENTORY"
test ! -L "$FOUNDATION_INVENTORY"
test "$(hash_file "$FOUNDATION_INVENTORY")" = 76b3704bfeb4fd75f2283d548625d63acd664b259ee3e946da34918fdb12f1c1
"$PY312" -I - "$FOUNDATION_ROOT" "$FOUNDATION_INVENTORY" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
inventory = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
authorized = {
    ".github/workflows/ci.yml",
    ".gitignore",
    ".python-version",
    "MANIFEST.in",
    "docs/superpowers/plans/2026-07-16-cellpose-local-first-roadmap.md",
    "docs/superpowers/plans/2026-07-16-cellpose-repository-foundation.md",
    "pyproject.toml",
    "scripts/inventory_worktree.py",
    "tests/dev/test_inventory_worktree.py",
}
entries = {entry["path"]: entry for entry in inventory["entries"]}
assert authorized <= entries.keys()
untouched = [entry for path, entry in entries.items() if path not in authorized]
assert len(untouched) == 102
for entry in untouched:
    path = root / entry["path"]
    if entry["kind"] == "file":
        assert path.is_file() and not path.is_symlink(), entry["path"]
        content = path.read_bytes()
    else:
        assert entry["kind"] == "symlink" and path.is_symlink(), entry["path"]
        content = os.readlink(path).encode()
    assert len(content) == entry["worktree_size"], entry["path"]
    assert hashlib.sha256(content).hexdigest() == entry["worktree_sha256"], entry["path"]
PY
test "$(hash_file "$UV")" = 392016c5bca9eb01bef3ae3957a8ed93d3bd9fe837825b5c4cc313e50c15a4d5
test "$(hash_file "$PY311")" = e6eedfbc57422e986a0e3b24b18ee45764b809ff1385d3af42e9c22b5bd00de5
test "$(hash_file "$PY312")" = 6a37ff35c2edec046bd7e5504f4603b93fdbd33166252a324d15b6e41cdd5483
git diff --cached --quiet
```

Expected: no index entries, the ignored inventory remains present, the user
files recorded by the inventory remain untouched, and the three final Phase 0
commits are `fix: clarify inventory archive failures`,
`test: make distribution proof offline`, and
`ci: enforce truthful repository foundation`.

Do not run the broad legacy suite, switch the MCP entrypoint, construct a
Cellpose model, delete or archive stale code, tag a version, publish GitHub
artifacts, or upload to PyPI in Phase 0.

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
