"""FastMCP server for Cellpose cell segmentation."""

# Import the shared MCP instance (created in mcp_instance.py)
from cellpose_mcp.mcp_instance import mcp

# Import tools to register them with the MCP server
# The tools module imports mcp from mcp_instance, so all decorators use the same instance
from cellpose_mcp import (  # noqa: F401
    cellprofiler_tools,
    package_tools,
    skills_tools,
    tools,
)
