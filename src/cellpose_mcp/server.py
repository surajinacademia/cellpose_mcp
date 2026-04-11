"""FastMCP server for Cellpose cell segmentation."""

# Re-export the shared MCP instance for package entry points and ``cellpose_mcp.mcp``
# Import tools to register them with the MCP server
# The tools module imports mcp from mcp_instance, so all decorators use the same instance
from cellpose_mcp import tools  # noqa: F401
from cellpose_mcp.mcp_instance import mcp

__all__ = ["mcp"]
