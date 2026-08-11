"""Command-line interface tests."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from typer.testing import CliRunner

from cellpose_mcp.cli import app as cli_app

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_console_script_is_declared() -> None:
    """Package metadata should expose a user-facing Cellpose command CLI."""
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["cellpose-mcp-cli"] == (
        "cellpose_mcp.cli.app:main"
    )


def test_models_command_outputs_json(monkeypatch: Any) -> None:
    """The models command should print structured JSON for shell workflows."""
    fake_ops = SimpleNamespace(
        list_available_models=lambda: {
            "segmentation_models": ["cyto"],
            "restoration_models": {"denoise": ["denoise_cyto3"]},
            "all_models": ["cyto", "denoise_cyto3"],
        }
    )
    monkeypatch.setattr(cli_app, "_load_operations", lambda: fake_ops)

    result = CliRunner().invoke(cli_app.app, ["models"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["segmentation_models"] == ["cyto"]
    assert "denoise_cyto3" in payload["all_models"]


def test_cli_surface_excludes_training() -> None:
    """The simplified CLI should not expose model-training workflows."""
    result = CliRunner().invoke(cli_app.app, ["--help"])

    assert result.exit_code == 0
    assert "train-segmentation" not in result.stdout
    assert "segment-3d" in result.stdout


def test_segment_2d_command_parses_options_and_calls_operation(
    monkeypatch: Any,
) -> None:
    """The 2D segmentation command should pass CLI options to the core operation."""
    calls: list[dict[str, Any]] = []

    def fake_segment_cells_2d(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {
            "cells_detected": 3,
            "output_path": "out_masks.tif",
            "diameter": 12.5,
            "mask_shape": [10, 20],
        }

    fake_ops = SimpleNamespace(segment_cells_2d=fake_segment_cells_2d)
    monkeypatch.setattr(cli_app, "_load_operations", lambda: fake_ops)

    result = CliRunner().invoke(
        cli_app.app,
        [
            "segment-2d",
            "image.tif",
            "--model-type",
            "cyto2",
            "--diameter",
            "12.5",
            "--channels",
            "0,1",
            "--cpu",
            "--output",
            "out_masks.tif",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["cells_detected"] == 3
    assert calls == [
        {
            "image_path": "image.tif",
            "model_type": "cyto2",
            "diameter": 12.5,
            "channels": [0, 1],
            "flow_threshold": 0.4,
            "cellprob_threshold": 0.0,
            "min_size": 15,
            "gpu": False,
            "augment": False,
            "normalize": True,
            "invert": False,
            "output_path": "out_masks.tif",
        }
    ]


def test_segment_2d_cli_defaults_to_cyto3(monkeypatch: Any) -> None:
    """The CLI default should select the restoration-compatible CP3 model."""
    calls: list[dict[str, Any]] = []

    def fake_segment_cells_2d(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {"cells_detected": 0}

    monkeypatch.setattr(
        cli_app,
        "_load_operations",
        lambda: SimpleNamespace(segment_cells_2d=fake_segment_cells_2d),
    )

    result = CliRunner().invoke(cli_app.app, ["segment-2d", "image.tif", "--cpu"])

    assert result.exit_code == 0
    assert calls[0]["model_type"] == "cyto3"


def test_cli_returns_nonzero_when_operation_reports_error(monkeypatch: Any) -> None:
    """Operation error dictionaries should become failing shell exit codes."""
    fake_ops = SimpleNamespace(
        load_image_info=lambda image_path: {"error": "bad image"}
    )
    monkeypatch.setattr(cli_app, "_load_operations", lambda: fake_ops)

    result = CliRunner().invoke(cli_app.app, ["info", "missing.tif"])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"] == "bad image"


def test_operation_stdout_does_not_pollute_cli_json(monkeypatch: Any) -> None:
    """Progress text from operations should not corrupt JSON stdout."""

    def noisy_load_image_info(image_path: str) -> dict[str, Any]:
        print("cellpose progress")
        return {"shape": [1, 2], "image_path": image_path}

    fake_ops = SimpleNamespace(load_image_info=noisy_load_image_info)
    monkeypatch.setattr(cli_app, "_load_operations", lambda: fake_ops)

    result = CliRunner().invoke(cli_app.app, ["info", "image.tif"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["shape"] == [1, 2]
    assert "cellpose progress" not in result.stdout
