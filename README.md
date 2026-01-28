# Cellpose MCP Server

[![Tests](https://github.com/surajinacademia/cellpose_mcp/workflows/Tests/badge.svg)](https://github.com/surajinacademia/cellpose_mcp/actions)
[![codecov](https://codecov.io/gh/surajinacademia/cellpose_mcp/graph/badge.svg?token=PLACEHOLDER)](https://codecov.io/gh/surajinacademia/cellpose_mcp)
[![PyPI version](https://badge.fury.io/py/cellpose-mcp.svg)](https://badge.fury.io/py/cellpose-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

MCP server for AI-powered Cellpose cell segmentation via Model Context Protocol (MCP). Perfect for AI-assisted microscopy analysis with Claude Desktop, Cursor, and other LLM applications.

> **📌 Project Origin**: This project is **inspired by and adapted from** [napari-mcp](https://github.com/royerlab/napari-mcp) by the royerlab team. The architecture, structure, and implementation patterns follow the excellent design established by napari-mcp, adapted for Cellpose cell segmentation workflows. This project is **open source and free to fork, modify, and experiment with** - feel free to use it as a starting point for your own MCP servers!

## 🚀 Quick Start (3 Steps)

### 1. Install the Package

```bash
pip install cellpose-mcp
```

**OR for development:**
```bash
git clone https://github.com/surajinacademia/cellpose_mcp.git
cd cellpose_mcp
pip install -e .
```

### 2. Auto-Configure Your AI Application

```bash
# For Cursor IDE
cellpose-mcp-install cursor

# For other applications (Claude Desktop, Claude Code, Cline, etc.)
cellpose-mcp-install --help # See all options
```

### 3. Restart Your Application & Start Using

Restart your AI app and you're ready! Try asking:
```
"Can you list available Cellpose models?"
"Segment the cells in ./data/sample.tif using the cyto2 model"
```

## 🎯 What Can You Do?

### Basic Cell Segmentation
```
"Segment the cells in ./data/sample.tif using the cyto2 model"
"List available Cellpose models"
"Estimate cell diameter from ./data/image.tif"
```

### Advanced Workflows
```
"Segment all TIFF files in ./data/images/ and save masks to ./output/"
"Train a custom segmentation model using images in ./train/images/ and masks in ./train/masks/"
"Restore and segment the noisy image in ./data/noisy.tif using oneclick_cyto3"
```

### Batch Processing
```
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


## 🤖 Supported AI Applications

| Application | Command | Status |
|-------------|---------|--------|
| **Cursor IDE** | `cellpose-mcp-install cursor` | ✅ Full Support |
| **Claude Desktop** | `cellpose-mcp-install claude-desktop` | 🚧 Coming Soon |
| **Claude Code** | `cellpose-mcp-install claude-code` | 🚧 Coming Soon |
| **Cline (VS Code)** | `cellpose-mcp-install cline-vscode` | 🚧 Coming Soon |
| **Cline (Cursor)** | `cellpose-mcp-install cline-cursor` | 🚧 Coming Soon |

## ⚠️ Security Notice

!!! warning "Image Processing Capabilities"
 This server provides powerful image processing and model training capabilities:

 - **File I/O operations** - Reads and writes image files
 - **Model loading and execution** - Loads and runs Cellpose models
 - **Training capabilities** - Can train custom models

 **Use only with trusted AI assistants on local networks.**
 Never expose to public internet without proper sandboxing.

## 📖 Documentation

- **[Quick Start Guide](#-quick-start-3-steps)** - Get running in 3 steps
- **[Available Tools](#-available-mcp-tools)** - Complete tool list
- **[Development Setup](#-development-setup)** - Setup for contributors
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute

## 🧪 Development Setup

```bash
# Clone repository
git clone https://github.com/surajinacademia/cellpose_mcp.git
cd cellpose_mcp

# Install with development dependencies
pip install -e ".[test,dev]"

# Run tests
pytest -m "not slow" # Skip slow tests
pytest --cov=src --cov-report=html # With coverage
```

## 📋 Architecture

- **FastMCP Server**: Handles MCP protocol communication
- **Cellpose Integration**: Manages model loading and segmentation operations
- **Tool Layer**: Exposes Cellpose functionality as MCP tools
- **File I/O**: Handles image reading, writing, and mask generation

Key features:
- **Thread-safe**: All operations are properly serialized
- **Non-blocking**: Async operations for better performance
- **Extensible**: Easy to add new tools and functionality
- **Open source**: Free to fork, modify, and experiment with

## 📚 Resources

- **[Cellpose](https://github.com/MouseLand/cellpose)** - Cell segmentation library
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - MCP specification
- **[FastMCP](https://github.com/jlowin/fastmcp)** - Python MCP framework
- **[Napari MCP](https://github.com/royerlab/napari-mcp)** - Original inspiration and architectural reference
- **[Claude Desktop](https://claude.ai/download)** - AI assistant with MCP support

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run pre-commit hooks: `pre-commit run --all-files`
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

**→ See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines**

## 📄 License

BSD-3-Clause License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Napari MCP](https://github.com/royerlab/napari-mcp)** by [royerlab](https://github.com/royerlab) - This project is directly inspired by and adapted from napari-mcp. The architecture, code structure, and implementation patterns follow the excellent design established by the napari-mcp team. Thank you for creating such a well-structured MCP server that serves as a perfect template!
- [Cellpose team](https://github.com/MouseLand/cellpose) for the excellent segmentation library
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [Anthropic](https://www.anthropic.com/) for Claude and MCP development

---

**Built with ❤️ for the microscopy and AI communities**

**This project is open source and free to fork, modify, and experiment with. Feel free to use it as a starting point for your own MCP servers!**
