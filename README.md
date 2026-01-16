# Cellpose MCP Server

🔬 MCP server for AI-powered Cellpose cell segmentation. Connect Claude, ChatGPT, Cursor, and other LLMs to Cellpose for automated cell segmentation workflows. Perfect for microscopy image analysis and building intelligent segmentation tools.

## 🚀 Quick Start (3 Steps)

### 1. Install the Package

```shell
# Activate your conda environment (e.g., image_analysis)
conda activate image_analysis

# Install cellpose-mcp
pip install cellpose-mcp

# OR for development:
git clone https://github.com/yourusername/cellpose-mcp.git
cd cellpose-mcp
pip install -e .
```

### 2. Auto-Configure Your AI Application

```shell
# For Cursor IDE
cellpose-mcp-install cursor

# For other applications
cellpose-mcp-install --help  # See all options
```

### 3. Restart Your Application & Start Using

Restart your AI app and you're ready! Try asking:

```
"Can you list available Cellpose models?"
"Segment the cells in ./data/sample.tif using the cyto2 model"
```

## 📦 Installation for Cursor IDE

### Prerequisites

- **Conda installed** (Anaconda or Miniconda)
- **`image_analysis` conda environment** with Cellpose installed
- **Cursor IDE** installed

### Step-by-Step Installation

1. **Activate your conda environment:**
   ```bash
   conda activate image_analysis
   ```

2. **Install Cellpose (if not already installed):**
   ```bash
   pip install cellpose
   ```

3. **Install cellpose-mcp:**
   ```bash
   pip install cellpose-mcp
   # OR for development:
   pip install -e .
   ```

4. **Auto-configure for Cursor:**
   ```bash
   cellpose-mcp-install cursor
   ```

   This will:
   - Auto-detect your `image_analysis` conda environment
   - Find the Cursor configuration file
   - Add cellpose-mcp to your MCP servers

5. **Restart Cursor IDE**

6. **Verify installation:**
   Ask your AI assistant: `"List available Cellpose models"`

### Manual Configuration (if auto-installer fails)

If the auto-installer doesn't work, manually add to Cursor's MCP settings:

**macOS:**
```json
{
  "mcpServers": {
    "cellpose": {
      "command": "/path/to/miniconda3/envs/image_analysis/bin/python",
      "args": ["-m", "cellpose_mcp"]
    }
  }
}
```

Location: `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`

**Linux:**
Location: `~/.config/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`

**Windows:**
Location: `%APPDATA%\Cursor\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json`

## 🎯 Capabilities & Features

### 2D Cell Segmentation
- Segment cells in 2D microscopy images
- Support for multiple model types (cyto, cyto2, cyto3, nuclei, etc.)
- Automatic diameter estimation
- Customizable thresholds and parameters

### 3D Cell Segmentation
- Full 3D volume segmentation
- Slice + stitch approach for anisotropic data
- Anisotropy correction
- Support for 3D/4D image stacks

### Image Restoration (Cellpose3)
- **Denoising**: Remove noise from microscopy images
- **Deblurring**: Correct motion blur and focus issues
- **Upsampling**: Increase image resolution
- **One-click**: Combined restoration + segmentation pipeline

### Model Training
- Train custom segmentation models
- Train restoration models
- Support for custom datasets
- Checkpoint management

### Batch Processing
- Process multiple images in batch
- Parallel processing support
- Progress tracking

### Utility Functions
- List available models
- Estimate cell diameter
- Save masks in various formats
- Image metadata extraction

## 🛠 Available MCP Tools

The server exposes 13+ tools for complete Cellpose functionality:

### Segmentation Tools

- **`segment_cells_2d`** - Segment cells in 2D images
  - Parameters: `image_path`, `model_type`, `diameter`, `channels`, `flow_threshold`, `cellprob_threshold`, `gpu`, etc.
  - Returns: `cells_detected`, `output_path`, `diameter`, `mask_shape`

- **`segment_cells_3d`** - Segment cells in 3D volumes
  - Parameters: `image_path`, `model_type`, `do_3d`, `anisotropy`, `stitch_threshold`, etc.
  - Returns: `cells_detected`, `output_path`, `volume_shape`, `anisotropy_used`

- **`segment_cells_batch`** - Batch process multiple images
  - Parameters: `image_paths`, `model_type`, `output_dir`, `batch_size`
  - Returns: `total_images`, `successful`, `failed`, `results`

### Image Restoration Tools

- **`denoise_image`** - Denoise microscopy images
  - Parameters: `image_path`, `model_type`, `channels`, `diameter`
  - Returns: `output_path`, `noise_reduction_estimate`

- **`deblur_image`** - Deblur microscopy images
  - Parameters: `image_path`, `model_type`, `channels`, `diameter`
  - Returns: `output_path`, `blur_reduction_estimate`

- **`upsample_image`** - Upsample low-resolution images
  - Parameters: `image_path`, `model_type`, `scale_factor`, `channels`
  - Returns: `output_path`, `original_shape`, `upsampled_shape`

