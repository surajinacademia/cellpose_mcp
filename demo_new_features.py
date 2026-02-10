"""Demo script showing how to use the new skills, verification, and integration features.

This script demonstrates the usage of:
1. Pipeline summary generation
2. Verification of segmentation results
3. Memory/logging for pipelines
4. CellProfiler integration
5. Package management

Note: This is a demonstration script. Actual usage would involve the MCP server.
"""

import os
import sys

# Set OpenMP env vars
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

# Add src to path for testing - import modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import modules directly without going through package __init__
from cellpose_mcp.skills import PipelineMemory, PipelineSummary, VerificationReport
from cellpose_mcp.package_manager import PackageManager
from cellpose_mcp.cellprofiler_integration import CellProfilerIntegration


def demo_pipeline_summary():
    """Demonstrate pipeline summary generation."""
    print("\n" + "=" * 60)
    print("DEMO: Pipeline Summary Generation")
    print("=" * 60)

    # Define pipeline steps
    pipeline_steps = [
        {
            "operation": "Cell Segmentation",
            "tool": "segment_cells_2d",
            "parameters": {
                "model_type": "cyto2",
                "diameter": 30,
                "flow_threshold": 0.4,
            },
            "output": "./output/masks.tif",
            "metrics": {
                "cells_detected": 142,
                "processing_time": "2.3s",
            },
        },
        {
            "operation": "Quality Verification",
            "tool": "verify_segmentation_results",
            "parameters": {
                "min_cell_size": 10,
                "expected_cell_count": 150,
            },
            "metrics": {
                "average_cell_size": 245.6,
                "verification_status": "passed",
            },
        },
    ]

    results = {
        "status": "Success",
        "total_cells_detected": 142,
        "quality_score": 0.95,
        "processing_time_total": "3.1s",
    }

    # Create summary
    summary = PipelineSummary.create_summary(
        pipeline_steps, results, "/tmp/demo_pipeline_summary.md"
    )

    print("\nPipeline Summary Created:")
    print("-" * 60)
    print(summary[:500] + "...")  # Show first 500 chars
    print("\nFull summary saved to: /tmp/demo_pipeline_summary.md")


def demo_memory_management():
    """Demonstrate pipeline memory management."""
    print("\n" + "=" * 60)
    print("DEMO: Pipeline Memory Management")
    print("=" * 60)

    memory_manager = PipelineMemory("/tmp/demo_memory")

    # Save pipeline memory
    pipeline_id = "experiment_2024_001"
    data = {
        "experiment_name": "Cell counting analysis",
        "image_source": "./data/sample.tif",
        "model_used": "cyto2",
        "parameters": {"diameter": 30, "flow_threshold": 0.4},
        "results": {"cells_detected": 142},
    }

    memory_file = memory_manager.save_memory(pipeline_id, data)
    print(f"\n✓ Memory saved to: {memory_file}")

    # Load memory back
    loaded = memory_manager.load_memory(pipeline_id)
    print(f"\n✓ Memory loaded successfully")
    print(f"  Pipeline ID: {loaded['pipeline_id']}")
    print(f"  Created at: {loaded['created_at']}")
    print(f"  Experiment: {loaded['data']['experiment_name']}")

    # List all memories
    memories = memory_manager.list_memories()
    print(f"\n✓ Total saved memories: {len(memories)}")


def demo_package_manager():
    """Demonstrate package management features."""
    print("\n" + "=" * 60)
    print("DEMO: Package Management")
    print("=" * 60)

    # Get allowed packages
    allowed = PackageManager.get_allowed_packages()
    print(f"\n✓ Total allowed packages: {len(allowed)}")
    print("\nSample allowed packages:")
    for pkg in allowed[:10]:
        print(f"  - {pkg}")

    # Check if specific packages are allowed
    print("\nPackage allowlist checks:")
    test_packages = ["scikit-image", "opencv-python", "malicious-package"]
    for pkg in test_packages:
        is_allowed = PackageManager.is_package_allowed(pkg)
        status = "✓ ALLOWED" if is_allowed else "✗ BLOCKED"
        print(f"  {status}: {pkg}")

    # Check installed packages
    print("\nChecking if pytest is installed:")
    result = PackageManager.check_package_installed("pytest")
    if result["installed"]:
        print(f"  ✓ pytest {result['version']} is installed")
    else:
        print("  ✗ pytest is not installed")


def demo_cellprofiler_integration():
    """Demonstrate CellProfiler integration."""
    print("\n" + "=" * 60)
    print("DEMO: CellProfiler Integration")
    print("=" * 60)

    cp_integration = CellProfilerIntegration()

    # Check if CellProfiler is available
    if cp_integration.cellprofiler_available:
        print("\n✓ CellProfiler is installed and available")
    else:
        print("\n✗ CellProfiler is not installed")
        print("  To install: pip install cellprofiler")

    # Create a basic pipeline structure
    modules = [
        {"name": "LoadImages", "type": "LoadImages"},
        {"name": "IdentifyPrimaryObjects", "type": "IdentifyPrimaryObjects"},
        {"name": "MeasureObjectSizeShape", "type": "MeasureObjectSizeShape"},
    ]

    result = cp_integration.create_basic_pipeline(
        ["image1.tif"], "/tmp/demo_pipeline.json", modules
    )

    if result["success"]:
        print(f"\n✓ CellProfiler pipeline created")
        print(f"  Modules: {result['module_count']}")
        print(f"  Path: {result['pipeline_path']}")


def demo_verification():
    """Demonstrate verification report (simulated)."""
    print("\n" + "=" * 60)
    print("DEMO: Verification Report")
    print("=" * 60)

    # Simulated verification results
    verification_results = {
        "verified": True,
        "metrics": {
            "total_cells": 142,
            "average_cell_size": 245.6,
            "median_cell_size": 238.0,
            "min_cell_size_observed": 95,
            "max_cell_size_observed": 512,
            "cell_size_std": 42.3,
        },
        "validation": {
            "pass": True,
            "warnings": [
                "Cell count (142) differs slightly from expected (150)",
                "High cell size variability detected",
            ],
            "errors": [],
        },
        "mask_shape": [1024, 1024],
        "image_shape": [1024, 1024],
    }

    report = VerificationReport.create_verification_report(
        verification_results, "/tmp/demo_verification_report.md"
    )

    print("\nVerification Report Created:")
    print("-" * 60)
    print(report[:400] + "...")  # Show first 400 chars
    print("\nFull report saved to: /tmp/demo_verification_report.md")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("CELLPOSE MCP - NEW FEATURES DEMONSTRATION")
    print("=" * 60)

    demo_pipeline_summary()
    demo_memory_management()
    demo_verification()
    demo_package_manager()
    demo_cellprofiler_integration()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nAll demos completed successfully!")
    print("\nTo use these features with an AI assistant:")
    print("1. Start the MCP server: cellpose-mcp")
    print("2. Ask the AI to use the new tools:")
    print("   - 'Create a pipeline summary for my analysis'")
    print("   - 'Verify the segmentation results'")
    print("   - 'Save the pipeline memory'")
    print("   - 'Install scikit-image package'")
    print("   - 'Check if CellProfiler is available'")


if __name__ == "__main__":
    main()
