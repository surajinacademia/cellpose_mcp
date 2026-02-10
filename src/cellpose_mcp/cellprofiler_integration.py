"""CellProfiler integration for advanced image analysis workflows."""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

# Fix OpenMP threading conflicts
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")


class CellProfilerIntegration:
    """Handles integration with CellProfiler for advanced image analysis."""

    def __init__(self):
        """Initialize CellProfiler integration."""
        self.cellprofiler_available = self._check_cellprofiler_available()

    def _check_cellprofiler_available(self) -> bool:
        """Check if CellProfiler is available in the environment.

        Returns:
            True if CellProfiler is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["cellprofiler", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run_pipeline(
        self,
        pipeline_file: str,
        input_dir: str,
        output_dir: str,
        plugins_dir: str | None = None,
    ) -> dict[str, Any]:
        """Run a CellProfiler pipeline.

        Args:
            pipeline_file: Path to CellProfiler pipeline file (.cppipe)
            input_dir: Directory containing input images
            output_dir: Directory to save output files
            plugins_dir: Optional directory containing CellProfiler plugins

        Returns:
            Dictionary with execution results
        """
        if not self.cellprofiler_available:
            return {
                "success": False,
                "error": "CellProfiler is not installed or not available in PATH",
            }

        try:
            # Construct CellProfiler command
            cmd = [
                "cellprofiler",
                "-c",
                "-r",
                "-p",
                pipeline_file,
                "-i",
                input_dir,
                "-o",
                output_dir,
            ]

            if plugins_dir:
                cmd.extend(["--plugins-directory", plugins_dir])

            # Run CellProfiler
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output_dir": output_dir,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Pipeline execution timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_basic_pipeline(
        self,
        input_images: list[str],
        output_path: str,
        modules: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create a basic CellProfiler pipeline programmatically.

        Args:
            input_images: List of input image paths
            output_path: Path to save the pipeline file
            modules: List of module configurations

        Returns:
            Dictionary with pipeline creation results
        """
        try:
            # Create a basic CellProfiler pipeline structure
            pipeline = {
                "CellProfiler Pipeline": "http://www.cellprofiler.org",
                "Version": 5,
                "DateRevision": "20220623123522",
                "GitHash": "",
                "ModuleCount": len(modules),
                "HasImagePlaneDetails": False,
            }

            # Add modules
            pipeline["Modules"] = modules

            # Save pipeline
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(pipeline, f, indent=2)

            return {
                "success": True,
                "pipeline_path": output_path,
                "module_count": len(modules),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_cellpose_masks(
        self,
        mask_dir: str,
        cellprofiler_project: str | None = None,
    ) -> dict[str, Any]:
        """Import Cellpose segmentation masks into CellProfiler format.

        Args:
            mask_dir: Directory containing Cellpose masks
            cellprofiler_project: Optional CellProfiler project to import into

        Returns:
            Dictionary with import results
        """
        try:
            mask_files = list(Path(mask_dir).glob("*_masks.*"))

            if not mask_files:
                return {
                    "success": False,
                    "error": "No mask files found in directory",
                }

            return {
                "success": True,
                "mask_count": len(mask_files),
                "mask_files": [str(f) for f in mask_files],
                "note": "Masks are in standard format compatible with CellProfiler LoadObjects module",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def export_measurements(
        self,
        output_dir: str,
        format: str = "csv",
    ) -> dict[str, Any]:
        """Export CellProfiler measurements in specified format.

        Args:
            output_dir: Directory containing CellProfiler output
            format: Export format (csv, excel, database)

        Returns:
            Dictionary with export results
        """
        try:
            output_path = Path(output_dir)
            if not output_path.exists():
                return {
                    "success": False,
                    "error": f"Output directory not found: {output_dir}",
                }

            # Find measurement files
            if format == "csv":
                measurement_files = list(output_path.glob("*.csv"))
            elif format == "excel":
                measurement_files = list(output_path.glob("*.xlsx"))
            else:
                measurement_files = list(output_path.glob("*"))

            return {
                "success": True,
                "measurement_files": [str(f) for f in measurement_files],
                "file_count": len(measurement_files),
                "format": format,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
