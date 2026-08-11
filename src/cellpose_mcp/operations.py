"""Core Cellpose operations for segmentation and restoration."""

import os
import ssl
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

# Fix OpenMP threading conflicts that can cause model.eval() to hang
# This must be set BEFORE importing cellpose or any libraries that use OpenMP
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
from cellpose import io, models
from cellpose import utils as cellpose_utils
from cellpose.denoise import CellposeDenoiseModel, DenoiseModel

# Pretrained model types supported by the pinned Cellpose release.
SEGMENTATION_MODELS = [
    "cyto3",
    "nuclei",
    "cyto2",
    "cyto",
    "tissuenet_cp3",
    "livecell_cp3",
    "yeast_PhC_cp3",
    "yeast_BF_cp3",
    "bact_phase_cp3",
    "bact_fluor_cp3",
    "deepbacs_cp3",
]
RESTORATION_MODELS = {
    "denoise": ["denoise_cyto3", "denoise_cyto2", "denoise_nuclei"],
    "deblur": ["deblur_cyto3", "deblur_cyto2", "deblur_nuclei"],
    "upsample": ["upsample_cyto3", "upsample_cyto2", "upsample_nuclei"],
    "oneclick": ["oneclick_cyto3", "oneclick_cyto2", "oneclick_nuclei"],
}
PRETRAINED_MODELS = SEGMENTATION_MODELS + [
    model for category in RESTORATION_MODELS.values() for model in category
]
DIAMETER_MODELS = ["cyto3", "nuclei", "cyto2", "cyto"]
MAX_MODEL_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024
MODEL_DOWNLOAD_CHUNK_BYTES = 1024 * 1024


def _validate_image_path(path: str) -> None:
    """Reject formats that Cellpose opens with pickle enabled."""
    if Path(path).suffix.lower() == ".npy":
        raise ValueError(
            ".npy inputs are disabled because Cellpose loads them with pickle enabled"
        )


def _read_image(path: str) -> np.ndarray:
    """Read an image after enforcing this package's input policy."""
    _validate_image_path(path)
    return np.asarray(io.imread(path))


def _require_model(model: str, allowed: list[str], kind: str) -> None:
    """Keep model arguments as curated identifiers, not filesystem paths."""
    if model not in allowed:
        choices = ", ".join(allowed)
        raise ValueError(
            f"unsupported {kind} model {model!r}; choose one of: {choices}"
        )


def _validate_model_download_url(url: str) -> None:
    """Require the exact HTTPS origin used for official Cellpose models."""
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.cellpose.org"
        or parsed.port not in (None, 443)
        or not parsed.path.startswith("/models/")
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("model download must use the approved Cellpose HTTPS host")


def _secure_model_download(url: str, dst: str, progress: bool = True) -> None:
    """Download a Cellpose model over verified HTTPS with a size bound."""
    del progress
    _validate_model_download_url(url)
    destination = Path(dst)
    destination.parent.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context()
    temp_fd, temp_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    try:
        # S310 is satisfied by exact scheme/host checks before and after redirects.
        with urlopen(url, context=context, timeout=60) as response:  # noqa: S310
            final_url = getattr(response, "geturl", lambda: url)()
            _validate_model_download_url(final_url)
            content_length = response.headers.get("Content-Length")
            if (
                content_length is not None
                and int(content_length) > MAX_MODEL_DOWNLOAD_BYTES
            ):
                raise ValueError("Cellpose model download exceeds the size limit")

            downloaded = 0
            with os.fdopen(temp_fd, "wb") as output:
                temp_fd = -1
                while chunk := response.read(MODEL_DOWNLOAD_CHUNK_BYTES):
                    downloaded += len(chunk)
                    if downloaded > MAX_MODEL_DOWNLOAD_BYTES:
                        raise ValueError(
                            "Cellpose model download exceeds the size limit"
                        )
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
        os.replace(temp_name, destination)
    finally:
        if temp_fd >= 0:
            os.close(temp_fd)
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


# Cellpose's bundled helper disables TLS verification process-wide. All model
# constructors resolve this module attribute at call time, so replace it once.
cellpose_utils.download_url_to_file = _secure_model_download


def _scalar_or_none(value: Any) -> float | None:
    """Return the first finite positive scalar in a Cellpose value."""
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=float).ravel()
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    scalar = float(arr[0])
    if np.isfinite(scalar) and scalar > 0:
        return scalar
    return None


