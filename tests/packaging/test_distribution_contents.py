# ruff: noqa: S603

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tarfile
import venv
import warnings
import zipfile
from pathlib import Path, PurePosixPath

import pytest

ROOT = Path(__file__).parents[2]
GIT = shutil.which("git")
if GIT is None:
    raise RuntimeError("Git is required for clean-clone package tests")

_NETWORK_ENVIRONMENT_VARIABLES = frozenset(
    {
        "ALL_PROXY",
        "CURL_CA_BUNDLE",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "PIP_CERT",
        "PIP_CLIENT_CERT",
        "PIP_EXTRA_INDEX_URL",
        "PIP_FIND_LINKS",
        "PIP_INDEX_URL",
        "PIP_PROXY",
        "PIP_TRUSTED_HOST",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "all_proxy",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)


def _offline_subprocess_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in _NETWORK_ENVIRONMENT_VARIABLES:
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


def _install_wheel(python: Path, wheel: Path) -> None:
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-index",
            "--no-deps",
            str(wheel),
        ],
        check=True,
        env=_offline_subprocess_environment(),
    )


VALID_WHEEL_PATHS = {
    "cellpose_mcp/__init__.py",
    "cellpose_mcp/__main__.py",
    "cellpose_mcp/features.toml",
    "cellpose_mcp/mcp_instance.py",
    "cellpose_mcp/py.typed",
    "cellpose_mcp/server.py",
    "cellpose_mcp/tools.py",
    "cellpose_mcp/cli/__init__.py",
    "cellpose_mcp/cli/install.py",
    "cellpose_mcp/release/__init__.py",
    "cellpose_mcp/release/feature_manifest.py",
    "cellpose_mcp-0.1.4.dist-info/licenses/LICENSE",
    "cellpose_mcp-0.1.4.dist-info/METADATA",
    "cellpose_mcp-0.1.4.dist-info/WHEEL",
    "cellpose_mcp-0.1.4.dist-info/entry_points.txt",
    "cellpose_mcp-0.1.4.dist-info/top_level.txt",
    "cellpose_mcp-0.1.4.dist-info/RECORD",
}
VALID_SDIST_PATHS = {
    "LICENSE",
    "MANIFEST.in",
    "PKG-INFO",
    "README.md",
    "pyproject.toml",
    "setup.cfg",
    "src/cellpose_mcp/__init__.py",
    "src/cellpose_mcp/__main__.py",
    "src/cellpose_mcp/cli/__init__.py",
    "src/cellpose_mcp/cli/install.py",
    "src/cellpose_mcp/features.toml",
    "src/cellpose_mcp/mcp_instance.py",
    "src/cellpose_mcp/py.typed",
    "src/cellpose_mcp/release/__init__.py",
    "src/cellpose_mcp/release/feature_manifest.py",
    "src/cellpose_mcp/server.py",
    "src/cellpose_mcp/tools.py",
    "src/cellpose_mcp.egg-info/SOURCES.txt",
}


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
            "--no-isolation",
            "--wheel",
            "--sdist",
            "--outdir",
            str(output),
        ],
        cwd=source,
        check=True,
        env=_offline_subprocess_environment(),
    )
    return next(output.glob("*.whl")), next(output.glob("*.tar.gz"))


def _unique_member_names(member_names: list[str]) -> set[str]:
    unique = set(member_names)
    assert len(unique) == len(member_names), member_names
    return unique


def _wheel_paths(wheel: Path) -> set[str]:
    with zipfile.ZipFile(wheel) as archive:
        return _unique_member_names(archive.namelist())


def stripped_sdist_paths(sdist: Path) -> set[str]:
    with tarfile.open(sdist, mode="r:gz") as archive:
        members = archive.getmembers()
    assert members
    _unique_member_names([member.name for member in members])
    roots: set[str] = set()
    stripped: set[str] = set()
    for member in members:
        name = member.name
        assert name
        assert "\\" not in name
        path = PurePosixPath(name)
        assert not path.is_absolute()
        assert all(part not in {"", ".", ".."} for part in name.split("/"))
        assert path.as_posix() == name
        roots.add(path.parts[0])
        if member.isdir():
            continue
        assert member.isfile()
        assert len(path.parts) > 1
        stripped.add(PurePosixPath(*path.parts[1:]).as_posix())
    assert len(roots) == 1
    root = next(iter(roots))
    assert root.startswith("cellpose_mcp-")
    return stripped


