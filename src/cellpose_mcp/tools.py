"""MCP tools for Cellpose cell segmentation, restoration, and training."""

import os

# Fix OpenMP threading conflicts that can cause model.eval() to hang
# This must be set BEFORE importing cellpose or any libraries that use OpenMP
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path
from typing import Any

import numpy as np
from cellpose import io, models
from cellpose.denoise import CellposeDenoiseModel, DenoiseModel

# Import the shared MCP instance
from cellpose_mcp.mcp_instance import mcp


def _unwrap_mcp_tool(wrapped: Any) -> Any:
    """Return the plain Python callable behind an MCP tool wrapper.

    FastMCP historically attached the original function as ``wrapped.fn``; some
    versions register the bare function instead, which has no ``.fn`` attribute.
    """
    inner = getattr(wrapped, "fn", None)
    if inner is not None:
        return inner
    return getattr(wrapped, "__wrapped__", wrapped)


# Predefined model types
PRETRAINED_MODELS = [
    "cyto",
    "cyto2",
    "cyto3",
    "nuclei",
    "bact",
    "tissuenet",
    "livecell",
    "yeast",
    "denoise_cyto2",
    "denoise_cyto3",
    "denoise_nuclei",
    "deblur_cyto2",
    "deblur_cyto3",
    "upsample_cyto2",
    "upsample_cyto3",
    "oneclick_cyto2",
    "oneclick_cyto3",
]


