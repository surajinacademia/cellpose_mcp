"""Core operation wiring tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest


@pytest.mark.parametrize(
    ("operation_name", "kwargs"),
    [
        ("segment_cells_2d", {"image_path": "payload.npy", "gpu": False}),
        ("segment_cells_3d", {"image_path": "payload.npy", "gpu": False}),
        (
            "segment_cells_batch",
            {"image_paths": ["payload.npy"], "gpu": False},
        ),
        ("denoise_image", {"image_path": "payload.npy", "gpu": False}),
        ("deblur_image", {"image_path": "payload.npy", "gpu": False}),
        ("upsample_image", {"image_path": "payload.npy", "gpu": False}),
        ("restore_and_segment", {"image_path": "payload.npy", "gpu": False}),
        (
            "estimate_cell_diameter",
            {"image_path": "payload.npy", "gpu": False},
        ),
        ("save_masks", {"mask_path": "payload.npy"}),
        ("load_image_info", {"image_path": "payload.npy"}),
    ],
)
def test_pickle_backed_npy_inputs_are_rejected_before_cellpose(
    monkeypatch: Any,
    operation_name: str,
    kwargs: dict[str, Any],
) -> None:
    """Public operations must not reach Cellpose's allow_pickle=True reader."""
    from cellpose_mcp import operations

    def unsafe_reader_reached(path: str) -> np.ndarray:
        raise AssertionError(f"unsafe Cellpose reader reached for {path}")

    class ModelConstructedBeforeValidation:
        def __init__(self, **model_kwargs: Any) -> None:
            raise AssertionError("model constructed before input validation")

    monkeypatch.setattr(operations.io, "imread", unsafe_reader_reached)
    monkeypatch.setattr(
        operations.models,
        "CellposeModel",
        ModelConstructedBeforeValidation,
    )

    result = getattr(operations, operation_name)(**kwargs)

    assert result["error"] == (
        ".npy inputs are disabled because Cellpose loads them with pickle enabled"
    )


@pytest.mark.parametrize(
    ("operation_name", "model_kwargs", "expected_kind"),
    [
        ("segment_cells_2d", {"model_type": "custom-model"}, "segmentation"),
        ("segment_cells_3d", {"model_type": "custom-model"}, "segmentation"),
        ("segment_cells_batch", {"model_type": "custom-model"}, "segmentation"),
        (
            "estimate_cell_diameter",
            {"model_type": "custom-model"},
            "diameter-estimation",
        ),
        ("denoise_image", {"model_type": "custom-model"}, "denoise"),
        ("deblur_image", {"model_type": "custom-model"}, "deblur"),
        ("upsample_image", {"model_type": "custom-model"}, "upsample"),
        (
            "restore_and_segment",
            {"restoration_model": "custom-model"},
            "oneclick",
        ),
        (
            "restore_and_segment",
            {"segmentation_model": "custom-model"},
            "segmentation",
        ),
    ],
)
def test_unlisted_models_are_rejected_before_image_or_model_loading(
    monkeypatch: Any,
    operation_name: str,
    model_kwargs: dict[str, str],
    expected_kind: str,
) -> None:
    """Model fields must remain identifiers, never attacker-controlled paths."""
    from cellpose_mcp import operations

    monkeypatch.setattr(
        operations.io,
        "imread",
        lambda path: (_ for _ in ()).throw(
            AssertionError("image read before model validation")
        ),
    )
    kwargs: dict[str, Any]
    if operation_name == "segment_cells_batch":
        kwargs = {"image_paths": ["image.tif"], "gpu": False}
    else:
        kwargs = {"image_path": "image.tif", "gpu": False}
    kwargs.update(model_kwargs)

    result = getattr(operations, operation_name)(**kwargs)

    assert result["error"].startswith(f"unsupported {expected_kind} model")


def test_model_downloader_requires_verified_cellpose_https(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """Cellpose downloads must not disable certificate verification globally."""
    import ssl

    from cellpose_mcp import operations

    observed_contexts: list[ssl.SSLContext] = []

    class FakeResponse:
        headers = {"Content-Length": "4"}

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self, size: int) -> bytes:
            if getattr(self, "served", False):
                return b""
            self.served = True
            return b"data"

    def fake_urlopen(
        url: str,
        *,
        context: ssl.SSLContext,
        timeout: int,
    ) -> FakeResponse:
        assert url == "https://www.cellpose.org/models/cyto3"
        assert timeout == 60
        observed_contexts.append(context)
        return FakeResponse()

    monkeypatch.setattr(operations, "urlopen", fake_urlopen)
    destination = tmp_path / "cyto3"

    operations._secure_model_download(
        "https://www.cellpose.org/models/cyto3",
        str(destination),
        progress=False,
    )

    assert destination.read_bytes() == b"data"
    assert observed_contexts[0].verify_mode == ssl.CERT_REQUIRED
    with pytest.raises(ValueError, match="approved Cellpose HTTPS host"):
        operations._secure_model_download(
            "https://example.com/model",
            str(destination),
            progress=False,
        )

    class RedirectedResponse(FakeResponse):
        def geturl(self) -> str:
            return "https://example.com/redirected-model"

    monkeypatch.setattr(
        operations,
        "urlopen",
        lambda *args, **kwargs: RedirectedResponse(),
    )
    with pytest.raises(ValueError, match="approved Cellpose HTTPS host"):
        operations._secure_model_download(
            "https://www.cellpose.org/models/cyto3",
            str(destination),
            progress=False,
        )


