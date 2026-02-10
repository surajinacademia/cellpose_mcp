"""MCP tools for pipeline skills, verification, and memory management."""

import os

# Fix OpenMP threading conflicts
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from typing import Any

from cellpose_mcp.mcp_instance import mcp
from cellpose_mcp.skills import PipelineMemory, PipelineSummary, VerificationReport


@mcp.tool()
def create_pipeline_summary(
    pipeline_steps: list[dict[str, Any]],
    results: dict[str, Any],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Create a detailed summary document for an image analysis pipeline.

    This tool generates a comprehensive markdown report documenting all steps
    in an image analysis workflow, including parameters used, outputs generated,
    and final results.

    Args:
        pipeline_steps: List of pipeline steps, each containing:
            - operation: Name of the operation
            - tool: Tool/function used
            - parameters: Dict of parameters used
            - output: Output file path or description
            - metrics: Optional metrics from this step
        results: Final results dictionary with status and summary metrics
        output_path: Optional path to save summary (default: ./pipeline_summary.md)

    Returns:
        Dictionary with summary text and file path
    """
    try:
        summary = PipelineSummary.create_summary(pipeline_steps, results, output_path)
        return {
            "success": True,
            "summary": summary,
            "output_path": output_path or "./pipeline_summary.md",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def verify_segmentation_results(
    mask_path: str,
    original_image_path: str,
    expected_cell_count: int | None = None,
    min_cell_size: int = 10,
    max_cell_size: int | None = None,
    generate_report: bool = True,
    report_path: str | None = None,
) -> dict[str, Any]:
    """Verify and validate segmentation results against quality criteria.

    This tool performs automated quality checks on segmentation masks,
    calculating metrics and validating against expected criteria.

    Args:
        mask_path: Path to segmentation mask file
        original_image_path: Path to original image
        expected_cell_count: Expected number of cells (optional validation)
        min_cell_size: Minimum acceptable cell size in pixels
        max_cell_size: Maximum acceptable cell size in pixels (optional)
        generate_report: Whether to generate a detailed verification report
        report_path: Optional path for report (default: ./verification_report.md)

    Returns:
        Dictionary with verification results, metrics, and validation status
    """
    try:
        verification_results = VerificationReport.verify_segmentation(
            mask_path,
            original_image_path,
            expected_cell_count,
            min_cell_size,
            max_cell_size,
        )

        if generate_report:
            report = VerificationReport.create_verification_report(
                verification_results, report_path
            )
            verification_results["report"] = report
            verification_results["report_path"] = report_path or "./verification_report.md"

        return verification_results

    except Exception as e:
        return {
            "verified": False,
            "error": str(e),
        }


@mcp.tool()
def save_analysis_memory(
    pipeline_id: str,
    data: dict[str, Any],
    memory_dir: str = "./pipeline_memory",
    append: bool = False,
) -> dict[str, Any]:
    """Save analysis pipeline memory to disk for future reference.

    This tool creates a persistent record of pipeline execution, including
    parameters, results, and any other relevant data for reproducibility.

    Args:
        pipeline_id: Unique identifier for this pipeline (e.g., 'experiment_001')
        data: Dictionary containing memory data to save
        memory_dir: Directory to store memory files
        append: Whether to append to existing memory or create new

    Returns:
        Dictionary with success status and file path
    """
    try:
        memory_manager = PipelineMemory(memory_dir)
        memory_file = memory_manager.save_memory(pipeline_id, data, append)
        return {
            "success": True,
            "memory_file": memory_file,
            "pipeline_id": pipeline_id,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def load_analysis_memory(
    pipeline_id: str, memory_dir: str = "./pipeline_memory"
) -> dict[str, Any]:
    """Load previously saved analysis pipeline memory.

    This tool retrieves saved pipeline execution data for review or reproduction.

    Args:
        pipeline_id: Unique identifier for the pipeline to load
        memory_dir: Directory where memory files are stored

    Returns:
        Dictionary with loaded memory data or error
    """
    try:
        memory_manager = PipelineMemory(memory_dir)
        memory_data = memory_manager.load_memory(pipeline_id)

        if memory_data is None:
            return {
                "success": False,
                "error": f"No memory found for pipeline_id: {pipeline_id}",
            }

        return {"success": True, "memory": memory_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_analysis_memories(memory_dir: str = "./pipeline_memory") -> dict[str, Any]:
    """List all saved analysis pipeline memories.

    This tool provides an overview of all stored pipeline executions.

    Args:
        memory_dir: Directory where memory files are stored

    Returns:
        Dictionary with list of available memories
    """
    try:
        memory_manager = PipelineMemory(memory_dir)
        memories = memory_manager.list_memories()
        return {"success": True, "memories": memories, "count": len(memories)}
    except Exception as e:
        return {"success": False, "error": str(e)}
