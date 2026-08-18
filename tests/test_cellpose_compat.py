"""Network-free regression tests for the Cellpose 3 compatibility adapter."""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from cellpose import models as cellpose_models
from cellpose.denoise import MODEL_NAMES as RESTORATION_MODEL_NAMES

from cellpose_mcp import tools


@pytest.fixture
def fake_image_io(monkeypatch: pytest.MonkeyPatch) -> tuple[np.ndarray, list[tuple[str, np.ndarray]]]:
    """Replace Cellpose image I/O with in-memory data for contract tests."""
    image = np.arange(20, dtype=np.uint8).reshape(4, 5)
    saved: list[tuple[str, np.ndarray]] = []

    monkeypatch.setattr(tools.io, "imread", lambda _path: image.copy())
    monkeypatch.setattr(
        tools.io,
        "imsave",
        lambda path, array: saved.append((str(path), np.asarray(array).copy())),
    )
    return image, saved


def test_pyproject_pins_the_supported_cellpose_release_and_hotfix_version() -> None:
    """The adapter is only valid for the explicitly supported CP3 release."""
    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    contents = pyproject.read_text(encoding="utf-8")

    assert re.search(r'^version = "0\.1\.5"$', contents, re.MULTILINE)
    assert re.search(
        r'^\s*"cellpose==3\.1\.1\.2",\s*$', contents, re.MULTILINE
    )


@pytest.mark.parametrize(
    "tool_name",
    [
        "segment_cells_2d",
        "segment_cells_3d",
        "segment_cells_batch",
        "estimate_cell_diameter",
    ],
)
def test_cp3_model_defaults_are_cyto3(tool_name: str) -> None:
    """CP4's cpsam identifier must not leak into the CP3 adapter."""
    tool = getattr(tools, tool_name)
    assert inspect.signature(tool).parameters["model_type"].default == "cyto3"


def test_tools_source_has_no_cpsam_reference() -> None:
    """Prevent accidental reintroduction of a CP4-only default or fallback."""
    assert "cpsam" not in Path(tools.__file__).read_text(encoding="utf-8")


def test_advertised_models_exist_in_cellpose_3() -> None:
    """Every advertised identifier must select the requested CP3 model."""
    available = tools.list_available_models()
    segmentation = set(available["segmentation_models"])
    restoration = {
        model
        for model_names in available["restoration_models"].values()
        for model in model_names
    }

    assert segmentation <= set(cellpose_models.MODEL_NAMES)
    assert restoration <= set(RESTORATION_MODEL_NAMES)
    assert {"bact", "tissuenet", "livecell", "yeast"}.isdisjoint(segmentation)
    assert set(available["all_models"]) == segmentation | restoration


