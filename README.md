# Cellpose CLI and MCP Server

[![Python 3.11-3.12](https://img.shields.io/badge/python-3.11--3.12-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![PyPI](https://img.shields.io/pypi/v/cellpose-mcp.svg)](https://pypi.org/project/cellpose-mcp/)

Cellpose-mcp provides a command-line interface and a Model Context Protocol (MCP) server for Cellpose segmentation workflows. Use the CLI for reproducible shell scripts, batch processing, and HPC-style runs; use the MCP server when an AI assistant should call the same Cellpose operations through natural language.

The package exposes 11 operations for 2D/3D segmentation, batch processing, image restoration, mask export, image metadata, and diameter estimation.


![Cellpose-MCP Research Poster](https://raw.githubusercontent.com/surajinacademia/cellpose_mcp/main/poster/cellpose_mcp_poster.png)


> **📌 Note**: This project started as a fun project inspired by [napari-mcp](https://github.com/royerlab/napari-mcp) and adapted for [Cellpose](https://github.com/MouseLand/cellpose) segmentation workflows. If you would like to contribute then please get in touch with me at [ssahu2@ucmerced.edu](mailto:ssahu2@ucmerced.edu).

### 🚀 Quick Start

**Requirements:** Python 3.11 or 3.12 (use a virtual environment or conda).

**Install from PyPI:**

```bash
pip install cellpose-mcp
```

**Run Cellpose from the shell:**

```bash
cellpose-mcp-cli models
cellpose-mcp-cli info demo_images/img00.png
mkdir -p results
cellpose-mcp-cli segment-2d demo_images/img00.png --model-type nuclei --diameter 30 --cpu --output results/img00_masks.tif
```

CLI commands print JSON to stdout and return a nonzero exit code when an operation reports an error.
Cellpose is pinned to `3.1.1.1`, the release that supports both segmentation and image restoration. CPU processing can be slow, so prefer GPU/MPS when available.

**Configure an AI app for MCP:**

```bash
cellpose-mcp-install cursor
# or:
cellpose-mcp-install codex
```

The installer uses the Python that runs the command (or a conda env named `Cellpose_mcp` if present). Restart your AI app after configuring.

**Development install (from source):**

```bash
git clone https://github.com/surajinacademia/cellpose_mcp.git
cd cellpose_mcp
pip install -e .
```

During development, `python -m cellpose_mcp.cli.app ...` runs the same CLI without relying on an installed console script.

### Command-line Usage

| Task | Command |
| ---- | ------- |
| List models | `cellpose-mcp-cli models` |
| Inspect an image | `cellpose-mcp-cli info path/to/image.tif` |
| Estimate diameter | `cellpose-mcp-cli estimate-diameter path/to/image.tif --model-type cyto2 --cpu` |
| Segment one 2D image | `cellpose-mcp-cli segment-2d path/to/image.tif --model-type nuclei --diameter 30 --cpu --output path/to/masks.tif` |
| Segment one 3D volume | `cellpose-mcp-cli segment-3d path/to/volume.tif --model-type cyto3 --cpu --output path/to/volume_masks.tif` |
| Segment a batch | `cellpose-mcp-cli batch path/to/*.tif --model-type cyto2 --output-dir results --cpu` |
| Denoise | `cellpose-mcp-cli denoise path/to/image.tif --model-type denoise_cyto3 --output results/denoised.tif` |
| Restore and segment | `cellpose-mcp-cli restore-and-segment path/to/noisy.tif --restoration-model oneclick_cyto3 --segmentation-model cyto3 --cpu` |
| Save masks, outlines, and overlay | `cellpose-mcp-cli save-masks path/to/masks.tif --image path/to/image.tif --output results/masks_formatted.tif` |

All commands use the same core implementation as the MCP tools.

### Security and Trust

- Cellpose runs locally. This package does not upload image bytes, but your AI client has its own data-handling policy.
- The MCP server uses local stdio and inherits the filesystem permissions of the user who starts it. It is not a sandbox; connect only trusted MCP clients.
- Input paths ending in `.npy` are rejected because the pinned Cellpose reader enables Python pickle for that format. Convert untrusted arrays to TIFF or PNG before use.
- Model arguments accept only the 23 curated identifiers returned by `cellpose-mcp-cli models`; arbitrary model paths are rejected.
- Missing model weights are downloaded only from `https://www.cellpose.org/models/` with certificate verification and a download-size limit.
- Commands write to the explicit output path, or to the documented suffix beside the input image. Existing output files may be replaced.
- The installer resolves Python to an absolute executable, refuses malformed or symlinked config targets, and publishes config files atomically with private permissions on POSIX.

See [SECURITY.md](https://github.com/surajinacademia/cellpose_mcp/blob/main/SECURITY.md) for supported versions and vulnerability reporting.

### Auto-Configure Your AI Application

After `pip install cellpose-mcp`, run the installer for your app. It writes to the correct MCP config file using your current Python.

| Application | Command | Notes |
| ----------- | ------- | ----- |
| **Cursor IDE** | `cellpose-mcp-install cursor` | Writes to `~/.cursor/mcp.json` |
| **Claude Desktop** | `cellpose-mcp-install claude-desktop` | Adds to Claude Desktop config |
| **Antigravity** | `cellpose-mcp-install antigravity` | Configures Antigravity MCP |
| **VS Code (Cline/Roo Cline)** | `cellpose-mcp-install vscode` | Configures Cline/Roo Cline extension |
| **Claude Code** | `cellpose-mcp-install claude-code` | Writes project-local `.mcp.json` |
| **Codex CLI/App** | `cellpose-mcp-install codex` or `cellpose-mcp-install codex-desktop` | Writes `~/.codex/config.toml` |
| **Codex project-local** | `cellpose-mcp-install codex-project` | Writes `.codex/config.toml` |

Options: `--python-path /path/to/python` to use a specific Python; `--env-name NAME` to use a conda env (default: `Cellpose_mcp`).

<details>
<summary>Manual Configuration for Claude Code</summary>

If you prefer manual setup (or use Claude Code), create a `.mcp.json` file in your project root. Use the full path to your Python executable if `python` is not the one that has `cellpose-mcp` installed (e.g. a venv or conda):

```json
{
  "mcpServers": {
    "cellpose": {
      "command": "python",
      "args": ["-m", "cellpose_mcp"],
      "env": {
        "KMP_DUPLICATE_LIB_OK": "TRUE",
        "OMP_NUM_THREADS": "1"
      }
    }
  }
}
```

For **Cursor**, use the same structure in `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` in your project.
</details>

<details>
<summary>Manual Configuration for Codex</summary>

Codex uses TOML config. For a global setup, edit `~/.codex/config.toml`; for a project-local setup, edit `.codex/config.toml`:

```toml
[mcp_servers.cellpose]
command = "python"
args = ["-m", "cellpose_mcp"]

[mcp_servers.cellpose.env]
KMP_DUPLICATE_LIB_OK = "TRUE"
OMP_NUM_THREADS = "1"
```
</details>

After installation, restart your AI app and try asking:

```text
"Can you list available Cellpose models?"
"Segment the cells in ./data/sample.tif using the cyto2 model"
```

Or run the same operations directly from the shell:

```bash
cellpose-mcp-cli segment-2d ./data/sample.tif --model-type cyto2 --cpu --output ./data/sample_masks.tif
cellpose-mcp-cli batch ./data/*.tif --model-type cyto2 --output-dir ./output --cpu
```

## 🎯 What Can You Do?

### Example: Cell Segmentation in Action

<table>
<tr>
<td width="50%">
<img src="https://raw.githubusercontent.com/surajinacademia/cellpose_mcp/main/poster/poster_images/img00.png" alt="Original fluorescence microscopy image" />
<p align="center"><em>Original Image: Fluorescence microscopy with green-stained cytoplasm and blue-stained nuclei</em></p>
</td>
<td width="50%">
<img src="https://raw.githubusercontent.com/surajinacademia/cellpose_mcp/main/poster/poster_images/img00_annotated_overlay.png" alt="Segmented cells with annotations" />
<p align="center"><em>Segmented Result: Cells automatically detected with boundaries and labels</em></p>
</td>
</tr>
</table>

### Basic Cell Segmentation

```text
"Segment the cells in ./data/sample.tif using the cyto2 model"
"List available Cellpose models"
"Estimate cell diameter from ./data/image.tif"
```

### Advanced Workflows

```text
"Segment all TIFF files in ./data/images/ and save masks to ./output/"
"Segment the 3D volume in ./data/volume.tif and save masks to ./output/volume_masks.tif"
"Restore and segment the noisy image in ./data/noisy.tif using oneclick_cyto3"
```

### Batch Processing

```text
"Process all images in ./data/ with the cyto2 model and save results to ./output/"
```

## 🛠 Available MCP Tools

The MCP server exposes the same 11 Cellpose operations for AI assistants:

### Segmentation Tools

- **`segment_cells_2d`** - Segment cells in 2D images
- **`segment_cells_3d`** - Segment cells in 3D volumes
- **`segment_cells_batch`** - Batch process multiple images

### Image Restoration Tools

- **`denoise_image`** - Denoise microscopy images
- **`deblur_image`** - Deblur microscopy images
- **`upsample_image`** - Upsample low-resolution images
- **`restore_and_segment`** - Combined restoration + segmentation

### Utility Tools

- **`list_available_models`** - List all pretrained models
- **`estimate_cell_diameter`** - Estimate cell diameter from image
- **`save_masks`** - Save masks in various formats
- **`load_image_info`** - Get image metadata

## 📖 Documentation

- **[Quick Start Guide](#-quick-start)** - Get running in 3 steps
- **[Command-line Usage](#command-line-usage)** - CLI commands for Cellpose workflows
- **[Available MCP Tools](#-available-mcp-tools)** - MCP tool list
- **[Release Notes](https://github.com/surajinacademia/cellpose_mcp/blob/main/RELEASE_NOTES_v0.1.5.md)** - Detailed v0.1.5 release information
- **[Changelog](https://github.com/surajinacademia/cellpose_mcp/blob/main/CHANGELOG.md)** - Version history and changes


## 📋 Architecture

- **Core operations**: Manage Cellpose model loading, segmentation, restoration, and file I/O without MCP dependencies
- **FastMCP adapter**: Registers the core operations as MCP tools for AI assistants
- **CLI adapter**: Exposes the same operations through `cellpose-mcp-cli` for reproducible command-line workflows
- **Installer CLI**: Writes MCP config for supported AI applications

Key features:

- **Reproducible CLI**: JSON output and shell exit codes for scripts and batch runs
- **MCP compatibility**: Existing AI-app integrations still use the same FastMCP server
- **Shared core**: CLI and MCP both call the same Cellpose operation layer


**Author:** [Suraj Sahu](https://physics.ucmerced.edu/content/suraj-sahu)
**Affiliation:** Department of Physics, University of California Merced, CA, USA
**Email:** ssahu2@ucmerced.edu


## 📄 License

BSD-3-Clause License - see [LICENSE](LICENSE) file for details.


## 🙏 Acknowledgments

- **[Napari MCP](https://github.com/royerlab/napari-mcp)** by [royerlab](https://github.com/royerlab)
- [Cellpose team](https://github.com/MouseLand/cellpose) for the excellent segmentation library
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [Anthropic](https://www.anthropic.com/) for Claude and MCP development
- [Model Context Protocol](https://modelcontextprotocol.io/) - Open standard for AI-tool integration

---
