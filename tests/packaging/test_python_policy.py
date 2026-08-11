"""Release policy checks that guard supported Python and publication behavior."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[2]


def _config() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_release_metadata_and_entry_points_are_consistent() -> None:
    document = _config()
    project = document["project"]
    assert isinstance(project, dict)
    assert project["version"] == "0.1.5"
    assert project["requires-python"] == ">=3.11,<3.13"
    assert "cellpose==3.1.1.1" in project["dependencies"]
    assert "fastmcp>=2.10.3,<3" in project["dependencies"]
    assert project["scripts"] == {
        "cellpose-mcp": "cellpose_mcp.__main__:main",
        "cellpose-mcp-cli": "cellpose_mcp.cli.app:main",
        "cellpose-mcp-install": "cellpose_mcp.cli.install:main",
    }

    source = (ROOT / "src" / "cellpose_mcp" / "__init__.py").read_text()
    match = re.search(r'^__version__ = "([^"]+)"$', source, re.MULTILINE)
    assert match is not None
    assert match.group(1) == project["version"]


def test_package_data_contains_only_the_typing_marker() -> None:
    package_data = _config()["tool"]["setuptools"]["package-data"]
    assert package_data == {"cellpose_mcp": ["py.typed"]}
    assert not (ROOT / "src" / "cellpose_mcp" / "features.toml").exists()
    assert not (ROOT / "scripts" / "check_feature_manifest.py").exists()


def test_ci_runs_the_active_suite_on_supported_python_versions() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    normalized = " ".join(workflow.split())
    assert workflow.startswith("name: CI\n")
    assert 'python-version: ["3.11", "3.12"]' in normalized
    assert 'python -m pip install "uv==0.10.4"' in normalized
    assert "uv sync --locked" in normalized
    assert 'pytest -m "not slow"' in normalized
    assert "ruff check" in normalized
    assert "mypy" in normalized
    assert "feature_manifest" not in normalized
    assert "Foundation" not in workflow


def test_publish_workflow_verifies_before_granting_oidc() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish-pypi.yml").read_text()
    normalized = " ".join(workflow.split())
    assert "verify:" in workflow
    assert "publish:" in workflow
    assert "needs: verify" in workflow
    assert "id-token: write" in workflow
    assert "GITHUB_REF_NAME" in workflow
    assert "pyproject.toml" in workflow
    assert 'pytest -m "not slow"' in normalized
    assert "python -m build" in normalized
    assert "feature_manifest" not in workflow


def test_pre_commit_tests_fail_closed() -> None:
    config = (ROOT / ".pre-commit-config.yaml").read_text()
    assert "tests/test_tools.py" not in config
    assert "|| true" not in config
    assert (
        'uv run --frozen --no-sync pytest -m "not slow and not integration"' in config
    )