def test_unknown_model_is_rejected_before_cellpose_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown CP3 identifiers must not silently select cyto3."""

    def unexpected_model(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Cellpose constructor must not run")

    monkeypatch.setattr(tools.models, "CellposeModel", unexpected_model)

    result = tools.segment_cells_2d("sample.tif", model_type="bact", gpu=False)

    assert "unsupported segmentation model 'bact'" in result["error"]
    assert result["cells_detected"] == 0


def test_existing_custom_model_file_is_accepted_for_inference(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
    tmp_path: Path,
) -> None:
    """A model produced by the training tool must remain usable for inference."""
    custom_model = tmp_path / "custom-model"
    custom_model.touch()
    masks = np.array([[0, 1], [1, 0]], dtype=np.int32)
    instances: list[Any] = []

    class FakeCellposeModel:
        diam_mean = 30.0

        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            instances.append(self)

        def eval(
            self, *args: Any, **kwargs: Any
        ) -> tuple[np.ndarray, list[Any], np.ndarray]:
            return masks, [], np.array([1.0])

    monkeypatch.setattr(tools.models, "CellposeModel", FakeCellposeModel)

    result = tools.segment_cells_2d(
        "sample.tif", model_type=str(custom_model), gpu=False
    )

    assert "error" not in result
    assert result["cells_detected"] == 1
    assert instances[0].kwargs == {
        "gpu": False,
        "model_type": str(custom_model),
    }


def test_segment_2d_uses_cp3_tuple_and_model_diameter(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
) -> None:
    """A CP3 style vector must never be treated as the reported diameter."""
    _image, saved = fake_image_io
    masks = np.array([[0, 1], [2, 2]], dtype=np.int32)
    styles = np.array([999.0, 1000.0])
    instances: list[Any] = []

    class FakeCellposeModel:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            self.diam_mean = 31.0
            instances.append(self)

        def eval(self, *args: Any, **kwargs: Any) -> tuple[np.ndarray, list[Any], np.ndarray]:
            self.eval_args = args
            self.eval_kwargs = kwargs
            return masks, [None, None, np.array([0.25, 0.75])], styles

    monkeypatch.setattr(tools.models, "CellposeModel", FakeCellposeModel)

    result = tools.segment_cells_2d("sample.tif", gpu=False)

    assert set(result) == {
        "cells_detected",
        "output_path",
        "diameter",
        "mask_shape",
        "flow_quality",
    }
    assert result["cells_detected"] == 2
    assert result["diameter"] == 31.0
    assert result["mask_shape"] == [2, 2]
    assert result["flow_quality"] == 0.5
    assert instances[0].kwargs == {"gpu": False, "model_type": "cyto3"}
    assert instances[0].eval_kwargs == {
        "diameter": None,
        "channels": None,
        "flow_threshold": 0.4,
        "cellprob_threshold": 0.0,
        "min_size": 15,
        "augment": False,
        "normalize": True,
        "invert": False,
    }
    assert len(saved) == 1
    np.testing.assert_array_equal(saved[0][1], masks)


def test_segment_2d_reports_an_explicit_diameter(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
) -> None:
    """An explicit user diameter remains the public result value."""
    masks = np.array([[0, 1]], dtype=np.int32)
    instances: list[Any] = []

    class FakeCellposeModel:
        diam_mean = 30.0

        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            instances.append(self)

        def eval(self, *args: Any, **kwargs: Any) -> tuple[np.ndarray, list[Any], np.ndarray]:
            self.eval_kwargs = kwargs
            return masks, [], np.array([500.0])

    monkeypatch.setattr(tools.models, "CellposeModel", FakeCellposeModel)

    result = tools.segment_cells_2d("sample.tif", diameter=18.5, gpu=False)

    assert result["diameter"] == 18.5
    assert instances[0].eval_kwargs["diameter"] == 18.5


def test_segment_3d_uses_cp3_tuple_without_reading_styles_as_diameter(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
) -> None:
    """The 3D tool retains its result shape while using the CP3 contract."""
    masks = np.array([[[0, 1], [2, 2]]], dtype=np.int32)
    instances: list[Any] = []

    class FakeCellposeModel:
        diam_mean = 33.0

        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            instances.append(self)

        def eval(self, *args: Any, **kwargs: Any) -> tuple[np.ndarray, list[Any], np.ndarray]:
            self.eval_kwargs = kwargs
            return masks, [], np.array([777.0])

    monkeypatch.setattr(tools.models, "CellposeModel", FakeCellposeModel)

    result = tools.segment_cells_3d(
        "volume.tif",
        diameter=21.0,
        do_3d=False,
        anisotropy=2.0,
        flow3d_smooth=1.5,
        gpu=False,
    )

    assert set(result) == {
        "cells_detected",
        "output_path",
        "diameter",
        "volume_shape",
        "anisotropy_used",
        "method",
    }
    assert result["diameter"] == 21.0
    assert result["volume_shape"] == [1, 2, 2]
    assert result["method"] == "slice_stitch"
    assert instances[0].kwargs == {"gpu": False, "model_type": "cyto3"}
    assert instances[0].eval_kwargs == {
        "diameter": 21.0,
        "channels": None,
        "do_3D": False,
        "anisotropy": 2.0,
        "stitch_threshold": 0.0,
        "flow3D_smooth": 1.5,
    }


def test_batch_uses_model_type_and_cp3_tuple(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
) -> None:
    """Batch segmentation must select the requested CP3 model once."""
    masks = np.array([[0, 1], [1, 0]], dtype=np.int32)
    instances: list[Any] = []

    class FakeCellposeModel:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            self.eval_kwargs: list[dict[str, Any]] = []
            instances.append(self)

        def eval(self, *args: Any, **kwargs: Any) -> tuple[np.ndarray, list[Any], np.ndarray]:
            self.eval_kwargs.append(kwargs)
            return masks, [], np.array([333.0])

    monkeypatch.setattr(tools.models, "CellposeModel", FakeCellposeModel)

    result = tools.segment_cells_batch(
        ["first.tif", "second.tif"], model_type="nuclei", batch_size=3, gpu=False
    )

    assert result["total_images"] == 2
    assert result["successful"] == 2
    assert result["failed"] == 0
    assert instances[0].kwargs == {"gpu": False, "model_type": "nuclei"}
    assert instances[0].eval_kwargs == [
        {"diameter": None, "batch_size": 3},
        {"diameter": None, "batch_size": 3},
    ]


@pytest.mark.parametrize(
    ("tool_name", "model_type", "diameter", "shape_key"),
    [
        ("denoise_image", "denoise_cyto2", 24.0, "restored_shape"),
        ("deblur_image", "deblur_cyto2", 19.0, "restored_shape"),
    ],
)
def test_restoration_tools_select_the_requested_cp3_model(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
    tool_name: str,
    model_type: str,
    diameter: float,
    shape_key: str,
) -> None:
    """Built-in CP3 restoration identifiers belong in ``model_type``."""
    image, _saved = fake_image_io
    instances: list[Any] = []

    class FakeDenoiseModel:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            instances.append(self)

        def eval(self, *args: Any, **kwargs: Any) -> np.ndarray:
            self.eval_args = args
            self.eval_kwargs = kwargs
            return image + 1

    monkeypatch.setattr(tools, "DenoiseModel", FakeDenoiseModel)

    result = getattr(tools, tool_name)(
        "sample.tif", model_type=model_type, diameter=diameter, gpu=False
    )

    assert result[shape_key] == [4, 5]
    assert instances[0].kwargs == {"gpu": False, "model_type": model_type}
    assert instances[0].eval_kwargs == {"channels": None, "diameter": diameter}


def test_upsample_selects_the_requested_model_and_converts_scale_to_diameter(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
) -> None:
    """CP3 upsampling derives its interpolation ratio from the supplied diameter."""
    image, _saved = fake_image_io
    instances: list[Any] = []

    class FakeDenoiseModel:
        diam_mean = 40.0

        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            instances.append(self)

        def eval(self, *args: Any, **kwargs: Any) -> np.ndarray:
            self.eval_args = args
            self.eval_kwargs = kwargs
            return image + 1

    monkeypatch.setattr(tools, "DenoiseModel", FakeDenoiseModel)

    result = tools.upsample_image(
        "sample.tif", model_type="upsample_cyto2", scale_factor=4, gpu=False
    )

    assert result["upsampled_shape"] == [4, 5]
    assert result["scale_factor"] == 4
    assert instances[0].kwargs == {"gpu": False, "model_type": "upsample_cyto2"}
    assert instances[0].eval_kwargs == {"channels": None, "diameter": 10.0}


def test_upsample_rejects_a_factor_that_cp3_cannot_apply() -> None:
    """The response must not claim an upsampling factor that CP3 ignores."""
    result = tools.upsample_image("sample.tif", scale_factor=11, gpu=False)

    assert result == {"error": "scale_factor must be 2 or 4"}


def test_restore_and_segment_uses_the_cp3_combined_contract(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
) -> None:
    """Combined restoration has distinct model identifiers and a four-item result."""
    image, saved = fake_image_io
    masks = np.array([[0, 1], [2, 2]], dtype=np.int32)
    instances: list[Any] = []

    class FakeCellposeDenoiseModel:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            self.cp = SimpleNamespace(diam_mean=28.0)
            instances.append(self)

        def eval(
            self, image_arg: np.ndarray, *, diameter: float | None, channels: list[int] | None
        ) -> tuple[np.ndarray, list[Any], np.ndarray, np.ndarray]:
            self.eval_image = image_arg
            self.eval_kwargs = {"diameter": diameter, "channels": channels}
            return masks, [], np.array([444.0]), image + 1

    monkeypatch.setattr(tools, "CellposeDenoiseModel", FakeCellposeDenoiseModel)

    result = tools.restore_and_segment(
        "sample.tif",
        restoration_model="oneclick_cyto2",
        segmentation_model="nuclei",
        channels=[0, 0],
        gpu=False,
    )

    assert set(result) == {
        "cells_detected",
        "mask_path",
        "restored_image_path",
        "diameter",
        "mask_shape",
    }
    assert result["cells_detected"] == 2
    assert result["diameter"] == 28.0
    assert result["mask_shape"] == [2, 2]
    assert instances[0].kwargs == {
        "gpu": False,
        "restore_type": "oneclick_cyto2",
        "model_type": "nuclei",
    }
    assert instances[0].eval_kwargs == {"diameter": None, "channels": [0, 0]}
    assert len(saved) == 2


def test_estimate_diameter_uses_the_cp3_size_model_wrapper(
    monkeypatch: pytest.MonkeyPatch,
    fake_image_io: tuple[np.ndarray, list[tuple[str, np.ndarray]]],
) -> None:
    """True automatic sizing is available through ``models.Cellpose``, not CellposeModel."""
    instances: list[Any] = []

    class FakeCellpose:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs
            instances.append(self)

        def eval(self, *args: Any, **kwargs: Any) -> tuple[np.ndarray, list[Any], np.ndarray, np.ndarray]:
            self.eval_args = args
            self.eval_kwargs = kwargs
            return np.zeros((2, 2), dtype=np.int32), [], np.array([888.0]), np.array([37.5])

    def unexpected_cellpose_model(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("CellposeModel cannot perform true CP3 diameter estimation")

    monkeypatch.setattr(tools.models, "Cellpose", FakeCellpose, raising=False)
    monkeypatch.setattr(tools.models, "CellposeModel", unexpected_cellpose_model)

    result = tools.estimate_cell_diameter("sample.tif", channels=[0, 0], gpu=False)

    assert result == {
        "estimated_diameter": 37.5,
        "confidence": "high",
        "model_used": "cyto3",
    }
    assert instances[0].kwargs == {"gpu": False, "model_type": "cyto3"}
    assert instances[0].eval_kwargs == {"channels": [0, 0], "diameter": None}


def test_estimate_diameter_rejects_models_without_a_cp3_size_model() -> None:
    """Diameter estimation must only advertise CP3 size-model identifiers."""
    result = tools.estimate_cell_diameter(
        "sample.tif", model_type="livecell_cp3", gpu=False
    )

    assert "unsupported diameter-estimation model 'livecell_cp3'" in result["error"]
    assert result["estimated_diameter"] == 0.0


def test_training_returns_the_path_written_by_cellpose_3(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The training result must use Cellpose's returned path and model name."""
    from cellpose import train

    train_data = [np.zeros((4, 5), dtype=np.float32)]
    train_labels = [np.zeros((4, 5), dtype=np.int32)]
    expected_path = tmp_path / "output" / "models" / "custom-model"
    calls: list[dict[str, Any]] = []

    class FakeCellposeModel:
        net = object()

        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

    def fake_train_seg(*args: Any, **kwargs: Any) -> tuple[Path, np.ndarray, np.ndarray]:
        calls.append({"args": args, "kwargs": kwargs})
        return expected_path, np.array([1.0]), np.array([2.0])

    monkeypatch.setattr(tools.os, "listdir", lambda _path: [])
    monkeypatch.setattr(
        tools.io,
        "load_train_test_data",
        lambda *args, **kwargs: (train_data, train_labels),
    )
    monkeypatch.setattr(tools.models, "CellposeModel", FakeCellposeModel)
    monkeypatch.setattr(train, "train_seg", fake_train_seg)

    result = tools.train_segmentation_model(
        train_dir="images",
        train_labels_dir="labels",
        model_name="custom-model",
        gpu=False,
        output_dir=str(tmp_path / "output"),
    )

    assert result["status"] == "completed"
    assert result["model_path"] == str(expected_path)
    assert calls[0]["kwargs"]["model_name"] == "custom-model"
