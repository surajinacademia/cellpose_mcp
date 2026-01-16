"""Shared MCP instance for Cellpose MCP Server."""

from fastmcp import FastMCP

# Create the MCP instance here - this will be imported by both server and tools
mcp = FastMCP("Cellpose MCP Server")
