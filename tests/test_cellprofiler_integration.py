"""Unit tests for CellProfiler integration."""

import os

import pytest

# Set OpenMP env vars before imports
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from cellpose_mcp.cellprofiler_integration import CellProfilerIntegration


@pytest.fixture
def cp_integration():
    """Create a CellProfilerIntegration instance."""
    return CellProfilerIntegration()


class TestCellProfilerIntegration:
    """Tests for CellProfilerIntegration class."""

    def test_check_cellprofiler_available(self, cp_integration):
        """Test checking if CellProfiler is available."""
        # This will be False in most test environments
        result = cp_integration.cellprofiler_available
        assert isinstance(result, bool)

    def test_import_cellpose_masks_empty_dir(self, cp_integration, tmp_path):
        """Test importing masks from empty directory."""
        result = cp_integration.import_cellpose_masks(str(tmp_path))
        assert result["success"] is False
        assert "No mask files found" in result["error"]

    def test_import_cellpose_masks_with_files(self, cp_integration, tmp_path):
        """Test importing masks when files exist."""
        # Create dummy mask files
        (tmp_path / "image1_masks.tif").touch()
        (tmp_path / "image2_masks.png").touch()

        result = cp_integration.import_cellpose_masks(str(tmp_path))
        assert result["success"] is True
        assert result["mask_count"] == 2

    def test_export_measurements_nonexistent_dir(self, cp_integration):
        """Test exporting measurements from non-existent directory."""
        result = cp_integration.export_measurements("/nonexistent/path")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_export_measurements_empty_dir(self, cp_integration, tmp_path):
        """Test exporting measurements from empty directory."""
        result = cp_integration.export_measurements(str(tmp_path))
        assert result["success"] is True
        assert result["file_count"] == 0

    def test_export_measurements_with_csv(self, cp_integration, tmp_path):
        """Test exporting CSV measurements."""
        # Create dummy CSV files
        (tmp_path / "measurements.csv").touch()
        (tmp_path / "data.csv").touch()

        result = cp_integration.export_measurements(str(tmp_path), format="csv")
        assert result["success"] is True
        assert result["file_count"] == 2
        assert result["format"] == "csv"

    def test_create_basic_pipeline(self, cp_integration, tmp_path):
        """Test creating a basic pipeline."""
        output_path = tmp_path / "test_pipeline.json"
        modules = [
            {"name": "LoadImages", "type": "LoadImages"},
            {"name": "IdentifyPrimaryObjects", "type": "IdentifyPrimaryObjects"},
        ]

        result = cp_integration.create_basic_pipeline(
            ["image1.tif", "image2.tif"], str(output_path), modules
        )

        assert result["success"] is True
        assert result["module_count"] == 2
        assert output_path.exists()

    @pytest.mark.integration
    def test_run_pipeline_without_cellprofiler(self, cp_integration, tmp_path):
        """Test running pipeline when CellProfiler is not available."""
        if not cp_integration.cellprofiler_available:
            result = cp_integration.run_pipeline(
                "dummy.cppipe", str(tmp_path), str(tmp_path / "output")
            )
            assert result["success"] is False
            assert "not installed" in result["error"]
