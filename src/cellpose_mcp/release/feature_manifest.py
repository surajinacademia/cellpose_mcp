"""Bootstrap feature ledger that cannot authorize a release."""

from __future__ import annotations

import tomllib
from importlib.resources import files
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

CORE_TOOLS = (
    "get_capabilities",
    "inspect_image",
    "list_models",
    "prepare_model",
    "segment",
    "refine_segmentation",
    "measure_masks",
    "evaluate_segmentation",
    "export_segmentation",
    "train_model",
    "restore_image",
    "get_job",
    "cancel_job",
)
BOOTSTRAP_BLOCKER = "core_capability_matrix_unresolved"


class BootstrapFeatureManifest(BaseModel):
    """Schema used only until pinned upstream probes resolve feature granularity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    target_release: Literal["0.2.0"]
    release_blockers: tuple[Literal["core_capability_matrix_unresolved"], ...]
    required_core_tools: tuple[str, ...]
    stable_features: tuple[dict[str, object], ...] = ()

    @model_validator(mode="after")
    def enforce_bootstrap_block(self) -> Self:
        """Prevent core shrinkage or premature stable records."""
        if self.release_blockers != (BOOTSTRAP_BLOCKER,):
            raise ValueError("bootstrap blocker must remain active")
        if self.required_core_tools != CORE_TOOLS:
            raise ValueError("required_core_tools must match approved 13-tool sequence")
        if self.stable_features:
            raise ValueError("schema version 1 forbids stable feature records")
        return self


class GateFailure(BaseModel):
    """One deterministic reason the bootstrap ledger cannot ship."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: Literal["unresolved_core_matrix", "missing_stable_tool"]
    subject: str
    message: str


class FeatureBootstrapGateError(RuntimeError):
    """Raised whenever release mode is attempted during bootstrap."""

    def __init__(self, failures: tuple[GateFailure, ...]) -> None:
        """Retain every failure in deterministic order."""
        self.failures = failures
        summary = "; ".join(
            f"{failure.code}:{failure.subject}" for failure in failures
        )
        super().__init__(f"bootstrap feature manifest blocks release: {summary}")


def load_feature_manifest(
    path: Path | None = None,
) -> BootstrapFeatureManifest:
    """Load the packaged bootstrap ledger or an explicit test file."""
    if path is None:
        content = files("cellpose_mcp").joinpath("features.toml").read_text(
            encoding="utf-8"
        )
    else:
        content = path.read_text(encoding="utf-8")
    return BootstrapFeatureManifest.model_validate(tomllib.loads(content))


def release_gate_failures(
    manifest: BootstrapFeatureManifest,
) -> tuple[GateFailure, ...]:
    """Return the matrix blocker followed by all missing core tools."""
    failures = [
        GateFailure(
            code="unresolved_core_matrix",
            subject=manifest.release_blockers[0],
            message="Pinned CP4/CP3 probes have not resolved the core matrix.",
        )
    ]
    failures.extend(
        GateFailure(
            code="missing_stable_tool",
            subject=tool,
            message=f"{tool} has no stable feature record.",
        )
        for tool in manifest.required_core_tools
    )
    return tuple(failures)


def assert_release_ready(manifest: BootstrapFeatureManifest) -> None:
    """Always raise for bootstrap schema version 1."""
    raise FeatureBootstrapGateError(release_gate_failures(manifest))