def _validate_no_cache_or_junk(paths: set[str]) -> None:
    assert not any(
        path.endswith((".pyc", ".pyo", ".DS_Store"))
        or "__pycache__" in PurePosixPath(path).parts
        for path in paths
    )


def _validate_wheel_paths(wheel_paths: set[str]) -> None:
    _validate_no_cache_or_junk(wheel_paths)
    assert wheel_paths == VALID_WHEEL_PATHS, {
        "missing": sorted(VALID_WHEEL_PATHS - wheel_paths),
        "unexpected": sorted(wheel_paths - VALID_WHEEL_PATHS),
    }


def _validate_sdist_paths(sdist_paths: set[str]) -> None:
    _validate_no_cache_or_junk(sdist_paths)
    assert sdist_paths == VALID_SDIST_PATHS, {
        "missing": sorted(VALID_SDIST_PATHS - sdist_paths),
        "unexpected": sorted(sdist_paths - VALID_SDIST_PATHS),
    }


def _write_synthetic_sdist(
    tmp_path: Path,
    member_names: tuple[str, ...],
) -> Path:
    sdist = tmp_path / "synthetic.tar.gz"
    with tarfile.open(sdist, mode="w:gz") as archive:
        for index, name in enumerate(member_names):
            content = f"payload-{index}".encode()
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return sdist


def _write_synthetic_wheel(
    tmp_path: Path,
    member_names: tuple[str, ...],
) -> Path:
    wheel = tmp_path / "synthetic.whl"
    with zipfile.ZipFile(wheel, mode="w") as archive:
        for index, name in enumerate(member_names):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(name, f"payload-{index}")
    return wheel


def _poison_network_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, str]:
    poisoned = dict.fromkeys(
        _NETWORK_ENVIRONMENT_VARIABLES,
        "https://poison.invalid/simple",
    )
    poisoned.update(
        {
            "PIP_CONFIG_FILE": "/poison/pip.conf",
            "PIP_DISABLE_PIP_VERSION_CHECK": "0",
            "PIP_NO_INDEX": "0",
            "PYTHONNOUSERSITE": "0",
            "PYTHONPATH": "/poison/pythonpath",
        }
    )
    for name, value in poisoned.items():
        monkeypatch.setenv(name, value)
    return poisoned


def _assert_offline_environment(
    environment: object,
    poisoned: dict[str, str],
) -> None:
    assert isinstance(environment, dict)
    assert _NETWORK_ENVIRONMENT_VARIABLES.isdisjoint(environment)
    assert environment["PIP_CONFIG_FILE"] == os.devnull
    assert environment["PIP_DISABLE_PIP_VERSION_CHECK"] == "1"
    assert environment["PIP_NO_INDEX"] == "1"
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["PYTHONPATH"] == ""
    assert all(
        os.environ[name] == value
        for name, value in poisoned.items()
    )


def test_clean_clone_build_is_dependency_checked_and_offline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    poisoned = _poison_network_environment(monkeypatch)
    source = tmp_path / "source"
    output = tmp_path / "dist"
    expected_wheel = output / "cellpose_mcp-0.1.4-py3-none-any.whl"
    expected_sdist = output / "cellpose_mcp-0.1.4.tar.gz"
    calls: list[tuple[list[str], dict[str, object]]] = []

    def record_run(command: list[str], **kwargs: object) -> None:
        calls.append((command, kwargs))
        if command[0] == GIT:
            source.mkdir()
            return
        output.mkdir()
        expected_wheel.write_bytes(b"")
        expected_sdist.write_bytes(b"")

    monkeypatch.setattr(subprocess, "run", record_run)

    wheel, sdist = build_from_clean_clone(tmp_path)

    assert (wheel, sdist) == (expected_wheel, expected_sdist)
    assert len(calls) == 2
    build_command, build_kwargs = calls[1]
    assert build_command == [
        sys.executable,
        "-m",
        "build",
        "--no-isolation",
        "--wheel",
        "--sdist",
        "--outdir",
        str(output),
    ]
    assert "--skip-dependency-check" not in build_command
    assert set(build_kwargs) == {"check", "cwd", "env"}
    assert build_kwargs["check"] is True
    assert build_kwargs["cwd"] == source
    _assert_offline_environment(build_kwargs["env"], poisoned)


