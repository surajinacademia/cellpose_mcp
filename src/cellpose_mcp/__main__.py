"""Main entry point for cellpose-mcp server."""

import os

# Fix OpenMP threading conflicts that can cause model.eval() to hang
# This must be set BEFORE importing cellpose or any libraries that use OpenMP
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from cellpose_mcp.server import mcp


def main() -> None:
    """Run the Cellpose MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
