"""FastMCP server for Cellpose cell segmentation."""

from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Cellpose MCP Server")

# Import tools to register them with the MCP server
# This must happen after mcp is created
from cellpose_mcp import tools  # noqa: F401

# Make mcp available to tools module
tools.mcp = mcp