def _reported_diameter(requested: float, returned: Any) -> float:
    """Prefer the explicit user diameter over unreliable model metadata."""
    if requested and requested > 0:
        return float(requested)
    return _scalar_or_none(returned) or 0.0


def _is_channel_last_image(img: np.ndarray) -> bool:
    """Return True for 2D images with RGB/RGBA-style trailing channels."""
    return img.ndim == 3 and img.shape[-1] in (3, 4)


def _z_axis_for_volume(img: np.ndarray) -> int | None:
    """Infer a conservative Z axis for ZYX or ZYXC volumes."""
    if img.ndim == 3 and not _is_channel_last_image(img):
        return 0
    if img.ndim == 4:
        return 0
    return None


def _restoration_error(exc: Exception) -> dict[str, Any]:
    """Normalize known Cellpose restoration dependency errors."""
    message = str(exc)
    if isinstance(exc, NameError) and "CPnet" in message:
        return {
            "error": (
                "Cellpose restoration is unavailable with this installed Cellpose "
                "version. Install a Cellpose release with restoration support or "
                "use segmentation-only tools."
            )
        }
    return {"error": message}


def _denoise_model(model_type: str, gpu: bool) -> DenoiseModel:
    """Create a restoration model across Cellpose v3/v4 constructor variants."""
    try:
        return DenoiseModel(gpu=gpu, model_type=model_type)
    except TypeError:
        return DenoiseModel(gpu=gpu, pretrained_model=model_type)


