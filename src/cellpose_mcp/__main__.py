"""Main entry point for cellpose-mcp server."""

from cellpose_mcp.server import mcp


def main() -> None:
    """Run the Cellpose MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
