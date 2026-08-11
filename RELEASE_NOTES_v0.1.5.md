# Cellpose-MCP v0.1.5

Version 0.1.5 returns the project to a focused design: one Cellpose operation layer with two thin interfaces. Use `cellpose-mcp-cli` for shell automation and the stdio MCP server for agent-driven analysis.

## What Ships

- 11 shared operations with JSON results
- 2D and 3D segmentation
- Batch segmentation
- Denoising, deblurring, upsampling, and restore-then-segment
- Curated model discovery, diameter estimation, image metadata, and mask export
- CLI, MCP server, and MCP client installer

Custom model training is intentionally not included.

## Security Changes

- `.npy` input is disabled before Cellpose can invoke its pickle-enabled reader.
- Model fields accept curated identifiers rather than arbitrary local paths.
- Model downloads use verified HTTPS, the official Cellpose model host, redirect checks, a size bound, and atomic writes.
- MCP installer config updates fail closed on malformed files and reject symlink traversal.
- Python executables are stored as resolved absolute paths and package verification runs in isolated mode.
- Machine-specific MCP configuration and stale release-gate files are no longer distributed.

The MCP server is a local stdio process, not a filesystem sandbox. It runs with the permissions of the user who starts it and can write the output paths supplied by the caller.

## Install

Python 3.11 or 3.12 is required.

```bash
pip install "cellpose-mcp==0.1.5"
```

Run from a terminal:

```bash
cellpose-mcp-cli models
cellpose-mcp-cli segment-2d image.tif --model-type cyto3 --cpu --output masks.tif
cellpose-mcp-cli segment-3d volume.tif --model-type cyto3 --cpu --output volume_masks.tif
```

Configure an AI client:

```bash
cellpose-mcp-install cursor
cellpose-mcp-install codex
```

See [README.md](README.md) for all commands and supported clients.
