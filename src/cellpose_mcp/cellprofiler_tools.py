"""MCP tools for CellProfiler integration."""

import os

# Fix OpenMP threading conflicts
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from typing import Any

from cellpose_mcp.cellprofiler_integration import CellProfilerIntegration
from cellpose_mcp.mcp_instance import mcp


@mcp.tool()
def run_cellprofiler_pipeline(
    pipeline_file: str,
    input_dir: str,
    output_dir: str,
    plugins_dir: str | None = None,
) -> dict[str, Any]:
    """Run a CellProfiler pipeline for advanced image analysis.

    This tool enables integration with CellProfiler for feature extraction,
    measurements, and advanced analysis workflows beyond basic segmentation.

    Args:
        pipeline_file: Path to CellProfiler pipeline file (.cppipe)
        input_dir: Directory containing input images
        output_dir: Directory to save output files and measurements
        plugins_dir: Optional directory containing CellProfiler plugins

    Returns:
        Dictionary with execution results including success status and output location
    """
    try:
        cp_integration = CellProfilerIntegration()
        result = cp_integration.run_pipeline(
            pipeline_file, input_dir, output_dir, plugins_dir
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def import_cellpose_to_cellprofiler(
    mask_dir: str,
    cellprofiler_project: str | None = None,
) -> dict[str, Any]:
    """Import Cellpose segmentation masks into CellProfiler format.

    This tool bridges Cellpose segmentation with CellProfiler's measurement
    and analysis capabilities.

    Args:
        mask_dir: Directory containing Cellpose-generated masks
        cellprofiler_project: Optional CellProfiler project to import into

    Returns:
        Dictionary with import results and compatible mask information
    """
    try:
        cp_integration = CellProfilerIntegration()
        result = cp_integration.import_cellpose_masks(mask_dir, cellprofiler_project)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def export_cellprofiler_measurements(
    output_dir: str,
    format: str = "csv",
) -> dict[str, Any]:
    """Export CellProfiler measurements in specified format.

    This tool retrieves and organizes CellProfiler measurement outputs.

    Args:
        output_dir: Directory containing CellProfiler output
        format: Export format - 'csv', 'excel', or 'database'

    Returns:
        Dictionary with measurement file locations and count
    """
    try:
        cp_integration = CellProfilerIntegration()
        result = cp_integration.export_measurements(output_dir, format)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def check_cellprofiler_available() -> dict[str, Any]:
    """Check if CellProfiler is installed and available.

    Returns:
        Dictionary with availability status and version information
    """
    try:
        cp_integration = CellProfilerIntegration()
        return {
            "available": cp_integration.cellprofiler_available,
            "note": "CellProfiler must be installed separately: pip install cellprofiler",
        }
    except Exception as e:
        return {"available": False, "error": str(e)}
