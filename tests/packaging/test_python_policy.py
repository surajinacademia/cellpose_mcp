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