def test_default_segmentation_model_is_cyto3() -> None:
    """Every segmentation entry point should use the CP3-compatible default."""
    from inspect import signature

    from cellpose_mcp import operations

    operations_with_model_defaults = (
        operations.segment_cells_2d,
        operations.segment_cells_3d,
        operations.segment_cells_batch,
        operations.estimate_cell_diameter,
    )

    for operation in operations_with_model_defaults:
        assert signature(operation).parameters["model_type"].default == "cyto3"


def test_core_operations_are_not_coupled_to_mcp() -> None:
    """Core operations should be importable without the MCP adapter module."""
    from cellpose_mcp import operations

    source = Path(operations.__file__).read_text()

    assert "mcp_instance" not in source
    assert operations.segment_cells_2d.__module__ == "cellpose_mcp.operations"
    assert operations.list_available_models.__module__ == "cellpose_mcp.operations"
    assert hasattr(operations, "segment_cells_3d")
    assert not hasattr(operations, "train_segmentation_model")


def test_model_inventory_only_advertises_supported_cellpose_models() -> None:
    """Every listed model identifier should be accepted by pinned Cellpose."""
    from cellpose import denoise

    from cellpose_mcp import operations

    inventory = operations.list_available_models()
    segmentation = inventory["segmentation_models"]
    restoration = [
        model
        for category in inventory["restoration_models"].values()
        for model in category
    ]

    assert set(segmentation) <= set(operations.models.MODEL_NAMES)
    assert set(restoration) <= set(denoise.MODEL_NAMES)
    assert inventory["all_models"] == segmentation + restoration


