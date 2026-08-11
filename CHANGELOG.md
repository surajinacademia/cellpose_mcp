# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-08-10

### Added

- A JSON command-line interface, `cellpose-mcp-cli`, backed by the same operations as the MCP server.
- Focused regression coverage for 2D and 3D segmentation, restoration, batch processing, CLI behavior, installer safety, and distribution contents.

### Security

- Reject `.npy` inputs before they reach Cellpose's pickle-enabled reader.
- Restrict model arguments to 23 curated pretrained identifiers, preventing model fields from being interpreted as local paths.
- Replace Cellpose's certificate-bypassing downloader with verified HTTPS, an official-host allowlist, redirect validation, a size limit, and atomic publication.
- Resolve installer Python commands to absolute executables and verify installed metadata in isolated mode.
- Refuse malformed or symlinked MCP configuration targets; publish valid JSON/TOML atomically with private permissions.

### Changed

- Keep a focused set of 11 shared operations across CLI and MCP, including 3D segmentation and restoration.
- Support Python 3.11 and 3.12 and pin Cellpose to the restoration-compatible `3.1.1.1` release.
- Make CI and pre-commit checks fail closed against the active code and test suite.

### Removed

- Custom model training operations.
- The stale feature-manifest release gate and its packaging surface.
- The tracked machine-specific `.mcp.json` configuration.

## [0.1.4] - 2026-04-11

### Fixed

- FastMCP compatibility when tool decorators do not expose ``.fn`` on the wrapped callable (import-time crash under `uv run` / recent FastMCP versions).
- ``cellpose_mcp.server`` now re-exports ``mcp`` so ``import cellpose_mcp`` and the CLI entry point resolve the shared FastMCP instance.

### Added

- GitHub Actions workflow (Ruff + pytest on Python 3.10–3.12).
- Smoke tests for package import, ``mcp`` singleton identity, and tool unwrapping.

### Changed

- Pinned ``fastmcp`` to ``>=2.10.3,<3`` until the project is tested on FastMCP 3.x.

## [0.1.0] - 2026-02-10

### 🎉 First Release

This is the first stable release of **Cellpose-MCP**, a Model Context Protocol (MCP) server that enables AI assistants to perform Cellpose cell segmentation through natural language commands.

### Added

#### Core Functionality
- **11 MCP Tools** for focused Cellpose functionality:
  - `segment_cells_2d` - Segment cells in 2D images
  - `segment_cells_3d` - Segment cells in 3D volumes
  - `segment_cells_batch` - Batch process multiple images with parallel execution
  - `denoise_image` - Denoise microscopy images
  - `deblur_image` - Deblur microscopy images
  - `upsample_image` - Upsample low-resolution images
  - `restore_and_segment` - Combined restoration + segmentation
  - `list_available_models` - List 23 curated pretrained Cellpose models
  - `estimate_cell_diameter` - Estimate cell diameter from images
  - `save_masks` - Save masks in various formats
  - `load_image_info` - Get image metadata

#### Supported AI Applications
- ✅ **Cursor IDE** - Full support with auto-configuration
- ✅ **Claude Desktop** - Full support with auto-configuration
- ✅ **Claude Code** - Full support (manual or auto-config)
- ✅ **VS Code** - Full support via Cline/Roo Cline extension
- 🔄 **Antigravity** - Under development

#### Technical Highlights
- Thread-safe, async FastMCP backend for non-blocking operations
- Seamless integration with Napari for visualization workflows
- Support for multiple image formats (TIFF, PNG, NPY)
- 23 curated pretrained Cellpose models available
- GPU acceleration support enabled by default
- Auto-installation CLI tool (`cellpose-mcp-install`) for easy setup

#### Documentation
- Comprehensive README with quick start guide
- Detailed release notes (RELEASE_NOTES_v0.1.0.md)
- Research poster showcasing capabilities
- Demo images and segmentation examples

### Installation

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

### Requirements

- Python 3.10 or higher
- Cellpose 3.0+
- See [pyproject.toml](pyproject.toml) for complete dependency list

### Links

- **Repository**: https://github.com/surajinacademia/cellpose_mcp
- **Documentation**: [README.md](README.md)
- **Issues**: https://github.com/surajinacademia/cellpose_mcp/issues
- **Detailed Release Notes**: [RELEASE_NOTES_v0.1.0.md](RELEASE_NOTES_v0.1.0.md)

### Acknowledgments

This project was inspired by [napari-mcp](https://github.com/royerlab/napari-mcp) and builds upon the excellent [Cellpose](https://github.com/MouseLand/cellpose) segmentation library. Special thanks to:

- [Napari MCP](https://github.com/royerlab/napari-mcp) by royerlab
- [Cellpose](https://github.com/MouseLand/cellpose) team
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [Anthropic](https://www.anthropic.com/) for Claude and MCP development

---

## [0.1.3] - 2026-02-10

### Fixed

- Documentation links on PyPI now use full GitHub URLs so "Release Notes" and "Changelog" work correctly on the [PyPI project page](https://pypi.org/project/cellpose-mcp/).

### Changed

- README: Release Notes and Changelog links point to GitHub (e.g. `https://github.com/surajinacademia/cellpose_mcp/blob/main/CHANGELOG.md`).

---

## [0.1.2] - 2026-02-10

### Changed

- **License**: Added Cellpose/HHMI copyright acknowledgment to LICENSE for BSD-3-Clause compliance.
- LICENSE wording updated to use plural "copyright holders" / "their" where appropriate.

---

## [0.1.1] - 2026-02-10

### Fixed

- Images in README now display correctly on PyPI by using GitHub raw content URLs for poster and demo images.

### Added

- PyPI badge in README linking to [pypi.org/project/cellpose-mcp/](https://pypi.org/project/cellpose-mcp/).

---

[0.1.0]: https://github.com/surajinacademia/cellpose_mcp/releases/tag/v0.1.0
[0.1.1]: https://github.com/surajinacademia/cellpose_mcp/releases/tag/v0.1.1
[0.1.2]: https://github.com/surajinacademia/cellpose_mcp/releases/tag/v0.1.2
[0.1.3]: https://github.com/surajinacademia/cellpose_mcp/releases/tag/v0.1.3
[0.1.4]: https://github.com/surajinacademia/cellpose_mcp/releases/tag/v0.1.4
[0.1.5]: https://github.com/surajinacademia/cellpose_mcp/releases/tag/v0.1.5
