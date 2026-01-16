"""MCP tools for Cellpose cell segmentation, restoration, and training."""

import os

# Fix OpenMP threading conflicts that can cause model.eval() to hang
# This must be set BEFORE importing cellpose or any libraries that use OpenMP
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path
from typing import Any

import imageio
import numpy as np
from cellpose import io, models
from cellpose.denoise import CellposeDenoiseModel, DenoiseModel

# Import the shared MCP instance
from cellpose_mcp.mcp_instance import mcp

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
    model_type: str = "cyto2",
    diameter: float = 0,
    channels: list[int] | None = None,
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    min_size: int = 15,
    gpu: bool = False,
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

    Returns:
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
                styles = None
            elif len(result) == 4:
                masks, flows, styles, diams = result
            else:
                raise ValueError(f"Unexpected number of return values: {len(result)}")
        else:
            masks = result
            flows = None
            styles = None
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
    model_type: str = "cyto2",
    diameter: float = 0,
    do_3d: bool = True,
    anisotropy: float | None = None,
    stitch_threshold: float = 0.0,
    flow3d_smooth: float = 0,
    channels: list[int] | None = None,
    gpu: bool = False,
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

    Returns:
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
                masks, flows, diams = result
            elif len(result) == 4:
                masks, flows, styles, diams = result
            else:
                raise ValueError(f"Unexpected number of return values: {len(result)}")
        else:
            masks = result
            flows = None
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
    model_type: str = "cyto2",
    diameter: float = 0,
    output_dir: str | None = None,
    gpu: bool = False,
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

    Returns:
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
                if isinstance(result, tuple):
                    masks = result[0]
                else:
                    masks = result

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
    gpu: bool = False,
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

    Returns:
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
    gpu: bool = False,
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

    Returns:
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
    gpu: bool = False,
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

    Returns:
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
    gpu: bool = False,
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

    Returns:
        Dictionary with combined restoration and segmentation results
    """
    try:
        img = io.imread(image_path)

        # Use CellposeDenoiseModel for combined pipeline
        model = CellposeDenoiseModel(
            gpu=gpu, pretrained_model=restoration_model, model_type=segmentation_model
        )

        # Run restoration + segmentation
        masks, flows, styles, diams, restored = model.eval(
            img, diameter=diameter, channels=channels, restore=True
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
    gpu: bool = False,
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

    Returns:
        Dictionary with training results
    """
    try:
        from cellpose import train

        # Load training data
        train_data, train_labels, _ = io.load_train_test_data(
            train_dir, train_labels_dir, image_filter="_img", mask_filter="_masks"
        )

        test_data = None
        test_labels = None
        if test_dir and test_labels_dir:
            test_data, test_labels, _ = io.load_train_test_data(
                test_dir, test_labels_dir, image_filter="_img", mask_filter="_masks"
            )

        # Initialize model
        # Note: Cellpose v4 defaults to 'cpsam' model. The model_type parameter
        # may show a warning but still works for compatibility with user expectations.
        model = models.CellposeModel(gpu=gpu, model_type=model_type)

        # Determine output directory
        if output_dir is None:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)

        # Train model
        train.train_seg(
            model.net,
            train_data,
            train_labels,
            test_data=test_data,
            test_labels=test_labels,
            channels=[0, 0],  # Default channels
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

    Returns:
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
    model_type: str = "cyto2",
    channels: list[int] | None = None,
) -> dict[str, Any]:
    """Estimate cell diameter from an image using Cellpose size model.

    Args:
        image_path: Path to input image
        model_type: Model type to use for estimation
        channels: Channel specification

    Returns:
        Dictionary with estimated diameter and confidence
    """
    try:
        img = io.imread(image_path)

        # Initialize model with size estimation
        model = models.CellposeModel(model_type=model_type)
        result = model.eval(img, channels=channels, diameter=None)

        # Handle Cellpose v4 API return values
        if isinstance(result, tuple):
            diams = result[-1]  # diams is always the last value
        else:
            diams = None

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
    save_outlines: bool = False,
    save_flows: bool = False,
) -> dict[str, Any]:
    """Save masks in various formats with optional outlines and flows.

    Args:
        mask_path: Path to existing mask file
        output_format: Output format (tif, png, npy)
        output_path: Optional custom output path
        save_outlines: Whether to save cell outlines
        save_flows: Whether to save flow fields

    Returns:
        Dictionary with output file paths
    """
    try:
        masks = io.imread(mask_path)

        mask_path_obj = Path(mask_path)
        if output_path is None:
            output_path = str(mask_path_obj.parent / f"{mask_path_obj.stem}_formatted.{output_format}")

        files_created = [output_path]

        # Save masks
        io.imsave(output_path, masks)

        # Save outlines if requested
        if save_outlines:
            from cellpose import utils

            outlines = utils.outlines_list(masks)
            outlines_path = output_path.replace(f".{output_format}", "_outlines.png")
            # Save outlines visualization
            files_created.append(outlines_path)

        return {
            "output_path": output_path,
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

    Returns:
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
segment_cells_2d = segment_cells_2d.fn

_segment_cells_3d_tool = segment_cells_3d
segment_cells_3d = segment_cells_3d.fn

_segment_cells_batch_tool = segment_cells_batch
segment_cells_batch = segment_cells_batch.fn

_denoise_image_tool = denoise_image
denoise_image = denoise_image.fn

_deblur_image_tool = deblur_image
deblur_image = deblur_image.fn

_upsample_image_tool = upsample_image
upsample_image = upsample_image.fn

_restore_and_segment_tool = restore_and_segment
restore_and_segment = restore_and_segment.fn

_train_segmentation_model_tool = train_segmentation_model
train_segmentation_model = train_segmentation_model.fn

_list_available_models_tool = list_available_models
list_available_models = list_available_models.fn

_estimate_cell_diameter_tool = estimate_cell_diameter
estimate_cell_diameter = estimate_cell_diameter.fn

_save_masks_tool = save_masks
save_masks = save_masks.fn

_load_image_info_tool = load_image_info
load_image_info = load_image_info.fn
