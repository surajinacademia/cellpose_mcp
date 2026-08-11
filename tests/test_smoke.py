"""Fast import and wiring checks (no segmentation runs)."""

from __future__ import annotations

import types

import pytest


@pytest.mark.smoke
def test_package_import_exposes_mcp() -> None:
    """Top-level package import must succeed and expose a FastMCP instance."""
    import cellpose_mcp

    assert cellpose_mcp.mcp is not None
    assert hasattr(cellpose_mcp.mcp, "run")


@pytest.mark.smoke
def test_mcp_singleton_matches_mcp_instance() -> None:
    """Server re-export must be the same object as the shared FastMCP instance."""
    from cellpose_mcp.mcp_instance import mcp as from_instance
    from cellpose_mcp.server import mcp as from_server

    assert from_server is from_instance


@pytest.mark.smoke
def test_tools_are_plain_callables_after_unwrap() -> None:
    """Public tool names must be plain functions; MCP may wrap as ``FunctionTool``."""
    from cellpose_mcp import tools

    assert isinstance(tools.segment_cells_2d, types.FunctionType)
    wrapped = tools._segment_cells_2d_tool
    assert getattr(wrapped, "fn", wrapped) is tools.segment_cells_2d


@pytest.mark.smoke
async def test_mcp_surface_excludes_training() -> None:
    """The simplified MCP surface should not expose model training."""
    from cellpose_mcp.server import mcp

    tool_names = set(await mcp.get_tools())

    assert "segment_cells_3d" in tool_names
    assert "train_segmentation_model" not in tool_names