def test_wheel_install_is_no_index_and_offline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    poisoned = _poison_network_environment(monkeypatch)
    python = tmp_path / "installed/bin/python"
    wheel = tmp_path / "cellpose_mcp-0.1.4-py3-none-any.whl"
    calls: list[tuple[list[str], dict[str, object]]] = []

    def record_run(command: list[str], **kwargs: object) -> None:
        calls.append((command, kwargs))

    monkeypatch.setattr(subprocess, "run", record_run)

    _install_wheel(python, wheel)

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == [
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-index",
        "--no-deps",
        str(wheel),
    ]
    assert set(kwargs) == {"check", "env"}
    assert kwargs["check"] is True
    _assert_offline_environment(kwargs["env"], poisoned)


def test_wheel_paths_rejects_duplicate_members(tmp_path: Path) -> None:
    name = "cellpose_mcp/__init__.py"
    wheel = _write_synthetic_wheel(tmp_path, (name, name))
    with pytest.raises(AssertionError):
        _wheel_paths(wheel)


def test_stripped_sdist_paths_rejects_duplicate_members(
    tmp_path: Path,
) -> None:
    name = "cellpose_mcp-0.1.4/src/cellpose_mcp/__init__.py"
    sdist = _write_synthetic_sdist(tmp_path, (name, name))
    with pytest.raises(AssertionError):
        stripped_sdist_paths(sdist)


@pytest.mark.parametrize(
    "payload",
    [
        "cellpose_mcp/.cache/token",
        "cellpose_mcp/model.bin",
        "cellpose_mcp/credentials.json",
    ],
)
def test_wheel_validator_rejects_unapproved_package_payload(
    payload: str,
) -> None:
    with pytest.raises(AssertionError):
        _validate_wheel_paths(VALID_WHEEL_PATHS | {payload})


@pytest.mark.parametrize(
    "payload",
    [
        "fake.dist-info/credentials.json",
        "nested/fake.dist-info/METADATA",
    ],
)
def test_wheel_validator_rejects_fake_or_nested_dist_info(
    payload: str,
) -> None:
    with pytest.raises(AssertionError):
        _validate_wheel_paths(VALID_WHEEL_PATHS | {payload})


@pytest.mark.parametrize(
    "payload",
    [
        "src/cellpose_mcp/.env",
        "src/cellpose_mcp/model.bin",
        "src/cellpose_mcp/__pycache__/tools.pyc",
        "src/cellpose_mcp/.DS_Store",
        "src/cellpose_mcp.egg-info/credentials.json",
    ],
)
def test_sdist_validator_rejects_unapproved_package_payload(
    payload: str,
) -> None:
    with pytest.raises(AssertionError):
        _validate_sdist_paths(VALID_SDIST_PATHS | {payload})


@pytest.mark.parametrize(
    "member_names",
    [
        ("cellpose_mcp-0.1.4/README.md", "other-root/LICENSE"),
        ("orphan.txt",),
        ("/absolute.txt",),
        ("cellpose_mcp-0.1.4/../secret.txt",),
    ],
)
def test_stripped_sdist_paths_rejects_unsafe_or_mixed_roots(
    tmp_path: Path,
    member_names: tuple[str, ...],
) -> None:
    sdist = _write_synthetic_sdist(tmp_path, member_names)
    with pytest.raises(AssertionError):
        stripped_sdist_paths(sdist)


@pytest.mark.integration
def test_clean_wheel_sdist_and_installed_manifest_metadata(
    tmp_path: Path,
) -> None:
    wheel, sdist = build_from_clean_clone(tmp_path)
    wheel_paths = _wheel_paths(wheel)
    _validate_wheel_paths(wheel_paths)

    sdist_paths = stripped_sdist_paths(sdist)
    _validate_sdist_paths(sdist_paths)

    environment = tmp_path / "installed"
    venv.EnvBuilder(
        with_pip=True,
        symlinks=True,
        system_site_packages=False,
    ).create(environment)
    python = environment / "bin" / "python"
    _install_wheel(python, wheel)
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
        env=_offline_subprocess_environment(),
    )
