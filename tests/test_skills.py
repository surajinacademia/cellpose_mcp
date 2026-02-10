"""Unit tests for skills module."""

import json
import os
from pathlib import Path

import pytest

# Set OpenMP env vars before imports
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from cellpose_mcp.skills import PipelineMemory, PipelineSummary, VerificationReport


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def pipeline_memory(temp_dir):
    """Create a PipelineMemory instance."""
    return PipelineMemory(str(temp_dir / "memory"))


class TestPipelineMemory:
    """Tests for PipelineMemory class."""

    def test_save_memory(self, pipeline_memory, temp_dir):
        """Test saving pipeline memory."""
        pipeline_id = "test_pipeline_001"
        data = {"param1": "value1", "param2": 42}

        memory_file = pipeline_memory.save_memory(pipeline_id, data)

        assert Path(memory_file).exists()
        assert pipeline_id in memory_file

    def test_load_memory(self, pipeline_memory):
        """Test loading pipeline memory."""
        pipeline_id = "test_pipeline_002"
        data = {"param1": "value1", "param2": 42}

        pipeline_memory.save_memory(pipeline_id, data)
        loaded_data = pipeline_memory.load_memory(pipeline_id)

        assert loaded_data is not None
        assert loaded_data["pipeline_id"] == pipeline_id
        assert loaded_data["data"] == data

    def test_load_nonexistent_memory(self, pipeline_memory):
        """Test loading non-existent memory returns None."""
        result = pipeline_memory.load_memory("nonexistent")
        assert result is None

    def test_append_memory(self, pipeline_memory):
        """Test appending to existing memory."""
        pipeline_id = "test_pipeline_003"
        data1 = {"step": 1}
        data2 = {"step": 2}

        pipeline_memory.save_memory(pipeline_id, data1)
        pipeline_memory.save_memory(pipeline_id, data2, append=True)

        loaded_data = pipeline_memory.load_memory(pipeline_id)
        assert len(loaded_data["history"]) == 1

    def test_list_memories(self, pipeline_memory):
        """Test listing all memories."""
        pipeline_memory.save_memory("pipeline_1", {"data": 1})
        pipeline_memory.save_memory("pipeline_2", {"data": 2})

        memories = pipeline_memory.list_memories()
        assert len(memories) == 2
        pipeline_ids = [m["pipeline_id"] for m in memories]
        assert "pipeline_1" in pipeline_ids
        assert "pipeline_2" in pipeline_ids


class TestPipelineSummary:
    """Tests for PipelineSummary class."""

    def test_create_summary(self, temp_dir):
        """Test creating a pipeline summary."""
        pipeline_steps = [
            {
                "operation": "Segmentation",
                "tool": "segment_cells_2d",
                "parameters": {"model_type": "cyto2", "diameter": 30},
                "output": "/tmp/masks.tif",
            }
        ]
        results = {"status": "Success", "cells_detected": 42}
        output_path = str(temp_dir / "summary.md")

        summary = PipelineSummary.create_summary(
            pipeline_steps, results, output_path
        )

        assert "Image Analysis Pipeline Summary" in summary
        assert "Segmentation" in summary
        assert "segment_cells_2d" in summary
        assert Path(output_path).exists()

    def test_summary_contains_steps(self, temp_dir):
        """Test that summary contains all pipeline steps."""
        pipeline_steps = [
            {"operation": "Step 1", "tool": "tool1"},
            {"operation": "Step 2", "tool": "tool2"},
        ]
        results = {"status": "Success"}
        output_path = str(temp_dir / "summary2.md")

        summary = PipelineSummary.create_summary(
            pipeline_steps, results, output_path
        )

        assert "Step 1" in summary
        assert "Step 2" in summary
        assert "tool1" in summary
        assert "tool2" in summary


class TestVerificationReport:
    """Tests for VerificationReport class."""

    def test_verify_segmentation_mock_no_deps(self, temp_dir, monkeypatch):
        """Test verification without actual image files."""
        # This is a smoke test without dependencies
        # Full integration tests would require actual image files
        pass

    def test_create_verification_report(self, temp_dir):
        """Test creating a verification report."""
        verification_results = {
            "verified": True,
            "metrics": {
                "total_cells": 42,
                "average_cell_size": 150.5,
            },
            "validation": {
                "pass": True,
                "warnings": [],
                "errors": [],
            },
        }
        output_path = str(temp_dir / "verification.md")

        report = VerificationReport.create_verification_report(
            verification_results, output_path
        )

        assert "Segmentation Verification Report" in report
        assert "PASSED" in report
        assert "42" in report
        assert Path(output_path).exists()

    def test_verification_report_with_errors(self, temp_dir):
        """Test creating a verification report with errors."""
        verification_results = {
            "verified": False,
            "metrics": {},
            "validation": {
                "pass": False,
                "warnings": ["High variability"],
                "errors": ["No cells detected"],
            },
        }
        output_path = str(temp_dir / "verification_error.md")

        report = VerificationReport.create_verification_report(
            verification_results, output_path
        )

        assert "FAILED" in report
        assert "No cells detected" in report
        assert "High variability" in report
