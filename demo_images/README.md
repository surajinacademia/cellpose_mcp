# Demo Images for Cellpose MCP

This directory contains sample images for testing and demonstrating Cellpose MCP functionality.

## Available Images

### 1. sample_cells.png
- **Type**: PNG (grayscale)
- **Size**: ~445 KB
- **Description**: Real microscopy image of cells
- **Use case**: Basic 2D cell segmentation examples

### 2. sample_cells_annotated.png
- **Type**: PNG (RGB overlay)
- **Size**: ~1.6 MB
- **Description**: Annotated version showing segmentation results
- **Use case**: Reference for expected segmentation output

### 3. synthetic_cells.tif
- **Type**: TIFF (grayscale)
- **Size**: ~256 KB
- **Description**: Synthetically generated cell-like circular objects
- **Use case**: Quick testing and validation

### 4. synthetic_cells_rgb.png
- **Type**: PNG (RGB)
- **Size**: ~225 KB
- **Description**: RGB version of synthetic cells
- **Use case**: Testing RGB image segmentation

## Usage Examples

### Basic Segmentation

```text
"Segment the cells in demo_images/sample_cells.png using the cyto2 model"
```

### Batch Processing

```text
"Process all images in demo_images/ with the cyto2 model and save results to ./output/"
```

### Diameter Estimation

```text
"Estimate cell diameter from demo_images/sample_cells.png"
```

## Adding Your Own Images

You can add your own microscopy images to this directory:

- Supported formats: TIFF, PNG, JPG
- Recommended: 8-bit or 16-bit grayscale for cell segmentation
- RGB images are also supported but may require appropriate model selection

## Image Sources

- `sample_cells.png` and `sample_cells_annotated.png`: From project poster materials
- `synthetic_cells.tif` and `synthetic_cells_rgb.png`: Synthetically generated for testing
