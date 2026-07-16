# ruff: noqa: S603

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from cellpose_mcp.release.feature_manifest import (
    BOOTSTRAP_BLOCKER,
    CORE_TOOLS,
    BootstrapFeatureManifest,
    FeatureBootstrapGateError,
    assert_release_ready,
    load_feature_manifest,
    release_gate_failures,
)

ROOT = Path(__file__).parents[2]


def valid_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "target_release": "0.2.0",
        "release_blockers": [BOOTSTRAP_BLOCKER],
        "required_core_tools": list(CORE_TOOLS),
        "stable_features": [],
    }


def test_packaged_bootstrap_manifest_is_structurally_valid() -> None:
    manifest = load_feature_manifest()
    assert manifest.schema_version == 1
    assert manifest.target_release == "0.2.0"
    assert manifest.release_blockers == (BOOTSTRAP_BLOCKER,)
    assert manifest.required_core_tools == CORE_TOOLS
    assert manifest.stable_features == ()


def test_unknown_manifest_field_is_rejected() -> None:
    data = valid_data()
    data["invented"] = True
    with pytest.raises(ValidationError, match="extra_forbidden"):
        BootstrapFeatureManifest.model_validate(data)


def test_core_tool_sequence_cannot_shrink() -> None:
    data = valid_data()
    data["required_core_tools"] = list(CORE_TOOLS[:-1])
    with pytest.raises(ValidationError, match="approved 13-tool sequence"):
        BootstrapFeatureManifest.model_validate(data)


def test_bootstrap_schema_rejects_fabricated_stable_features() -> None:
    data = valid_data()
    data["stable_features"] = [
        {
            "feature_id": "fake.segment",
            "tool": "segment",
            "evidence": ["tests/fake.py::test_fake"],
        }
    ]
    with pytest.raises(
        ValidationError,
        match="schema version 1 forbids stable feature records",
    ):
        BootstrapFeatureManifest.model_validate(data)


def test_release_gate_is_blocked_by_matrix_and_every_core_tool() -> None:
    manifest = load_feature_manifest()
    failures = release_gate_failures(manifest)
    assert len(failures) == 14
    assert failures[0].code == "unresolved_core_matrix"
    assert failures[0].subject == BOOTSTRAP_BLOCKER
    assert {failure.subject for failure in failures[1:]} == set(CORE_TOOLS)
    assert {failure.code for failure in failures[1:]} == {"missing_stable_tool"}
    with pytest.raises(FeatureBootstrapGateError) as caught:
        assert_release_ready(manifest)
    assert caught.value.failures == failures


def test_check_command_distinguishes_development_and_release() -> None:
    development = subprocess.run(
        [sys.executable, "scripts/check_feature_manifest.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert development.returncode == 0
    assert "bootstrap manifest valid; release blockers: 14" in development.stdout

    release = subprocess.run(
        [sys.executable, "scripts/check_feature_manifest.py", "--release"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert release.returncode == 1
    assert "unresolved_core_matrix" in release.stdout
    assert release.stdout.count("missing_stable_tool") == 13
