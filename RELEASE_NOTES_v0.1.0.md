# 🎉 Cellpose-MCP v0.1.0 - First Release

We're excited to announce the first stable release of **Cellpose-MCP**, a Model Context Protocol (MCP) server that enables AI assistants to perform Cellpose cell segmentation through natural language commands.

## ✨ What's New

This initial release provides a complete MCP server implementation for Cellpose, enabling AI assistants like Claude, Cursor IDE, and others to perform sophisticated cell segmentation workflows through conversational interfaces.

## 🚀 Features

### Core Functionality
- **13+ MCP Tools** for comprehensive Cellpose functionality:
  - 2D and 3D cell segmentation
  - Batch processing with parallel execution
  - Image restoration (denoising, deblurring, upsampling)
  - Custom model training for segmentation and restoration
  - Utility tools for model management and image analysis

### Supported AI Applications
- ✅ **Cursor IDE** - Full support with auto-configuration
- ✅ **Claude Desktop** - Full support with auto-configuration
- ✅ **Claude Code** - Full support (manual or auto-config)
- ✅ **VS Code** - Full support via Cline/Roo Cline extension
- 🔄 **Antigravity** - Under development

### Technical Highlights
- Thread-safe, async FastMCP backend for non-blocking operations
- Seamless integration with Napari for visualization workflows
- Support for multiple image formats (TIFF, PNG, NPY)
- 19 pretrained Cellpose models available
- GPU acceleration support enabled by default

## 📦 Installation

```bash
pip install cellpose-mcp
```

### Quick Setup

After installation, configure your AI application:

```bash
# For Cursor IDE
cellpose-mcp-install cursor

# For Claude Desktop
cellpose-mcp-install claude-desktop

# For VS Code
cellpose-mcp-install vscode

# For other applications
cellpose-mcp-install --help
```

## 📋 Requirements

- Python 3.10 or higher
- Cellpose 3.0+
- See [pyproject.toml](https://github.com/surajinacademia/cellpose_mcp/blob/main/pyproject.toml) for complete dependency list

## 🔗 Links

- **Repository**: https://github.com/surajinacademia/cellpose_mcp
- **Documentation**: [README.md](https://github.com/surajinacademia/cellpose_mcp#readme)
- **Issues**: https://github.com/surajinacademia/cellpose_mcp/issues

## 🙏 Acknowledgments

This project was inspired by [napari-mcp](https://github.com/royerlab/napari-mcp) and builds upon the excellent [Cellpose](https://github.com/MouseLand/cellpose) segmentation library. Special thanks to:

- [Napari MCP](https://github.com/royerlab/napari-mcp) by royerlab
- [Cellpose](https://github.com/MouseLand/cellpose) team
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [Anthropic](https://www.anthropic.com/) for Claude and MCP development

## 📝 Example Usage

After installation and configuration, try asking your AI assistant:

```
"Can you list available Cellpose models?"
"Segment the cells in ./data/sample.tif using the cyto2 model"
"Process all images in ./data/ with the cyto2 model and save results to ./output/"
```

---

**Full Changelog**: https://github.com/surajinacademia/cellpose_mcp/compare/2582078...v0.1.0
