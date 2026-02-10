# Cellpose MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![PyPI](https://img.shields.io/pypi/v/cellpose-mcp.svg)](https://pypi.org/project/cellpose-mcp/)

Cellpose-mcp is a Model Context Protocol (MCP) server that enables AI assistants like Claude, Cursor IDE, etc. to perform cell segmentation through natural language commands. This tool exposes comprehensive Cellpose functionality through 13+ MCP tools, including 2D/3D segmentation, batch processing, image restoration (denoising, deblurring, upsampling), and custom model training. The system integrates seamlessly with Napari, enabling complete workflows from segmentation to interactive visualization.


![Cellpose-MCP Research Poster](https://raw.githubusercontent.com/surajinacademia/cellpose_mcp/main/poster/cellpose_mcp_poster.png)


> **📌 Note**: This project started as a fun project inspired by [napari-mcp](https://github.com/royerlab/napari-mcp) and adapted for [Cellpose](https://github.com/MouseLand/cellpose) segmentation workflows. If you would like to contribute then please get in touch with me at [ssahu2@ucmerced.edu](mailto:ssahu2@ucmerced.edu).

### 🚀 Quick Start

```bash
pip install cellpose-mcp
```

**OR for development:**

```bash
git clone https://github.com/surajinacademia/cellpose_mcp.git
cd cellpose_mcp
pip install -e .
```

### Auto-Configure Your AI Application

| Application | Installation Command | Notes |
| ----------- | -------------------- | ----- |
| **Cursor IDE** | `cellpose-mcp-install cursor` | Auto-configures MCP settings |
| **Claude Desktop** | `cellpose-mcp-install claude-desktop` | Adds to Claude Desktop config |
| **Antigravity** | `cellpose-mcp-install antigravity` | Configures Antigravity MCP |
| **Claude Code** | `cellpose-mcp-install claude-code` | Or manually add `.mcp.json` to project root |
| **VS Code** | `cellpose-mcp-install vscode` | Configures Cline/Roo Cline extension |

<details>
<summary>Manual Configuration for Claude Code</summary>

If you prefer manual setup, create a `.mcp.json` file in your project root:

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
</details>

After installation, restart your AI app and try asking:

```text
"Can you list available Cellpose models?"
"Segment the cells in ./data/sample.tif using the cyto2 model"
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
"Train a custom segmentation model using images in ./train/images/ and masks in ./train/masks/"
"Restore and segment the noisy image in ./data/noisy.tif using oneclick_cyto3"
```

### Batch Processing

```text
"Process all images in ./data/ with the cyto2 model and save results to ./output/"
```

## 🛠 Available MCP Tools

The server exposes 13+ tools for complete Cellpose functionality:

### Segmentation Tools

- **`segment_cells_2d`** - Segment cells in 2D images
- **`segment_cells_3d`** - Segment cells in 3D volumes
- **`segment_cells_batch`** - Batch process multiple images

### Image Restoration Tools

- **`denoise_image`** - Denoise microscopy images
- **`deblur_image`** - Deblur microscopy images
- **`upsample_image`** - Upsample low-resolution images
- **`restore_and_segment`** - Combined restoration + segmentation

### Training Tools

- **`train_segmentation_model`** - Train custom segmentation model
- **`train_restoration_model`** - Train custom restoration model

### Utility Tools

- **`list_available_models`** - List all pretrained models
- **`estimate_cell_diameter`** - Estimate cell diameter from image
- **`save_masks`** - Save masks in various formats
- **`load_image_info`** - Get image metadata

## 📖 Documentation

- **[Quick Start Guide](#-quick-start)** - Get running in 3 steps
- **[Available Tools](#-available-mcp-tools)** - Complete tool list
- **[Release Notes](https://github.com/surajinacademia/cellpose_mcp/blob/main/RELEASE_NOTES_v0.1.0.md)** - Detailed v0.1.0 release information
- **[Changelog](https://github.com/surajinacademia/cellpose_mcp/blob/main/CHANGELOG.md)** - Version history and changes


## 📋 Architecture

- **FastMCP Server**: Handles MCP protocol communication
- **Cellpose Integration**: Manages model loading and segmentation operations
- **Tool Layer**: Exposes Cellpose functionality as MCP tools
- **File I/O**: Handles image reading, writing, and mask generation

Key features:

- **Thread-safe**: All operations are properly serialized
- **Non-blocking**: Async operations for better performance
- **Napari Integration**: Integration with Napari for visualization and analysis


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
