"""User-facing command-line interface for Cellpose operations."""

from __future__ import annotations

import json
from contextlib import redirect_stderr, redirect_stdout
from functools import lru_cache
from io import StringIO
from pathlib import Path
from typing import Any, cast

import typer

app = typer.Typer(
    help="Run Cellpose segmentation, restoration, and utility operations.",
    no_args_is_help=True,
)


@lru_cache(maxsize=1)
def _load_operations() -> Any:
    """Import operations lazily so CLI help stays lightweight."""
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
        from cellpose_mcp import operations

    return operations


def _call_operation(name: str, **kwargs: Any) -> dict[str, Any]:
    """Call a core operation while keeping command stdout machine-readable."""
    with redirect_stdout(StringIO()):
        result = getattr(_load_operations(), name)(**kwargs)
    return cast("dict[str, Any]", result)


def _parse_channels(channels: str | None) -> list[int] | None:
    """Parse comma-separated Cellpose channel arguments."""
    if channels is None or channels.strip() == "":
        return None
    try:
        return [int(channel.strip()) for channel in channels.split(",")]
    except ValueError as exc:
        raise typer.BadParameter("channels must be comma-separated integers") from exc


def _path(path: Path | None) -> str | None:
    """Convert optional Path options to strings for core operations."""
    return str(path) if path is not None else None


def _emit_result(result: dict[str, Any]) -> None:
    """Print JSON and fail the command if the operation returned an error."""
    typer.echo(json.dumps(result, indent=2))
    if "error" in result:
        raise typer.Exit(1)


@app.command("models")
def models() -> None:
    """List available pretrained Cellpose models."""
    _emit_result(_call_operation("list_available_models"))


@app.command("info")
def info(image: Path) -> None:
    """Get image metadata."""
    _emit_result(_call_operation("load_image_info", image_path=str(image)))


@app.command("estimate-diameter")
def estimate_diameter(
    image: Path,
    model_type: str = typer.Option("cyto3", help="Cellpose model type."),
    channels: str | None = typer.Option(
        None,
        help="Comma-separated channel specification, for example 0,1.",
    ),
    gpu: bool = typer.Option(True, "--gpu/--cpu", help="Use GPU acceleration."),
) -> None:
    """Estimate cell diameter from an image."""
    _emit_result(
        _call_operation(
            "estimate_cell_diameter",
            image_path=str(image),
            model_type=model_type,
            channels=_parse_channels(channels),
            gpu=gpu,
        )
    )


@app.command("segment-2d")
def segment_2d(
    image: Path,
    model_type: str = typer.Option("cyto3", help="Cellpose model type."),
    diameter: float = typer.Option(0, help="Expected diameter in pixels; 0 = auto."),
    channels: str | None = typer.Option(
        None,
        help="Comma-separated channel specification, for example 0,1.",
    ),
    flow_threshold: float = typer.Option(0.4, help="Cellpose flow threshold."),
    cellprob_threshold: float = typer.Option(0.0, help="Cell probability threshold."),
    min_size: int = typer.Option(15, help="Minimum cell size in pixels."),
    gpu: bool = typer.Option(True, "--gpu/--cpu", help="Use GPU acceleration."),
    augment: bool = typer.Option(False, help="Use test-time augmentation."),
    normalize: bool = typer.Option(
        True,
        "--normalize/--no-normalize",
        help="Normalize image intensities.",
    ),
    invert: bool = typer.Option(False, help="Invert image intensities."),
    output_path: Path | None = typer.Option(
        None,
        "--output",
        help="Optional mask output path.",
    ),
) -> None:
    """Segment cells in a 2D microscopy image."""
    _emit_result(
        _call_operation(
            "segment_cells_2d",
            image_path=str(image),
            model_type=model_type,
            diameter=diameter,
            channels=_parse_channels(channels),
            flow_threshold=flow_threshold,
            cellprob_threshold=cellprob_threshold,
            min_size=min_size,
            gpu=gpu,
            augment=augment,
            normalize=normalize,
            invert=invert,
            output_path=_path(output_path),
        )
    )


@app.command("segment-3d")
def segment_3d(
    image: Path,
    model_type: str = typer.Option("cyto3", help="Cellpose model type."),
    diameter: float = typer.Option(0, help="Expected diameter in pixels; 0 = auto."),
    do_3d: bool = typer.Option(True, "--do-3d/--slice-stitch", help="Use full 3D."),
    anisotropy: float | None = typer.Option(None, help="Z/XY pixel-size ratio."),
    stitch_threshold: float = typer.Option(0.0, help="Slice stitching threshold."),
    flow3d_smooth: float = typer.Option(0, help="3D flow smoothing factor."),
    channels: str | None = typer.Option(
        None,
        help="Comma-separated channel specification, for example 0,1.",
    ),
    gpu: bool = typer.Option(True, "--gpu/--cpu", help="Use GPU acceleration."),
    output_path: Path | None = typer.Option(
        None,
        "--output",
        help="Optional mask output path.",
    ),
) -> None:
    """Segment cells in a 3D microscopy volume."""
    _emit_result(
        _call_operation(
            "segment_cells_3d",
            image_path=str(image),
            model_type=model_type,
            diameter=diameter,
            do_3d=do_3d,
            anisotropy=anisotropy,
            stitch_threshold=stitch_threshold,
            flow3d_smooth=flow3d_smooth,
            channels=_parse_channels(channels),
            gpu=gpu,
            output_path=_path(output_path),
        )
    )


