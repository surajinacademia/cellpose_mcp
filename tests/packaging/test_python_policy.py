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
