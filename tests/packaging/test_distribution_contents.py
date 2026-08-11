"""Distribution checks for the active Cellpose CLI and MCP runtime."""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

import pytest

ROOT = Path(__file__).parents[2]


def _project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return str(tomllib.load(stream)["project"]["version"])


def _offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.upper().endswith("_PROXY") or name.startswith("PIP_"):
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


def _build_distributions(tmp_path: Path) -> tuple[Path, Path]:
    output = tmp_path / "dist"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(output),
            str(ROOT),
        ],
        check=True,
        env=_offline_environment(),
    )
    wheel = next(output.glob("*.whl"))
    sdist = next(output.glob("*.tar.gz"))
    return wheel, sdist


def _wheel_paths(wheel: Path) -> set[str]:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert len(names) == len(set(names))
    return set(names)


def _sdist_paths(sdist: Path) -> set[str]:
    with tarfile.open(sdist, mode="r:gz") as archive:
        members = archive.getmembers()
    roots = {PurePosixPath(member.name).parts[0] for member in members}
    assert len(roots) == 1
    root = roots.pop()
    assert root == f"cellpose_mcp-{_project_version()}"
    paths: set[str] = set()
    for member in members:
        path = PurePosixPath(member.name)
        assert not path.is_absolute()
        assert ".." not in path.parts
        if member.isfile():
            paths.add(PurePosixPath(*path.parts[1:]).as_posix())
    return paths


def _assert_runtime_only(paths: set[str]) -> None:
    forbidden = (
        ".mcp.json",
        ".agents/",
        ".codex/",
        "features.toml",
        "feature_manifest.py",
        "__pycache__",
        ".pyc",
        ".DS_Store",
        "credentials",
        "train_data/",
        "results/",
    )
    assert not any(token in path for path in paths for token in forbidden)


@pytest.mark.integration
def test_build_install_and_distribution_contents(tmp_path: Path) -> None:
    """Build offline, inspect payloads, and verify installed entry points."""
    wheel, sdist = _build_distributions(tmp_path)
    version = _project_version()
    assert wheel.name == f"cellpose_mcp-{version}-py3-none-any.whl"
    assert sdist.name == f"cellpose_mcp-{version}.tar.gz"

    wheel_paths = _wheel_paths(wheel)
    required_wheel = {
        "cellpose_mcp/__init__.py",
        "cellpose_mcp/__main__.py",
        "cellpose_mcp/mcp_instance.py",
        "cellpose_mcp/operations.py",
        "cellpose_mcp/server.py",
        "cellpose_mcp/tools.py",
        "cellpose_mcp/cli/app.py",
        "cellpose_mcp/cli/install.py",
        "cellpose_mcp/py.typed",
        f"cellpose_mcp-{version}.dist-info/METADATA",
        f"cellpose_mcp-{version}.dist-info/entry_points.txt",
    }
    assert required_wheel <= wheel_paths
    _assert_runtime_only(wheel_paths)

    sdist_paths = _sdist_paths(sdist)
    required_sdist = {
        "LICENSE",
        "MANIFEST.in",
        "README.md",
        "pyproject.toml",
        "src/cellpose_mcp/operations.py",
        "src/cellpose_mcp/tools.py",
        "src/cellpose_mcp/cli/app.py",
        "src/cellpose_mcp/cli/install.py",
    }
    assert required_sdist <= sdist_paths
    _assert_runtime_only(sdist_paths)

    installed = tmp_path / "installed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--target",
            str(installed),
            str(wheel),
        ],
        check=True,
        env=_offline_environment(),
    )
    code = """
import importlib.metadata
import sys

sys.path.insert(0, sys.argv[1])
import cellpose_mcp

distribution = next(
    item
    for item in importlib.metadata.distributions(path=[sys.argv[1]])
    if item.metadata["Name"] == "cellpose-mcp"
)
assert distribution.version == EXPECTED_VERSION
assert cellpose_mcp.__version__ == EXPECTED_VERSION
scripts = {entry.name for entry in distribution.entry_points if entry.group == "console_scripts"}
assert scripts == {"cellpose-mcp", "cellpose-mcp-cli", "cellpose-mcp-install"}
""".replace("EXPECTED_VERSION", repr(version))
    subprocess.run(
        [sys.executable, "-I", "-c", code, str(installed)],
        check=True,
        env=_offline_environment(),
    )
