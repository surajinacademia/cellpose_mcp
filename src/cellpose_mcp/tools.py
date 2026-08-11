"""MCP adapters for Cellpose operations."""

from typing import Any

from cellpose_mcp import operations as _operations
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


PRETRAINED_MODELS = _operations.PRETRAINED_MODELS

_segment_cells_2d_tool = mcp.tool()(_operations.segment_cells_2d)
segment_cells_2d = _unwrap_mcp_tool(_segment_cells_2d_tool)

_segment_cells_3d_tool = mcp.tool()(_operations.segment_cells_3d)
segment_cells_3d = _unwrap_mcp_tool(_segment_cells_3d_tool)

_segment_cells_batch_tool = mcp.tool()(_operations.segment_cells_batch)
segment_cells_batch = _unwrap_mcp_tool(_segment_cells_batch_tool)

_denoise_image_tool = mcp.tool()(_operations.denoise_image)
denoise_image = _unwrap_mcp_tool(_denoise_image_tool)

_deblur_image_tool = mcp.tool()(_operations.deblur_image)
deblur_image = _unwrap_mcp_tool(_deblur_image_tool)

_upsample_image_tool = mcp.tool()(_operations.upsample_image)
upsample_image = _unwrap_mcp_tool(_upsample_image_tool)

_restore_and_segment_tool = mcp.tool()(_operations.restore_and_segment)
restore_and_segment = _unwrap_mcp_tool(_restore_and_segment_tool)

_list_available_models_tool = mcp.tool()(_operations.list_available_models)
list_available_models = _unwrap_mcp_tool(_list_available_models_tool)

_estimate_cell_diameter_tool = mcp.tool()(_operations.estimate_cell_diameter)
estimate_cell_diameter = _unwrap_mcp_tool(_estimate_cell_diameter_tool)

_save_masks_tool = mcp.tool()(_operations.save_masks)
save_masks = _unwrap_mcp_tool(_save_masks_tool)

_load_image_info_tool = mcp.tool()(_operations.load_image_info)
load_image_info = _unwrap_mcp_tool(_load_image_info_tool)

__all__ = [
    "PRETRAINED_MODELS",
    "segment_cells_2d",
    "segment_cells_3d",
    "segment_cells_batch",
    "denoise_image",
    "deblur_image",
    "upsample_image",
    "restore_and_segment",
    "list_available_models",
    "estimate_cell_diameter",
    "save_masks",
    "load_image_info",
]
