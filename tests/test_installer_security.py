"""Security regression tests for MCP configuration installation."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from cellpose_mcp.cli import install


def test_resolve_python_path_persists_the_resolved_executable(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    executable = tmp_path / "python"
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o700)
    monkeypatch.setattr(install.shutil, "which", lambda value: str(executable))

    assert install.resolve_python_path("python") == str(executable.resolve())


def test_python_verification_is_isolated_and_does_not_import_project_code(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def record_run(command: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(install.subprocess, "run", record_run)
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "hostile"))
    monkeypatch.setenv("PYTHONHOME", str(tmp_path / "hostile-home"))

    assert install.verify_python_can_import("/trusted/python") is True
    command, kwargs = calls[0]
    assert command[:3] == ["/trusted/python", "-I", "-c"]
    assert "importlib.metadata.distribution" in command[3]
    assert "import cellpose_mcp" not in command[3]
    assert "PYTHONPATH" not in kwargs["env"]
    assert "PYTHONHOME" not in kwargs["env"]


def test_json_config_refuses_a_project_controlled_symlink(tmp_path: Path) -> None:
    target = tmp_path / "outside.json"
    target.write_text("keep me")
    config = tmp_path / "project" / ".mcp.json"
    config.parent.mkdir()
    config.symlink_to(target)

    assert (
        install.write_mcp_config(
            config,
            "/trusted/python",
            trusted_root=config.parent,
        )
        is False
    )
    assert target.read_text() == "keep me"
    assert config.is_symlink()


def test_codex_config_refuses_a_symlinked_project_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / ".codex").symlink_to(outside, target_is_directory=True)

    assert (
        install.write_codex_config(
            project / ".codex" / "config.toml",
            "/trusted/python",
            trusted_root=project,
        )
        is False
    )
    assert not (outside / "config.toml").exists()


def test_malformed_json_config_is_preserved(tmp_path: Path) -> None:
    config = tmp_path / "mcp.json"
    config.write_text("{ malformed")

    assert (
        install.write_mcp_config(
            config,
            "/trusted/python",
            trusted_root=tmp_path,
        )
        is False
    )
    assert config.read_text() == "{ malformed"


def test_config_publication_is_private_and_preserves_other_servers(
    tmp_path: Path,
) -> None:
    config = tmp_path / "mcp.json"
    config.write_text(json.dumps({"mcpServers": {"other": {"command": "other"}}}))
    config.chmod(0o644)

    assert install.write_mcp_config(
        config,
        "/trusted/python",
        trusted_root=tmp_path,
    )

    payload = json.loads(config.read_text())
    assert payload["mcpServers"]["other"] == {"command": "other"}
    assert payload["mcpServers"]["cellpose"]["command"] == "/trusted/python"
    assert stat.S_IMODE(config.stat().st_mode) == 0o600


def test_codex_toml_update_preserves_header_with_trailing_comment(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        "[mcp_servers.cellpose]\n"
        'command = "old"\n\n'
        '[projects."/important"] # keep this table\n'
        'trust_level = "trusted"\n'
    )

    assert install.write_codex_config(
        config,
        "/trusted/python",
        trusted_root=tmp_path,
    )

    text = config.read_text()
    assert '[projects."/important"] # keep this table' in text
    assert 'trust_level = "trusted"' in text
    assert 'command = "/trusted/python"' in text


def test_project_config_paths_remain_under_their_project_root(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert install.get_codex_project_config_path() == (
        tmp_path / ".codex" / "config.toml"
    )
    assert os.path.commonpath(
        [tmp_path, install.get_codex_project_config_path()]
    ) == str(tmp_path)
