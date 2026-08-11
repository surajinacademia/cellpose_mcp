"""Main entry point for cellpose-mcp server."""

import os
import sys

# Fix OpenMP threading conflicts that can cause model.eval() to hang
# This must be set BEFORE importing cellpose or any libraries that use OpenMP
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")


def main() -> None:
    """Run the Cellpose MCP server."""
    if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        print("Run the Cellpose MCP server.")
        print()
        print("Usage: python -m cellpose_mcp")
        print()
        print("This command starts the MCP server over stdio.")
        return

    from cellpose_mcp.server import mcp

    mcp.run()


if __name__ == "__main__":
    main()
