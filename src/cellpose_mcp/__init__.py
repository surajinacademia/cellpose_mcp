"""Cellpose MCP Server - AI-powered cell segmentation via Model Context Protocol."""

import os

# Fix OpenMP threading conflicts that can cause model.eval() to hang
# This must be set BEFORE importing cellpose or any libraries that use OpenMP
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Also set OMP_NUM_THREADS to prevent potential threading issues
os.environ.setdefault("OMP_NUM_THREADS", "1")

__version__ = "0.1.0"

from cellpose_mcp.server import mcp

__all__ = ["__version__", "mcp"]
