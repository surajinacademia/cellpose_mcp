from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[2]
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


def config() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_public_python_range_and_classifiers_are_exact() -> None:
    project = config()["project"]
    assert isinstance(project, dict)
    assert project["requires-python"] == ">=3.11,<3.13"
    assert project["classifiers"] == EXPECTED_CLASSIFIERS


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
