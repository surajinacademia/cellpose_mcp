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