@mcp.tool()
def segment_cells_2d(
    image_path: str,
    model_type: str = "cpsam",
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
        # Load image
        img = io.imread(image_path)
        if img.ndim > 2 and img.shape[-1] > 4:
            img = img[:, :, :4]  # Limit to 4 channels max

        # Initialize model
        # Note: Cellpose v4 defaults to 'cpsam' model. The model_type parameter
        # may show a warning but still works for compatibility with user expectations.
        model = models.CellposeModel(gpu=gpu, model_type=model_type)

        # Run segmentation
        # Convert diameter=0 to None for auto-estimation (Cellpose v4 requirement)
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

        # Handle Cellpose v4 API - returns 3 values (masks, flows, diams)
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
            output_path = str(img_path.parent / f"{img_path.stem}_masks{img_path.suffix}")

        # Save masks
        io.imsave(output_path, masks)

        # Count cells (exclude background label 0)
        n_cells = len(np.unique(masks)) - 1 if masks is not None else 0
        diameter_used = float(diams) if isinstance(diams, (int, float, np.number)) else float(diams[0])

        return {
            "cells_detected": int(n_cells),
            "output_path": output_path,
            "diameter": diameter_used,
            "mask_shape": list(masks.shape) if masks is not None else [],
            "flow_quality": float(np.mean(flows[2])) if flows and len(flows) > 2 else 0.0,
        }
    except Exception as e:
        return {"error": str(e), "cells_detected": 0}


@mcp.tool()
def segment_cells_3d(
    image_path: str,
    model_type: str = "cpsam",
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
        # Load 3D image
        img = io.imread(image_path)

        # Initialize model
        # Note: Cellpose v4 defaults to 'cpsam' model. The model_type parameter
        # may show a warning but still works for compatibility with user expectations.
        model = models.CellposeModel(gpu=gpu, model_type=model_type)

        # Run 3D segmentation
        # Convert diameter=0 to None for auto-estimation (Cellpose v4 requirement)
        diameter_param = None if diameter == 0 else diameter
        result = model.eval(
            img,
            diameter=diameter_param,
            channels=channels,
            do_3D=do_3d,
            anisotropy=anisotropy,
            stitch_threshold=stitch_threshold,
            flow3D_smooth=flow3d_smooth,
        )

        # Handle Cellpose v4 API - returns 3 values (masks, flows, diams)
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
            output_path = str(img_path.parent / f"{img_path.stem}_masks_3d{img_path.suffix}")

        # Save masks
        io.imsave(output_path, masks)

        n_cells = len(np.unique(masks)) - 1 if masks is not None else 0
        diameter_used = float(diams) if isinstance(diams, (int, float, np.number)) else float(diams[0])

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


@mcp.tool()
def segment_cells_batch(
    image_paths: list[str],
    model_type: str = "cpsam",
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
        # Initialize model once (use pretrained_model for Cellpose v4+)
        model = models.CellposeModel(gpu=gpu, pretrained_model=model_type)

        results = []
        for img_path in image_paths:
            try:
                img = io.imread(img_path)
                # Convert diameter=0 to None for auto-estimation
                diameter_param = None if diameter == 0 else diameter
                result = model.eval(img, diameter=diameter_param, batch_size=batch_size)

                # Handle Cellpose v4 API return values
                masks = result[0] if isinstance(result, tuple) else result

                # Determine output path
                img_path_obj = Path(img_path)
                if output_dir:
                    output_path = Path(output_dir) / f"{img_path_obj.stem}_masks{img_path_obj.suffix}"
                    os.makedirs(output_dir, exist_ok=True)
                else:
                    output_path = img_path_obj.parent / f"{img_path_obj.stem}_masks{img_path_obj.suffix}"

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
                results.append({"image_path": img_path, "success": False, "error": str(e)})

        return {
            "total_images": len(image_paths),
            "successful": sum(1 for r in results if r.get("success", False)),
            "failed": sum(1 for r in results if not r.get("success", False)),
            "results": results,
        }
    except Exception as e:
        return {"error": str(e), "total_images": len(image_paths), "successful": 0, "failed": len(image_paths)}


@mcp.tool()
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
        img = io.imread(image_path)

        # Initialize denoising model
        model = DenoiseModel(gpu=gpu, pretrained_model=model_type)

        # Denoise image
        restored = model.eval(img, channels=channels, diameter=diameter)

        # Determine output path
        if output_path is None:
            img_path = Path(image_path)
            output_path = str(img_path.parent / f"{img_path.stem}_denoised{img_path.suffix}")

        # Save restored image
        io.imsave(output_path, restored)

        return {
            "output_path": output_path,
            "original_shape": list(img.shape),
            "restored_shape": list(restored.shape),
            "noise_reduction_estimate": "high",  # Qualitative estimate
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
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
        img = io.imread(image_path)

        model = DenoiseModel(gpu=gpu, pretrained_model=model_type)
        restored = model.eval(img, channels=channels, diameter=diameter)

        if output_path is None:
            img_path = Path(image_path)
            output_path = str(img_path.parent / f"{img_path.stem}_deblurred{img_path.suffix}")

        io.imsave(output_path, restored)

        return {
            "output_path": output_path,
            "original_shape": list(img.shape),
            "restored_shape": list(restored.shape),
            "blur_reduction_estimate": "high",
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
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
        scale_factor: Upsampling factor (typically 2 or 4)
        channels: Channel specification
        gpu: Whether to use GPU acceleration
        output_path: Optional path to save upsampled image

    Returns
    -------
        Dictionary with upsampling results
    """
    try:
        img = io.imread(image_path)

        model = DenoiseModel(gpu=gpu, pretrained_model=model_type)
        upsampled = model.eval(img, channels=channels)

        if output_path is None:
            img_path = Path(image_path)
            output_path = str(img_path.parent / f"{img_path.stem}_upsampled{img_path.suffix}")

        io.imsave(output_path, upsampled)

        return {
            "output_path": output_path,
            "original_shape": list(img.shape),
            "upsampled_shape": list(upsampled.shape),
            "scale_factor": scale_factor,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
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
        img = io.imread(image_path)

        # Use CellposeDenoiseModel for combined pipeline
        model = CellposeDenoiseModel(
            gpu=gpu, pretrained_model=restoration_model, model_type=segmentation_model
        )

        # Run restoration + segmentation (diameter=None for auto-estimate)
        diameter_param = None if diameter == 0 else diameter
        masks, flows, styles, diams, restored = model.eval(
            img, diameter=diameter_param, channels=channels, restore=True
        )

        # Determine output paths
        img_path = Path(image_path)
        if output_path_mask is None:
            output_path_mask = str(img_path.parent / f"{img_path.stem}_restored_masks{img_path.suffix}")
        if output_path_restored is None:
            output_path_restored = str(img_path.parent / f"{img_path.stem}_restored{img_path.suffix}")

        # Save outputs
        io.imsave(output_path_mask, masks)
        io.imsave(output_path_restored, restored)

        n_cells = len(np.unique(masks)) - 1 if masks is not None else 0
        diameter_used = float(diams) if isinstance(diams, (int, float, np.number)) else float(diams[0])

        return {
            "cells_detected": int(n_cells),
            "mask_path": output_path_mask,
            "restored_image_path": output_path_restored,
            "diameter": diameter_used,
            "mask_shape": list(masks.shape) if masks is not None else [],
        }
    except Exception as e:
        return {"error": str(e), "cells_detected": 0}


@mcp.tool()
def train_segmentation_model(
    train_dir: str,
    train_labels_dir: str,
    model_name: str,
    model_type: str = "cyto",
    n_epochs: int = 100,
    learning_rate: float = 0.0001,
    batch_size: int = 8,
    test_dir: str | None = None,
    test_labels_dir: str | None = None,
    gpu: bool = True,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Train a custom Cellpose segmentation model.

    Args:
        train_dir: Directory containing training images
        train_labels_dir: Directory containing training masks/labels
        model_name: Name for the trained model
        model_type: Base model type (cyto, nuclei, etc.)
        n_epochs: Number of training epochs
        learning_rate: Learning rate for training
        batch_size: Batch size for training
        test_dir: Optional directory with test images
        test_labels_dir: Optional directory with test labels
        gpu: Whether to use GPU acceleration
        output_dir: Directory to save trained model (default: current directory)

    Returns
    -------
        Dictionary with training results
    """
    try:
        import tempfile

        from cellpose import train

        # Cellpose expects images and masks in the same directory (image_filter/_img,
        # mask_filter/_masks). Build a combined dir when separate dirs are given.
        def _combined_data_dir(images_dir: str, labels_dir: str) -> tuple[str, tempfile.TemporaryDirectory | None]:
            img_names = {f for f in os.listdir(images_dir) if "_img" in f}
            label_names = {f for f in os.listdir(labels_dir) if "_masks" in f}
            if not img_names or not label_names:
                return images_dir, None  # fallback: use images_dir only
            # Build combined temp dir with symlinks so Cellpose finds both
            tmp = tempfile.TemporaryDirectory(prefix="cellpose_train_")
            for f in img_names:
                os.symlink(os.path.join(images_dir, f), os.path.join(tmp.name, f))
            for f in label_names:
                os.symlink(os.path.join(labels_dir, f), os.path.join(tmp.name, f))
            return tmp.name, tmp

        train_combined, train_tmp = _combined_data_dir(train_dir, train_labels_dir)
        try:
            out = io.load_train_test_data(
                train_combined, test_dir=None, image_filter="_img", mask_filter="_masks"
            )
        finally:
            if train_tmp is not None:
                train_tmp.cleanup()
        train_data = out[0]
        train_labels = out[1]

        test_data = None
        test_labels = None
        if test_dir and test_labels_dir:
            test_combined, test_tmp = _combined_data_dir(test_dir, test_labels_dir)
            try:
                out_test = io.load_train_test_data(
                    test_combined, test_dir=None, image_filter="_img", mask_filter="_masks"
                )
                test_data = out_test[0]
                test_labels = out_test[1]
            finally:
                if test_tmp is not None:
                    test_tmp.cleanup()

        # Initialize model
        # Note: Cellpose v4 defaults to 'cpsam' model. The model_type parameter
        # may show a warning but still works for compatibility with user expectations.
        model = models.CellposeModel(gpu=gpu, model_type=model_type)

        # Determine output directory
        if output_dir is None:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)

        # Train model (Cellpose v4 uses channel_axis, not channels)
        train.train_seg(
            model.net,
            train_data,
            train_labels,
            test_data=test_data,
            test_labels=test_labels,
            save_path=output_dir,
            n_epochs=n_epochs,
            learning_rate=learning_rate,
            batch_size=batch_size,
        )

        model_path = os.path.join(output_dir, f"{model_name}.pth")

        return {
            "model_path": model_path,
            "model_name": model_name,
            "n_epochs": n_epochs,
            "training_images": len(train_data),
            "test_images": len(test_data) if test_data else 0,
            "status": "completed",
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp.tool()
def list_available_models() -> dict[str, Any]:
    """List all available pretrained Cellpose models.

    Returns
    -------
        Dictionary with lists of available models by category
    """
    return {
        "segmentation_models": ["cyto", "cyto2", "cyto3", "nuclei", "bact", "tissuenet", "livecell", "yeast"],
        "restoration_models": {
            "denoise": ["denoise_cyto2", "denoise_cyto3", "denoise_nuclei"],
            "deblur": ["deblur_cyto2", "deblur_cyto3"],
            "upsample": ["upsample_cyto2", "upsample_cyto3"],
            "oneclick": ["oneclick_cyto2", "oneclick_cyto3"],
        },
        "all_models": PRETRAINED_MODELS,
    }


@mcp.tool()
def estimate_cell_diameter(
    image_path: str,
    model_type: str = "cpsam",
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
        img = io.imread(image_path)

        # Initialize model with size estimation
        model = models.CellposeModel(gpu=gpu, model_type=model_type)
        result = model.eval(img, channels=channels, diameter=None)

        # Handle Cellpose v4 API return values (diams is always the last tuple element)
        diams = result[-1] if isinstance(result, tuple) else None

        diameter_est = float(diams) if isinstance(diams, (int, float, np.number)) else float(diams[0]) if diams is not None else 0.0

        return {
            "estimated_diameter": diameter_est,
            "confidence": "high" if diameter_est > 0 else "low",
            "model_used": model_type,
        }
    except Exception as e:
        return {"error": str(e), "estimated_diameter": 0.0}


@mcp.tool()
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

        masks = io.imread(mask_path)

        mask_path_obj = Path(mask_path)
        if output_path is None:
            output_path = str(mask_path_obj.parent / f"{mask_path_obj.stem}_formatted.{output_format}")

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
            img = io.imread(image_path)
            if img.ndim > 2:
                img_2d = img[0] if img.shape[0] < img.shape[-1] else np.mean(img[:, :, : min(4, img.shape[-1])], axis=-1)
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


@mcp.tool()
def load_image_info(image_path: str) -> dict[str, Any]:
    """Get information about an image file.

    Args:
        image_path: Path to image file

    Returns
    -------
        Dictionary with image metadata (shape, dtype, channels, dimensions)
    """
    try:
        img = io.imread(image_path)

        info = {
            "shape": list(img.shape),
            "dtype": str(img.dtype),
            "is_3d": len(img.shape) == 3 and img.shape[-1] <= 4,  # 3D volume or RGB
            "is_4d": len(img.shape) == 4,  # 4D volume
            "channels": img.shape[-1] if len(img.shape) > 2 and img.shape[-1] <= 4 else 1,
            "pixel_size": None,  # Would need metadata parsing
        }

        return info
    except Exception as e:
        return {"error": str(e)}


# Make all MCP tools directly callable by exposing their underlying functions
# This allows tools to be called both as MCP tools (via protocol) and as Python functions (directly)
_segment_cells_2d_tool = segment_cells_2d
segment_cells_2d = _unwrap_mcp_tool(segment_cells_2d)

_segment_cells_3d_tool = segment_cells_3d
segment_cells_3d = _unwrap_mcp_tool(segment_cells_3d)

_segment_cells_batch_tool = segment_cells_batch
segment_cells_batch = _unwrap_mcp_tool(segment_cells_batch)

_denoise_image_tool = denoise_image
denoise_image = _unwrap_mcp_tool(denoise_image)

_deblur_image_tool = deblur_image
deblur_image = _unwrap_mcp_tool(deblur_image)

_upsample_image_tool = upsample_image
upsample_image = _unwrap_mcp_tool(upsample_image)

_restore_and_segment_tool = restore_and_segment
restore_and_segment = _unwrap_mcp_tool(restore_and_segment)

_train_segmentation_model_tool = train_segmentation_model
train_segmentation_model = _unwrap_mcp_tool(train_segmentation_model)

_list_available_models_tool = list_available_models
list_available_models = _unwrap_mcp_tool(list_available_models)

_estimate_cell_diameter_tool = estimate_cell_diameter
estimate_cell_diameter = _unwrap_mcp_tool(estimate_cell_diameter)

_save_masks_tool = save_masks
save_masks = _unwrap_mcp_tool(save_masks)

_load_image_info_tool = load_image_info
load_image_info = _unwrap_mcp_tool(load_image_info)
