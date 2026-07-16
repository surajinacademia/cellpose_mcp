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