@app.command("batch")
def batch(
    image_paths: list[Path],
    model_type: str = typer.Option("cyto3", help="Cellpose model type."),
    diameter: float = typer.Option(0, help="Expected diameter in pixels; 0 = auto."),
    output_dir: Path | None = typer.Option(None, help="Directory for mask outputs."),
    gpu: bool = typer.Option(True, "--gpu/--cpu", help="Use GPU acceleration."),
    batch_size: int = typer.Option(8, help="Cellpose batch size."),
) -> None:
    """Segment cells in multiple images."""
    _emit_result(
        _call_operation(
            "segment_cells_batch",
            image_paths=[str(image_path) for image_path in image_paths],
            model_type=model_type,
            diameter=diameter,
            output_dir=_path(output_dir),
            gpu=gpu,
            batch_size=batch_size,
        )
    )


@app.command("denoise")
def denoise(
    image: Path,
    model_type: str = typer.Option("denoise_cyto3", help="Restoration model type."),
    channels: str | None = typer.Option(
        None,
        help="Comma-separated channel specification, for example 0,1.",
    ),
    diameter: float = typer.Option(30.0, help="Expected object diameter."),
    gpu: bool = typer.Option(True, "--gpu/--cpu", help="Use GPU acceleration."),
    output_path: Path | None = typer.Option(None, "--output", help="Output path."),
) -> None:
    """Denoise a microscopy image."""
    _emit_result(
        _call_operation(
            "denoise_image",
            image_path=str(image),
            model_type=model_type,
            channels=_parse_channels(channels),
            diameter=diameter,
            gpu=gpu,
            output_path=_path(output_path),
        )
    )


@app.command("deblur")
def deblur(
    image: Path,
    model_type: str = typer.Option("deblur_cyto3", help="Restoration model type."),
    channels: str | None = typer.Option(
        None,
        help="Comma-separated channel specification, for example 0,1.",
    ),
    diameter: float = typer.Option(30.0, help="Expected object diameter."),
    gpu: bool = typer.Option(True, "--gpu/--cpu", help="Use GPU acceleration."),
    output_path: Path | None = typer.Option(None, "--output", help="Output path."),
) -> None:
    """Deblur a microscopy image."""
    _emit_result(
        _call_operation(
            "deblur_image",
            image_path=str(image),
            model_type=model_type,
            channels=_parse_channels(channels),
            diameter=diameter,
            gpu=gpu,
            output_path=_path(output_path),
        )
    )


@app.command("upsample")
def upsample(
    image: Path,
    model_type: str = typer.Option("upsample_cyto3", help="Upsampling model type."),
    scale_factor: int = typer.Option(2, help="Requested upsampling factor."),
    channels: str | None = typer.Option(
        None,
        help="Comma-separated channel specification, for example 0,1.",
    ),
    gpu: bool = typer.Option(True, "--gpu/--cpu", help="Use GPU acceleration."),
    output_path: Path | None = typer.Option(None, "--output", help="Output path."),
) -> None:
    """Upsample a microscopy image."""
    _emit_result(
        _call_operation(
            "upsample_image",
            image_path=str(image),
            model_type=model_type,
            scale_factor=scale_factor,
            channels=_parse_channels(channels),
            gpu=gpu,
            output_path=_path(output_path),
        )
    )


@app.command("restore-and-segment")
def restore_and_segment(
    image: Path,
    restoration_model: str = typer.Option("oneclick_cyto3", help="Restoration model."),
    segmentation_model: str = typer.Option("cyto3", help="Segmentation model."),
    diameter: float = typer.Option(0, help="Expected diameter in pixels; 0 = auto."),
    channels: str | None = typer.Option(
        None,
        help="Comma-separated channel specification, for example 0,1.",
    ),
    gpu: bool = typer.Option(True, "--gpu/--cpu", help="Use GPU acceleration."),
    output_path_mask: Path | None = typer.Option(
        None,
        "--output-mask",
        help="Optional mask output path.",
    ),
    output_path_restored: Path | None = typer.Option(
        None,
        "--output-restored",
        help="Optional restored-image output path.",
    ),
) -> None:
    """Restore and segment an image in one pipeline."""
    _emit_result(
        _call_operation(
            "restore_and_segment",
            image_path=str(image),
            restoration_model=restoration_model,
            segmentation_model=segmentation_model,
            diameter=diameter,
            channels=_parse_channels(channels),
            gpu=gpu,
            output_path_mask=_path(output_path_mask),
            output_path_restored=_path(output_path_restored),
        )
    )


@app.command("save-masks")
def save_masks(
    mask: Path,
    output_format: str = typer.Option("tif", help="Mask output format."),
    output_path: Path | None = typer.Option(None, "--output", help="Output path."),
    image_path: Path | None = typer.Option(
        None,
        "--image",
        help="Optional original image for overlay generation.",
    ),
    save_flows: bool = typer.Option(False, help="Reserved for future flow output."),
) -> None:
    """Save masks plus outlines and overlay visualizations."""
    _emit_result(
        _call_operation(
            "save_masks",
            mask_path=str(mask),
            output_format=output_format,
            output_path=_path(output_path),
            image_path=_path(image_path),
            save_flows=save_flows,
        )
    )


def main() -> None:
    """Run the Cellpose operations CLI."""
    app()


if __name__ == "__main__":
    main()
