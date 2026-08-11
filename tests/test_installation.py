"""Build, isolated install, and end-to-end segmentation checks."""

from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_IMAGE = REPO_ROOT / "demo_images" / "img00.png"


def _run(
    cmd: list[str], *, cwd: Path | None = None, timeout: int | None = None
) -> None:
    subprocess.run(
        cmd, check=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


@pytest.mark.smoke
def test_distribution_metadata_and_console_scripts() -> None:
    """Installed distribution must expose version and declared entry points."""
    dist = importlib.metadata.distribution("cellpose-mcp")
    assert dist.version
    scripts = {ep.name for ep in dist.entry_points if ep.group == "console_scripts"}
    assert "cellpose-mcp" in scripts
    assert "cellpose-mcp-install" in scripts


@pytest.mark.integration
def test_install_cli_help_exits_zero() -> None:
    """Installer argparse wiring must work (what users run after pip install)."""
    proc = subprocess.run(
        [sys.executable, "-m", "cellpose_mcp.cli.install", "--help"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0
    assert "cursor" in proc.stdout
    assert "claude-desktop" in proc.stdout


@pytest.mark.integration
def test_server_module_help_exits_zero() -> None:
    """The MCP server entry point should expose help instead of starting the server."""
    proc = subprocess.run(
        [sys.executable, "-m", "cellpose_mcp", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "Run the Cellpose MCP server" in proc.stdout


@pytest.mark.integration
def test_installer_accepts_project_mcp_aliases(tmp_path: Path) -> None:
    """Claude Code should write a project-local MCP JSON config."""
    cwd = tmp_path / "claude-code"
    cwd.mkdir()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "cellpose_mcp.cli.install",
            "claude-code",
            "--python-path",
            sys.executable,
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    config = json.loads((cwd / ".mcp.json").read_text())
    assert config["mcpServers"]["cellpose"]["args"] == ["-m", "cellpose_mcp"]


@pytest.mark.integration
def test_installer_writes_codex_toml_config(tmp_path: Path) -> None:
    """Codex aliases should write Codex-compatible TOML MCP config."""
    home = tmp_path / "home"
    home.mkdir()
    env = {**os.environ, "HOME": str(home)}

    for app_name in ("codex", "codex-cli", "Codex-desktop"):
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "cellpose_mcp.cli.install",
                app_name,
                "--python-path",
                sys.executable,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        assert proc.returncode == 0, proc.stderr + proc.stdout

    config_path = home / ".codex" / "config.toml"
    text = config_path.read_text()
    assert "[mcp_servers.cellpose]" in text
    assert f'command = "{Path(sys.executable).resolve()}"' in text
    assert 'args = ["-m", "cellpose_mcp"]' in text
    assert "[mcp_servers.cellpose.env]" in text


@pytest.mark.integration
def test_installer_writes_project_codex_toml_config(tmp_path: Path) -> None:
    """Project-scoped Codex installs should write .codex/config.toml."""
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "cellpose_mcp.cli.install",
            "codex-project",
            "--python-path",
            sys.executable,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    text = (tmp_path / ".codex" / "config.toml").read_text()
    assert "[mcp_servers.cellpose]" in text


@pytest.mark.integration
def test_pep517_wheel_builds_no_deps(tmp_path: Path) -> None:
    """``pip wheel --no-deps`` must produce a wheel (sdist/PyPI installability)."""
    wheel_dir = tmp_path / "wheels"
    wheel_dir.mkdir()
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(REPO_ROOT),
            "--no-deps",
            "--no-build-isolation",
            "-w",
            str(wheel_dir),
        ],
        timeout=300,
    )
    wheels = list(wheel_dir.glob("cellpose_mcp-*.whl"))
    assert wheels, f"expected cellpose_mcp-*.whl under {wheel_dir}"


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.install_e2e
@pytest.mark.timeout(1200)
def test_fresh_venv_wheel_install_segment_e2e(tmp_path: Path) -> None:
    """Mimic a first-time user: venv, install wheel + deps, import, tools, segment.

    Downloads Cellpose/Torch dependencies and runs one CPU segmentation. Skippable
    locally via ``SKIP_INSTALL_E2E=1``; CI runs this in a dedicated workflow job.
    """
    if os.environ.get("SKIP_INSTALL_E2E", "").lower() in ("1", "true", "yes"):
        pytest.skip("SKIP_INSTALL_E2E is set")

    assert DEMO_IMAGE.is_file(), f"missing demo image: {DEMO_IMAGE}"

    wheel_dir = tmp_path / "wheels"
    wheel_dir.mkdir()
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(REPO_ROOT),
            "--no-deps",
            "--no-build-isolation",
            "-w",
            str(wheel_dir),
        ],
        timeout=300,
    )
    wheels = sorted(wheel_dir.glob("cellpose_mcp-*.whl"))
    assert len(wheels) == 1, wheels

    venv = tmp_path / "venv"
    _run([sys.executable, "-m", "venv", str(venv)], timeout=120)
    pip = str(venv / "bin" / "pip")
    py = str(venv / "bin" / "python")
    if sys.platform == "win32":
        pip = str(venv / "Scripts" / "pip.exe")
        py = str(venv / "Scripts" / "python.exe")

    _run([pip, "install", "--upgrade", "pip", "setuptools", "wheel"], timeout=300)
    _run([pip, "install", str(wheels[0])], timeout=1800)

    verify = r"""
import asyncio
import sys
from pathlib import Path

from cellpose_mcp.server import mcp
from cellpose_mcp import tools

repo = Path(sys.argv[1])
img = repo / "demo_images" / "img00.png"
assert img.is_file(), img

n_tools = len(asyncio.run(mcp.get_tools()))
assert n_tools >= 11, n_tools

info = tools.load_image_info(str(img))
assert "error" not in info, info
assert "shape" in info

models = tools.list_available_models()
assert "segmentation_models" in models

out = Path(sys.argv[2]) / "e2e_masks.png"
seg = tools.segment_cells_2d(
    str(img),
    model_type="cyto3",
    gpu=False,
    diameter=30,
    output_path=str(out),
)
assert "error" not in seg, seg
assert seg.get("cells_detected", 0) >= 1
assert out.is_file()
print("ok", seg["cells_detected"])
"""
    _run([py, "-c", verify, str(REPO_ROOT), str(tmp_path)], timeout=1100)


def test_cellpose_mcp_executable_exists_after_install() -> None:
    """Console script from metadata should resolve on PATH when env is set up."""
    script = shutil.which("cellpose-mcp")
    # In minimal tox/venv setups the script may be next to sys.executable
    if script is None:
        bindir = Path(sys.executable).resolve().parent
        candidate = bindir / (
            "cellpose-mcp.exe" if sys.platform == "win32" else "cellpose-mcp"
        )
        assert candidate.is_file(), (
            "cellpose-mcp console script not found on PATH or beside python"
        )
    else:
        assert Path(script).exists()
