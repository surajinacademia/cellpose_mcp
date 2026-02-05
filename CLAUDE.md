# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cellpose-mcp is a Python MCP (Model Context Protocol) server that exposes Cellpose cell segmentation capabilities to AI assistants (Claude Desktop, Cursor, Claude Code). It wraps Cellpose's segmentation, restoration, and training APIs as MCP tools.

## Common Commands

```bash
# Install for development
pip install -e ".[test,dev]"

# Run the MCP server
python -m cellpose_mcp
# or: cellpose-mcp

# Install MCP config for AI apps
cellpose-mcp-install cursor
cellpose-mcp-install claude-desktop

# Run tests
pytest
pytest -m "not slow"          # skip slow tests
pytest tests/test_file.py::test_name  # single test

# Lint and format
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type check
mypy src/cellpose_mcp --ignore-missing-imports
```

## Architecture

```
AI App (Claude/Cursor) ──MCP Protocol──▶ FastMCP Server ──▶ Tools ──▶ Cellpose
```

**Entry flow**: `__main__.py` → `server.py` (imports mcp + tools) → `mcp_instance.py` (FastMCP singleton) → `tools.py` (11 tool functions)

**Key files**:
- `src/cellpose_mcp/tools.py` — All 11 MCP tool implementations (segmentation, restoration, training, utilities). This is the main file for feature work.
- `src/cellpose_mcp/mcp_instance.py` — Single shared FastMCP instance imported by tools and server.
- `src/cellpose_mcp/cli/install.py` — Auto-installer that writes MCP config for Cursor/Claude Desktop.

**Tool registration pattern**: Functions in `tools.py` are decorated with `@mcp.tool()`, then the raw callable is re-extracted via `.fn` so tools can also be called directly in tests:
```python
@mcp.tool()
def segment_cells_2d(...): ...
_segment_cells_2d_tool = segment_cells_2d  # MCP-decorated version
segment_cells_2d = segment_cells_2d.fn      # raw callable
```

## Important Details

- **OpenMP env vars** (`KMP_DUPLICATE_LIB_OK`, `OMP_NUM_THREADS`) must be set before cellpose import. They are set in `__init__.py`, `__main__.py`, `tools.py`, and `.mcp.json`.
- **Cellpose v3/v4 compatibility**: `tools.py` handles API differences in return values (3 vs 4 tuple elements) and model type parameters. Check existing patterns when modifying tools.
- **Diameter parameter**: Value of `0` is converted to `None` for Cellpose's auto-estimation. Follow this convention for new tools.
- **Test markers**: `slow`, `integration`, `unit`, `smoke` — defined in `pyproject.toml`.
- **Docstring format**: numpy-style docstrings on all tool functions.