def test_segment_2d_reports_requested_diameter_when_cellpose_returns_invalid(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """Explicit user diameter should not be replaced by invalid Cellpose metadata."""
    from cellpose_mcp import operations

    class FakeModel:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def eval(
            self, *args: Any, **kwargs: Any
        ) -> tuple[np.ndarray, list[Any], float]:
            masks = np.array([[0, 1], [2, 2]], dtype=np.uint16)
            flows = [None, None, np.ones((2, 2), dtype=np.float32)]
            return masks, flows, -0.01

    monkeypatch.setattr(operations.io, "imread", lambda path: np.zeros((2, 2)))
    monkeypatch.setattr(operations.io, "imsave", lambda path, data: None)
    monkeypatch.setattr(
        operations.models, "CellposeModel", lambda **kwargs: FakeModel(**kwargs)
    )

    result = operations.segment_cells_2d(
        "image.tif",
        diameter=30,
        gpu=False,
        output_path=str(tmp_path / "masks.tif"),
    )

    assert result["diameter"] == 30.0
    assert result["cells_detected"] == 2


def test_segment_3d_passes_z_axis_for_zyx_stack(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """A plain ZYX volume should tell Cellpose which axis is Z."""
    from cellpose_mcp import operations

    calls: list[dict[str, Any]] = []

    class FakeModel:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def eval(
            self, *args: Any, **kwargs: Any
        ) -> tuple[np.ndarray, list[Any], float]:
            calls.append(kwargs)
            return np.zeros((3, 4, 5), dtype=np.uint16), [], 12.0

    monkeypatch.setattr(operations.io, "imread", lambda path: np.zeros((3, 4, 5)))
    monkeypatch.setattr(operations.io, "imsave", lambda path, data: None)
    monkeypatch.setattr(
        operations.models, "CellposeModel", lambda **kwargs: FakeModel(**kwargs)
    )

    result = operations.segment_cells_3d(
        "stack.tif",
        diameter=8,
        do_3d=False,
        stitch_threshold=0.1,
        output_path=str(tmp_path / "masks.tif"),
    )

    assert "error" not in result
    assert calls[0]["z_axis"] == 0
    assert calls[0]["diameter"] is None
    assert result["diameter"] == 8.0


def test_load_image_info_distinguishes_rgb_from_volume(monkeypatch: Any) -> None:
    """RGB images are channel images, not 3D volumes."""
    from cellpose_mcp import operations

    monkeypatch.setattr(
        operations.io, "imread", lambda path: np.zeros((10, 12, 3), dtype=np.uint8)
    )

    info = operations.load_image_info("rgb.png")

    assert info["channels"] == 3
    assert info["is_3d"] is False


def test_estimate_diameter_uses_cellpose_size_model(monkeypatch: Any) -> None:
    """Diameter estimation should use the CP3 wrapper that owns SizeModel."""
    from cellpose_mcp import operations

    class FakeCellpose:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def eval(
            self, *args: Any, **kwargs: Any
        ) -> tuple[None, None, None, np.ndarray]:
            return None, None, None, np.array([18.5])

    monkeypatch.setattr(
        operations.io, "imread", lambda path: np.zeros((4, 4), dtype=np.uint8)
    )
    monkeypatch.setattr(
        operations.models, "Cellpose", lambda **kwargs: FakeCellpose(**kwargs)
    )
    monkeypatch.setattr(
        operations.models,
        "CellposeModel",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("diameter estimation bypassed SizeModel")
        ),
    )

    result = operations.estimate_cell_diameter("image.tif", gpu=False)

    assert result == {
        "estimated_diameter": 18.5,
        "confidence": "high",
        "model_used": "cyto3",
    }


def test_restoration_nameerror_becomes_clear_compatibility_error(
    monkeypatch: Any,
) -> None:
    """Cellpose restoration internals should not leak as CPnet NameError."""
    from cellpose_mcp import operations

    class BrokenDenoiseModel:
        def __init__(self, **kwargs: Any) -> None:
            raise NameError("name 'CPnet' is not defined")

    monkeypatch.setattr(
        operations.io, "imread", lambda path: np.zeros((2, 2), dtype=np.uint8)
    )
    monkeypatch.setattr(operations, "DenoiseModel", BrokenDenoiseModel)

    result = operations.denoise_image("image.tif", gpu=False)

    assert "Cellpose restoration is unavailable" in result["error"]
    assert "CPnet" not in result["error"]


def test_upsample_maps_scale_factor_to_cellpose_diameter(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """A requested scale should be passed through Cellpose's diameter ratio."""
    from cellpose_mcp import operations

    calls: list[dict[str, Any]] = []

    class FakeUpsampleModel:
        diam_mean = 30.0

        def eval(self, image: np.ndarray, **kwargs: Any) -> np.ndarray:
            calls.append(kwargs)
            return np.zeros((8, 10), dtype=np.uint8)

    monkeypatch.setattr(
        operations.io, "imread", lambda path: np.zeros((4, 5), dtype=np.uint8)
    )
    monkeypatch.setattr(operations.io, "imsave", lambda path, data: None)
    monkeypatch.setattr(
        operations, "_denoise_model", lambda model_type, gpu: FakeUpsampleModel()
    )

    result = operations.upsample_image(
        "image.tif",
        scale_factor=2,
        gpu=False,
        output_path=str(tmp_path / "upsampled.tif"),
    )

    assert calls[0]["diameter"] == 15.0
    assert result["upsampled_shape"] == [8, 10]


def test_upsample_rejects_nonpositive_scale_factor() -> None:
    """Invalid scale factors should fail before loading a model."""
    from cellpose_mcp import operations

    result = operations.upsample_image("image.tif", scale_factor=0, gpu=False)

    assert result == {"error": "scale_factor must be at least 1"}


def test_restore_and_segment_accepts_four_value_return_shape(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """The supported four-value restoration result should be accepted."""
    from cellpose_mcp import operations

    class FakeCombinedModel:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def eval(
            self, *args: Any, **kwargs: Any
        ) -> tuple[np.ndarray, list[Any], Any, np.ndarray]:
            masks = np.array([[0, 1], [1, 0]], dtype=np.uint16)
            restored = np.ones((2, 2), dtype=np.uint8)
            return masks, [], None, restored

    monkeypatch.setattr(
        operations.io, "imread", lambda path: np.zeros((2, 2), dtype=np.uint8)
    )
    monkeypatch.setattr(operations.io, "imsave", lambda path, data: None)
    monkeypatch.setattr(operations, "CellposeDenoiseModel", FakeCombinedModel)

    result = operations.restore_and_segment(
        "image.tif",
        diameter=9,
        gpu=False,
        output_path_mask=str(tmp_path / "masks.tif"),
        output_path_restored=str(tmp_path / "restored.tif"),
    )

    assert "error" not in result
    assert result["diameter"] == 9.0
    assert result["cells_detected"] == 1