- **`restore_and_segment`** - Combined restoration + segmentation
  - Parameters: `image_path`, `restoration_model`, `segmentation_model`, `diameter`
  - Returns: `cells_detected`, `mask_path`, `restored_image_path`

### Training Tools

- **`train_segmentation_model`** - Train custom segmentation model
  - Parameters: `train_dir`, `train_labels_dir`, `model_name`, `n_epochs`, `learning_rate`
  - Returns: `model_path`, `training_images`, `test_images`, `status`

- **`train_restoration_model`** - Train custom restoration model
  - Parameters: `train_dir`, `model_name`, `restoration_type`, `n_epochs`
  - Returns: `model_path`, `status`

### Utility Tools

- **`list_available_models`** - List all pretrained models
  - Returns: `segmentation_models`, `restoration_models`, `all_models`

- **`estimate_cell_diameter`** - Estimate cell diameter from image
  - Parameters: `image_path`, `model_type`
  - Returns: `estimated_diameter`, `confidence`

- **`save_masks`** - Save masks in various formats
  - Parameters: `mask_path`, `output_format`, `save_outlines`, `save_flows`
  - Returns: `output_path`, `files_created`

- **`load_image_info`** - Get image metadata
  - Parameters: `image_path`
  - Returns: `shape`, `dtype`, `channels`, `is_3d`, `is_4d`

## 📖 Usage Examples

### Basic 2D Segmentation

```
"Segment the cells in ./data/microscopy_image.tif using the cyto2 model"
```

### 3D Volume Segmentation

```
"Segment the 3D volume in ./data/volume.tif with anisotropy factor 2.5"
```

### Image Restoration + Segmentation

```
"Restore and segment the noisy image in ./data/noisy.tif using oneclick_cyto3"
```

### Batch Processing

```
"Segment all TIFF files in ./data/images/ and save masks to ./output/"
```

### Training Custom Model

```
"Train a segmentation model using images in ./train/images/ and masks in ./train/masks/ with 200 epochs"
```

## 🤖 Supported AI Applications

| Application | Command | Status |
|------------|---------|--------|
| Cursor IDE | `cellpose-mcp-install cursor` | ✅ Full Support |
| Claude Desktop | `cellpose-mcp-install claude-desktop` | 🚧 Coming Soon |
| Claude Code | `cellpose-mcp-install claude-code` | 🚧 Coming Soon |
| Cline (VS Code) | `cellpose-mcp-install cline-vscode` | 🚧 Coming Soon |
| Cline (Cursor) | `cellpose-mcp-install cline-cursor` | 🚧 Coming Soon |

## 🏗 Architecture

```
┌─────────────────────────────────┐
│   AI Assistant (Cursor/Claude)  │
│   MCP Tools                      │
└───────────┬─────────────────────┘
            │
            │ MCP Protocol (JSON-RPC)
            ↓
┌─────────────────────────────────┐
│   Cellpose MCP Server           │
│   - FastMCP Server              │
│   - Tool Registration           │
│   - 13+ Tools                    │
└───────────┬─────────────────────┘
            │
            │ Python API calls
            ↓
┌─────────────────────────────────┐
│   Cellpose Library               │
│   - CellposeModel               │
│   - DenoiseModel                │
│   - CellposeDenoiseModel         │
│   - Training API                │
└───────────┬─────────────────────┘
            │
            │ Conda Environment
            ↓
┌─────────────────────────────────┐
│   image_analysis environment     │
│   Python 3.10+                   │
└─────────────────────────────────┘
```

## 🧪 Testing

Run the test script to verify installation:

```bash
python test_cellpose.py
```

This will check:
- ✅ Cellpose installation
- ✅ Required dependencies
- ✅ MCP server initialization
- ✅ Model loading

## 🛠 Development Setup

```shell
# Clone repository
git clone https://github.com/yourusername/cellpose-mcp.git
cd cellpose-mcp

# Activate conda environment
conda activate image_analysis

# Install in development mode
pip install -e ".[dev]"

# Run tests
python test_cellpose.py
```

## 📚 Resources

- [Cellpose Documentation](https://cellpose.readthedocs.io/) - Cellpose library docs
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [FastMCP](https://github.com/jlowin/fastmcp) - Python MCP framework
- [Cursor IDE](https://cursor.sh/) - AI-powered code editor

## ⚠️ Security Notice

This MCP server provides powerful image processing capabilities. Use only with trusted AI assistants on local networks. Never expose to the public internet without proper sandboxing.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

BSD 3-Clause License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Cellpose team](https://github.com/MouseLand/cellpose) for the excellent segmentation library
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [Napari MCP](https://github.com/royerlab/napari-mcp) for architectural inspiration
- [Anthropic](https://www.anthropic.com/) for Claude and MCP development

Built with ❤️ for the microscopy and AI communities.
