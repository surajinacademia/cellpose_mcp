# ruff: noqa: S603

from __future__ import annotations

import hashlib
import importlib.util
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


def git(repo: Path, *args: str) -> bytes:
    completed = subprocess.run(
        [GIT, "--no-optional-locks", "-C", str(repo), *args],
        check=True,
        capture_output=True,
    )
    return completed.stdout


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
                        (1, 2, 7, 10, 12, stat.S_IFREG),
                        (1, 2, 7, 10, 12, stat.S_IFREG),
                        (1, 3, 8, 11, 13, stat.S_IFREG),
                    ],
                ),
                self.assertRaisesRegex(
                    RuntimeError,
                    "changed while it was being hashed",
                ),
            ):
                inventory.hash_regular_stable(path)

    def test_inventory_refuses_symlinked_worktree_ancestor(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo = base / "repo"
            repo.mkdir()
            git(repo, "init")
            git(repo, "config", "user.email", "inventory@example.invalid")
            git(repo, "config", "user.name", "Inventory Test")
            directory = repo / "dir"
            directory.mkdir()
            tracked = directory / "file"
            tracked.write_bytes(b"inside\n")
            git(repo, "add", "dir/file")
            git(repo, "commit", "-m", "nested fixture")

            external = base / "external"
            external.mkdir()
            (external / "file").write_bytes(b"outside\n")
            tracked.unlink()
            directory.rmdir()
            directory.symlink_to(external, target_is_directory=True)

            with self.assertRaisesRegex(
                RuntimeError,
                "symbolic link in worktree path",
            ):
                inventory.build_inventory(repo)

    def test_inventory_records_missing_file_below_deleted_directory(
        self,
    ) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            git(repo, "init")
            git(repo, "config", "user.email", "inventory@example.invalid")
            git(repo, "config", "user.name", "Inventory Test")
            directory = repo / "dir"
            directory.mkdir()
            tracked = directory / "file"
            content = b"nested\n"
            tracked.write_bytes(content)
            git(repo, "add", "dir/file")
            git(repo, "commit", "-m", "nested fixture")
            object_id = git(
                repo,
                "rev-parse",
                "HEAD:dir/file",
            ).decode().strip()
            shutil.rmtree(directory)

            try:
                document = inventory.build_inventory(repo)
            except RuntimeError as exc:
                self.fail(f"nested deletion aborted inventory: {exc}")
            entries = {
                entry["path"]: entry
                for entry in document["entries"]
            }
            missing = entries["dir/file"]
            self.assertEqual(missing["category"], "modified")
            self.assertEqual(missing["git_status"], " D")
            self.assertEqual(missing["kind"], "missing")
            self.assertIsNone(missing["worktree_size"])
            self.assertIsNone(missing["worktree_sha256"])
            self.assertEqual(missing["index_object_id"], object_id)
            self.assertEqual(missing["index_mode"], "100644")
            self.assertEqual(missing["index_type"], "blob")
            self.assertEqual(
                missing["index_sha256"],
                hashlib.sha256(content).hexdigest(),
            )

    def test_inspection_aborts_if_classified_file_is_replaced_before_open(
        self,
    ) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            victim = repo / "victim"
            original = repo / "original"
            victim.write_bytes(b"content")
            original_open = inventory.os.open
            replaced = False

            def replacing_open(target, flags, *args, **kwargs):
                nonlocal replaced
                if not replaced and target in (victim, victim.name):
                    victim.replace(original)
                    victim.write_bytes(b"changed")
                    replaced = True
                return original_open(target, flags, *args, **kwargs)

            with (
                mock.patch.object(
                    inventory.os,
                    "open",
                    side_effect=replacing_open,
                ),
                self.assertRaisesRegex(
                    RuntimeError,
                    "changed while it was being hashed",
                ),
            ):
                inventory.inspect_worktree(repo, victim.name)
            self.assertTrue(replaced)

    def test_file_identity_includes_ctime(self) -> None:
        inventory = load_inventory_module()
        info = mock.Mock(
            st_dev=1,
            st_ino=2,
            st_size=3,
            st_mtime_ns=4,
            st_ctime_ns=5,
            st_mode=stat.S_IFREG,
        )

        self.assertEqual(
            inventory.file_identity(info),
            (1, 2, 3, 4, 5, stat.S_IFREG),
        )

    def test_inventory_preserves_gitlink_mode_and_type(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            git(repo, "init")
            git(repo, "config", "user.email", "inventory@example.invalid")
            git(repo, "config", "user.name", "Inventory Test")
            (repo / "seed").write_bytes(b"seed\n")
            git(repo, "add", "seed")
            git(repo, "commit", "-m", "seed")
            target_commit = git(repo, "rev-parse", "HEAD").decode().strip()
            git(
                repo,
                "update-index",
                "--add",
                "--cacheinfo",
                "160000",
                target_commit,
                "module",
            )
            git(repo, "commit", "-m", "gitlink")

            try:
                document = inventory.build_inventory(repo)
            except subprocess.CalledProcessError as exc:
                self.fail(f"valid gitlink inventory aborted: {exc}")
            entries = {
                entry["path"]: entry
                for entry in document["entries"]
            }
            gitlink = entries["module"]
            self.assertEqual(gitlink["index_object_id"], target_commit)
            self.assertEqual(gitlink["index_mode"], "160000")
            self.assertEqual(gitlink["index_type"], "commit")
            self.assertIsNone(gitlink["index_sha256"])

    def test_inventory_aborts_if_worktree_status_changes(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            repo = create_dirty_repo(Path(temporary))
            before = inventory.changed_paths(repo)
            after = {**before, "clean.txt": " M"}

            with (
                mock.patch.object(
                    inventory,
                    "changed_paths",
                    side_effect=[before, after],
                ),
                self.assertRaisesRegex(
                    RuntimeError,
                    "worktree status changed during inventory",
                ),
            ):
                inventory.build_inventory(repo)

    def test_inventory_aborts_if_head_changes(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            repo = create_dirty_repo(Path(temporary))
            original_git_output = inventory.git_output
            heads = iter([b"1" * 40 + b"\n", b"2" * 40 + b"\n"])

            def changing_git_output(query_repo, *args):
                if args == ("rev-parse", "HEAD"):
                    return next(heads)
                return original_git_output(query_repo, *args)

            with (
                mock.patch.object(
                    inventory,
                    "git_output",
                    side_effect=changing_git_output,
                ),
                self.assertRaisesRegex(
                    RuntimeError,
                    "HEAD changed during inventory",
                ),
            ):
                inventory.build_inventory(repo)

    def test_index_identity_refuses_symlinks(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "real-index"
            target.write_bytes(b"index")
            link = base / "index"
            link.symlink_to(target.name)

            with self.assertRaisesRegex(
                RuntimeError,
                "Git index path is not a stable regular file",
            ):
                inventory.index_identity(link)

    def test_index_identity_aborts_if_path_is_replaced_during_read(self) -> None:
        inventory = load_inventory_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            path = base / "index"
            original = base / "original-index"
            path.write_bytes(b"original index")
            original_read = inventory.os.read
            replaced = False

            def replacing_read(descriptor, size):
                nonlocal replaced
                chunk = original_read(descriptor, size)
                if not replaced:
                    path.replace(original)
                    path.write_bytes(b"replacement")
                    replaced = True
                return chunk

            with (
                mock.patch.object(
                    inventory.os,
                    "read",
                    side_effect=replacing_read,
                ),
                self.assertRaisesRegex(
                    RuntimeError,
                    "Git index changed while it was being read",
                ),
            ):
                inventory.index_identity(path)
            self.assertTrue(replaced)


if __name__ == "__main__":
    unittest.main()