def segment_cells_2d(
    image_path: str,
    model_type: str = "cyto3",
    diameter: float = 0,
    channels: list[int] | None = None,
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    min_size: int = 15,
    gpu: bool = True,
    augment: bool = False,
    normalize: bool = True,
    invert: bool = False,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Segment cells in a 2D microscopy image using Cellpose.

    Args:
        image_path: Path to input image file (TIFF, PNG, etc.)
        model_type: Cellpose model type (cyto, cyto2, cyto3, nuclei, etc.)
        diameter: Expected cell diameter in pixels (0 = auto-estimate)
        channels: Channel specification [cyto, nuclei] or None for grayscale
        flow_threshold: Flow error threshold (lower = more masks, may be worse quality)
        cellprob_threshold: Cell probability threshold (higher = fewer masks)
        min_size: Minimum cell size in pixels
        gpu: Whether to use GPU acceleration
        augment: Use test-time augmentation (flip/rotate)
        normalize: Normalize image intensities
        invert: Invert image intensities (for bright background)
        output_path: Optional path to save masks (default: image_path with _masks suffix)

    Returns
    -------
        Dictionary with segmentation results including cells_detected, output_path, diameter, mask_shape
    """
    try:
        _require_model(model_type, SEGMENTATION_MODELS, "segmentation")
        img = _read_image(image_path)
        if img.ndim > 2 and img.shape[-1] > 4:
            img = img[:, :, :4]  # Limit to 4 channels max

        # Initialize model
        model = models.CellposeModel(gpu=gpu, model_type=model_type)

        # Run segmentation
        # Convert diameter=0 to None for auto-estimation.
        diameter_param = None if diameter == 0 else diameter
        result = model.eval(
            img,
            diameter=diameter_param,
            channels=channels,
            flow_threshold=flow_threshold,
            cellprob_threshold=cellprob_threshold,
            min_size=min_size,
            augment=augment,
            normalize=normalize,
            invert=invert,
        )

        # Cellpose releases return either three or four values.
        if isinstance(result, tuple):
            if len(result) == 3:
                masks, flows, diams = result
            elif len(result) == 4:
                masks, flows, _, diams = result
            else:
                raise ValueError(f"Unexpected number of return values: {len(result)}")
        else:
            masks = result
            flows = None
            diams = None

        # Determine output path
        if output_path is None:
            img_path = Path(image_path)
            output_path = str(
                img_path.parent / f"{img_path.stem}_masks{img_path.suffix}"
            )

        # Save masks
        io.imsave(output_path, masks)

        # Count cells (exclude background label 0)
        n_cells = len(np.unique(masks)) - 1 if masks is not None else 0
        diameter_used = _reported_diameter(diameter, diams)

        return {
            "cells_detected": int(n_cells),
            "output_path": output_path,
            "diameter": diameter_used,
            "mask_shape": list(masks.shape) if masks is not None else [],
            "flow_quality": float(np.mean(flows[2]))
            if flows and len(flows) > 2
            else 0.0,
        }
    except Exception as e:
        return {"error": str(e), "cells_detected": 0}


def segment_cells_3d(
    image_path: str,
    model_type: str = "cyto3",
    diameter: float = 0,
    do_3d: bool = True,
    anisotropy: float | None = None,
    stitch_threshold: float = 0.0,
    flow3d_smooth: float = 0,
    channels: list[int] | None = None,
    gpu: bool = True,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Segment cells in a 3D volume using Cellpose.

    Args:
        image_path: Path to input 3D image stack (TIFF, etc.)
        model_type: Cellpose model type
        diameter: Expected cell diameter in pixels
        do_3d: Use full 3D segmentation (True) or slice + stitch (False)
        anisotropy: Z-axis anisotropy factor (z_pixel_size / xy_pixel_size)
        stitch_threshold: Threshold for stitching masks across slices (if do_3d=False)
        flow3d_smooth: Smoothing factor for 3D flows
        channels: Channel specification [cyto, nuclei] or None
        gpu: Whether to use GPU acceleration
        output_path: Optional path to save masks

    Returns
    -------
        Dictionary with 3D segmentation results
    """
    try:
        _require_model(model_type, SEGMENTATION_MODELS, "segmentation")
        img = _read_image(image_path)

        # Initialize model
        model = models.CellposeModel(gpu=gpu, model_type=model_type)

        # Keep full 3D and stitched volumes at native size to avoid mask resizing.
        diameter_param = (
            None if diameter == 0 or do_3d or stitch_threshold > 0 else diameter
        )
        z_axis = _z_axis_for_volume(img)
        result = model.eval(
            img,
            diameter=diameter_param,
            channels=channels,
            z_axis=z_axis,
            do_3D=do_3d,
            anisotropy=anisotropy,
            stitch_threshold=stitch_threshold,
            flow3D_smooth=flow3d_smooth,
        )

        # Cellpose releases return either three or four values.
        if isinstance(result, tuple):
            if len(result) == 3:
                masks, _, diams = result
            elif len(result) == 4:
                masks, _, _, diams = result
            else:
                raise ValueError(f"Unexpected number of return values: {len(result)}")
        else:
            masks = result
            diams = None

        # Determine output path
        if output_path is None:
            img_path = Path(image_path)
            output_path = str(
                img_path.parent / f"{img_path.stem}_masks_3d{img_path.suffix}"
            )

        # Save masks
        io.imsave(output_path, masks)

        n_cells = len(np.unique(masks)) - 1 if masks is not None else 0
        diameter_used = _reported_diameter(diameter, diams)

        return {
            "cells_detected": int(n_cells),
            "output_path": output_path,
            "diameter": diameter_used,
            "volume_shape": list(masks.shape) if masks is not None else [],
            "anisotropy_used": float(anisotropy) if anisotropy else None,
            "method": "full_3d" if do_3d else "slice_stitch",
        }
    except Exception as e:
        return {"error": str(e), "cells_detected": 0}


def segment_cells_batch(
    image_paths: list[str],
    model_type: str = "cyto3",
    diameter: float = 0,
    output_dir: str | None = None,
    gpu: bool = True,
    batch_size: int = 8,
) -> dict[str, Any]:
    """Segment cells in multiple images in batch.

    Args:
        image_paths: List of paths to input images
        model_type: Cellpose model type
        diameter: Expected cell diameter in pixels
        output_dir: Directory to save masks (default: same as input images)
        gpu: Whether to use GPU acceleration
        batch_size: Number of images to process in parallel

    Returns
    -------
        Dictionary with batch processing results
    """
    try:
        _require_model(model_type, SEGMENTATION_MODELS, "segmentation")
        for img_path in image_paths:
            _validate_image_path(img_path)

        # Initialize one model for the whole batch.
        model = models.CellposeModel(gpu=gpu, pretrained_model=model_type)

        results = []
        for img_path in image_paths:
            try:
                img = _read_image(img_path)
                # Convert diameter=0 to None for auto-estimation
                diameter_param = None if diameter == 0 else diameter
                result = model.eval(img, diameter=diameter_param, batch_size=batch_size)

                # The first return value is always the mask array.
                masks = result[0] if isinstance(result, tuple) else result

                # Determine output path
                img_path_obj = Path(img_path)
                if output_dir:
                    output_path = (
                        Path(output_dir)
                        / f"{img_path_obj.stem}_masks{img_path_obj.suffix}"
                    )
                    os.makedirs(output_dir, exist_ok=True)
                else:
                    output_path = (
                        img_path_obj.parent
                        / f"{img_path_obj.stem}_masks{img_path_obj.suffix}"
                    )

                io.imsave(str(output_path), masks)
                n_cells = len(np.unique(masks)) - 1 if masks is not None else 0

                results.append(
                    {
                        "image_path": img_path,
                        "cells_detected": int(n_cells),
                        "output_path": str(output_path),
                        "success": True,
                    }
                )
            except Exception as e:
                results.append(
                    {"image_path": img_path, "success": False, "error": str(e)}
                )

        return {
            "total_images": len(image_paths),
            "successful": sum(1 for r in results if r.get("success", False)),
            "failed": sum(1 for r in results if not r.get("success", False)),
            "results": results,
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_images": len(image_paths),
            "successful": 0,
            "failed": len(image_paths),
        }


def denoise_image(
    image_path: str,
    model_type: str = "denoise_cyto3",
    channels: list[int] | None = None,
    diameter: float = 30.0,
    gpu: bool = True,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Denoise a microscopy image using Cellpose restoration models.

    Args:
        image_path: Path to input image
        model_type: Restoration model type (denoise_cyto2, denoise_cyto3, etc.)
        channels: Channel specification
        diameter: Expected object diameter for scaling
        gpu: Whether to use GPU acceleration
        output_path: Optional path to save denoised image

    Returns
    -------
        Dictionary with denoising results
    """
    try:
        _require_model(model_type, RESTORATION_MODELS["denoise"], "denoise")
        img = _read_image(image_path)

        # Initialize denoising model
        model = _denoise_model(model_type, gpu)

        # Denoise image
        restored = model.eval(img, channels=channels, diameter=diameter)

        # Determine output path
        if output_path is None:
            img_path = Path(image_path)
            output_path = str(
                img_path.parent / f"{img_path.stem}_denoised{img_path.suffix}"
            )

        # Save restored image
        io.imsave(output_path, restored)

        return {
            "output_path": output_path,
            "original_shape": list(img.shape),
            "restored_shape": list(restored.shape),
            "noise_reduction_estimate": "high",  # Qualitative estimate
        }
    except Exception as e:
        return _restoration_error(e)


def deblur_image(
    image_path: str,
    model_type: str = "deblur_cyto3",
    channels: list[int] | None = None,
    diameter: float = 30.0,
    gpu: bool = True,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Deblur a microscopy image using Cellpose restoration models.

    Args:
        image_path: Path to input image
        model_type: Restoration model type (deblur_cyto2, deblur_cyto3, etc.)
        channels: Channel specification
        diameter: Expected object diameter for scaling
        gpu: Whether to use GPU acceleration
        output_path: Optional path to save deblurred image

    Returns
    -------
        Dictionary with deblurring results
    """
    try:
        _require_model(model_type, RESTORATION_MODELS["deblur"], "deblur")
        img = _read_image(image_path)

        model = _denoise_model(model_type, gpu)
        restored = model.eval(img, channels=channels, diameter=diameter)

        if output_path is None:
            img_path = Path(image_path)
            output_path = str(
                img_path.parent / f"{img_path.stem}_deblurred{img_path.suffix}"
            )

        io.imsave(output_path, restored)

        return {
            "output_path": output_path,
            "original_shape": list(img.shape),
            "restored_shape": list(restored.shape),
            "blur_reduction_estimate": "high",
        }
    except Exception as e:
        return _restoration_error(e)


def upsample_image(
    image_path: str,
    model_type: str = "upsample_cyto3",
    scale_factor: int = 2,
    channels: list[int] | None = None,
    gpu: bool = True,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Upsample a microscopy image using Cellpose restoration models.

    Args:
        image_path: Path to input image
        model_type: Upsampling model type (upsample_cyto2, upsample_cyto3, etc.)
        scale_factor: Requested upsampling factor (typically 2 or 4)
        channels: Channel specification
        gpu: Whether to use GPU acceleration
        output_path: Optional path to save upsampled image

    Returns
    -------
        Dictionary with upsampling results
    """
    if scale_factor < 1:
        return {"error": "scale_factor must be at least 1"}

    try:
        _require_model(model_type, RESTORATION_MODELS["upsample"], "upsample")
        img = _read_image(image_path)

        model = _denoise_model(model_type, gpu)
        source_diameter = model.diam_mean / scale_factor
        upsampled = model.eval(
            img,
            channels=channels,
            diameter=source_diameter,
        )

        if output_path is None:
            img_path = Path(image_path)
            output_path = str(
                img_path.parent / f"{img_path.stem}_upsampled{img_path.suffix}"
            )

        io.imsave(output_path, upsampled)

        return {
            "output_path": output_path,
            "original_shape": list(img.shape),
            "upsampled_shape": list(upsampled.shape),
            "scale_factor": scale_factor,
        }
    except Exception as e:
        return _restoration_error(e)


def restore_and_segment(
    image_path: str,
    restoration_model: str = "oneclick_cyto3",
    segmentation_model: str = "cyto3",
    diameter: float = 0,
    channels: list[int] | None = None,
    gpu: bool = True,
    output_path_mask: str | None = None,
    output_path_restored: str | None = None,
) -> dict[str, Any]:
    """Restore (denoise/deblur) and segment an image in one pipeline.

    Args:
        image_path: Path to input image
        restoration_model: Restoration model type (oneclick_cyto3, etc.)
        segmentation_model: Segmentation model type (cyto3, etc.)
        diameter: Expected cell diameter in pixels
        channels: Channel specification
        gpu: Whether to use GPU acceleration
        output_path_mask: Optional path to save masks
        output_path_restored: Optional path to save restored image

    Returns
    -------
        Dictionary with combined restoration and segmentation results
    """
    try:
        _require_model(restoration_model, RESTORATION_MODELS["oneclick"], "oneclick")
        _require_model(segmentation_model, SEGMENTATION_MODELS, "segmentation")
        img = _read_image(image_path)

        # Use CellposeDenoiseModel for combined pipeline
        model = CellposeDenoiseModel(
            gpu=gpu,
            restore_type=restoration_model,
            model_type=segmentation_model,
        )

        # Run restoration + segmentation (diameter=None for auto-estimate)
        diameter_param = None if diameter == 0 else diameter
        result = model.eval(img, diameter=diameter_param, channels=channels)
        if isinstance(result, tuple) and len(result) == 5:
            masks, _, _, diams, restored = result
        elif isinstance(result, tuple) and len(result) == 4:
            masks, _, _, restored = result
            diams = None
        else:
            raise ValueError("Unexpected Cellpose restoration return value")

        # Determine output paths
        img_path = Path(image_path)
        if output_path_mask is None:
            output_path_mask = str(
                img_path.parent / f"{img_path.stem}_restored_masks{img_path.suffix}"
            )
        if output_path_restored is None:
            output_path_restored = str(
                img_path.parent / f"{img_path.stem}_restored{img_path.suffix}"
            )

        # Save outputs
        io.imsave(output_path_mask, masks)
        io.imsave(output_path_restored, restored)

        n_cells = len(np.unique(masks)) - 1 if masks is not None else 0
        diameter_used = _reported_diameter(diameter, diams)

        return {
            "cells_detected": int(n_cells),
            "mask_path": output_path_mask,
            "restored_image_path": output_path_restored,
            "diameter": diameter_used,
            "mask_shape": list(masks.shape) if masks is not None else [],
        }
    except Exception as e:
        error = _restoration_error(e)
        error["cells_detected"] = 0
        return error


def list_available_models() -> dict[str, Any]:
    """List all available pretrained Cellpose models.

    Returns
    -------
        Dictionary with lists of available models by category
    """
    return {
        "segmentation_models": list(SEGMENTATION_MODELS),
        "restoration_models": {
            category: list(model_names)
            for category, model_names in RESTORATION_MODELS.items()
        },
        "all_models": list(PRETRAINED_MODELS),
    }


def estimate_cell_diameter(
    image_path: str,
    model_type: str = "cyto3",
    channels: list[int] | None = None,
    gpu: bool = True,
) -> dict[str, Any]:
    """Estimate cell diameter from an image using Cellpose size model.

    Args:
        image_path: Path to input image
        model_type: Model type to use for estimation
        channels: Channel specification
        gpu: Whether to use GPU acceleration

    Returns
    -------
        Dictionary with estimated diameter and confidence
    """
    try:
        _require_model(model_type, DIAMETER_MODELS, "diameter-estimation")
        img = _read_image(image_path)

        # Cellpose owns the pretrained SizeModel; CellposeModel does not.
        model = models.Cellpose(gpu=gpu, model_type=model_type)
        result = model.eval(img, channels=channels, diameter=None)

        # The reported diameter is the last tuple element.
        diams = result[-1] if isinstance(result, tuple) else None
        diameter_est = _scalar_or_none(diams) or 0.0

        return {
            "estimated_diameter": diameter_est,
            "confidence": "high" if diameter_est > 0 else "low",
            "model_used": model_type,
        }
    except Exception as e:
        return {"error": str(e), "estimated_diameter": 0.0}


def save_masks(
    mask_path: str,
    output_format: str = "tif",
    output_path: str | None = None,
    image_path: str | None = None,
    save_flows: bool = False,
) -> dict[str, Any]:
    """Save masks plus outlines and overlay visualizations.

    Always writes three outputs: (1) masks in the chosen format,
    (2) outlines as a binary PNG, (3) overlay PNG (colored masks on image or black).

    Args:
        mask_path: Path to existing mask file
        output_format: Output format for masks (tif, png, npy)
        output_path: Optional custom output path for the masks file
        image_path: Optional path to original image; if provided, overlay is drawn on it
        save_flows: Reserved for future use (flow fields not saved)

    Returns
    -------
        Dictionary with mask_path, outlines_path, overlay_path, and files_created
    """
    try:
        from cellpose import plot, utils

        masks = _read_image(mask_path)

        mask_path_obj = Path(mask_path)
        if output_path is None:
            output_path = str(
                mask_path_obj.parent / f"{mask_path_obj.stem}_formatted.{output_format}"
            )

        base = output_path.replace(f".{output_format}", "")
        outlines_path = f"{base}_outlines.png"
        overlay_path = f"{base}_overlay.png"

        files_created = [output_path]

        # 2D views for outlines and overlay (use first slice if 3D)
        if masks.ndim > 2:
            masks_2d = masks[0] if masks.shape[0] < masks.shape[-1] else masks[:, :, 0]
        else:
            masks_2d = masks

        h, w = masks_2d.shape[:2]

        # 1. Save masks
        io.imsave(output_path, masks)

        # 2. Save outlines (binary PNG of outline pixels)
        outlines = utils.outlines_list(masks_2d)
        out_img = np.zeros((h, w), dtype=np.uint8)
        for o in outlines:
            if o is None or len(o) == 0:
                continue
            rr = np.clip(o[:, 1].astype(np.int32), 0, h - 1)
            cc = np.clip(o[:, 0].astype(np.int32), 0, w - 1)
            out_img[rr, cc] = 255
        io.imsave(outlines_path, out_img)
        files_created.append(outlines_path)

        # 3. Save overlay (colored mask on image or black)
        if image_path is not None:
            img = _read_image(image_path)
            if img.ndim > 2:
                img_2d = (
                    img[0]
                    if img.shape[0] < img.shape[-1]
                    else np.mean(img[:, :, : min(4, img.shape[-1])], axis=-1)
                )
            else:
                img_2d = np.asarray(img, dtype=np.float32)
            ih, iw = img_2d.shape[:2]
            if (ih, iw) != (h, w):
                canvas = np.zeros((h, w), dtype=np.float32)
                ph, pw = min(h, ih), min(w, iw)
                canvas[:ph, :pw] = img_2d[:ph, :pw]
                img_2d = canvas
            else:
                img_2d = img_2d.astype(np.float32)
        else:
            img_2d = np.zeros((h, w), dtype=np.float32)
        if np.issubdtype(img_2d.dtype, np.integer):
            img_2d = img_2d.astype(np.float32) / max(float(np.max(img_2d)), 1.0)
        overlay_rgb = plot.mask_overlay(img_2d, masks_2d)
        if overlay_rgb.max() <= 1.0:
            overlay_uint8 = (np.clip(overlay_rgb, 0, 1) * 255).astype(np.uint8)
        else:
            overlay_uint8 = np.clip(overlay_rgb, 0, 255).astype(np.uint8)
        io.imsave(overlay_path, overlay_uint8)
        files_created.append(overlay_path)

        return {
            "output_path": output_path,
            "outlines_path": outlines_path,
            "overlay_path": overlay_path,
            "files_created": files_created,
            "format": output_format,
        }
    except Exception as e:
        return {"error": str(e)}


def load_image_info(image_path: str) -> dict[str, Any]:
    """Get information about an image file.

    Args:
        image_path: Path to image file

    Returns
    -------
        Dictionary with image metadata (shape, dtype, channels, dimensions)
    """
    try:
        img = _read_image(image_path)

        info = {
            "shape": list(img.shape),
            "dtype": str(img.dtype),
            "is_3d": len(img.shape) == 3 and not _is_channel_last_image(img),
            "is_4d": len(img.shape) == 4,  # 4D volume
            "channels": img.shape[-1] if _is_channel_last_image(img) else 1,
            "pixel_size": None,  # Would need metadata parsing
        }

        return info
    except Exception as e:
        return {"error": str(e)}
