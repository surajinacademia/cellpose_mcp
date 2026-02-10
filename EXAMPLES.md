# Cellpose MCP - New Features Example Workflow

This document demonstrates how to use the new features for pipeline documentation, verification, CellProfiler integration, and package management.

## Overview of New Features

The Cellpose MCP server now includes 25+ tools with the following new capabilities:

1. **Pipeline Skills & Documentation** (5 tools)
2. **CellProfiler Integration** (4 tools)
3. **Package Management** (4 tools)

## Example Workflow 1: Complete Cell Analysis with Documentation

### Step 1: Segment Cells

```text
"Segment the cells in ./data/sample.tif using the cyto2 model with diameter 30"
```

### Step 2: Verify Segmentation Results

```text
"Verify the segmentation results in ./data/sample_masks.tif against the original image ./data/sample.tif. 
Expected cell count is around 150, minimum cell size is 10 pixels."
```

This will generate a verification report showing:
- Total cells detected
- Average/median/min/max cell sizes
- Cell size variability
- Validation warnings and errors

### Step 3: Create Pipeline Summary

```text
"Create a pipeline summary document that includes:
- Step 1: Segmentation with cyto2 model (diameter=30)
- Step 2: Verification with min_cell_size=10

Save the summary to ./results/analysis_summary.md"
```

### Step 4: Save Pipeline Memory

```text
"Save the pipeline memory with ID 'experiment_001' including:
- Image source: ./data/sample.tif
- Model: cyto2
- Parameters used
- Results: 142 cells detected"
```

## Example Workflow 2: CellProfiler Integration

### Step 1: Segment with Cellpose

```text
"Segment all images in ./data/images/ using cyto2 model and save masks to ./data/masks/"
```

### Step 2: Check CellProfiler Availability

```text
"Check if CellProfiler is available"
```

### Step 3: Import Cellpose Masks to CellProfiler

```text
"Import Cellpose masks from ./data/masks/ into CellProfiler format"
```

### Step 4: Run CellProfiler Pipeline

```text
"Run the CellProfiler pipeline ./pipelines/measure_cells.cppipe on images in ./data/images/ 
with output to ./results/cellprofiler_output/"
```

### Step 5: Export Measurements

```text
"Export CellProfiler measurements from ./results/cellprofiler_output/ in CSV format"
```

## Example Workflow 3: Dynamic Package Management

### Check Available Packages

```text
"List all packages that can be installed for image processing"
```

This shows a whitelist of approved packages including:
- scikit-image
- opencv-python
- pillow
- scipy
- pandas
- matplotlib
- seaborn
- napari
- cellprofiler

### Install a Package

```text
"Install scikit-image package for additional image processing capabilities"
```

### Verify Installation

```text
"Check if scikit-image is installed"
```

## Example Workflow 4: Complete Reproducible Analysis

This workflow demonstrates a complete, documented, and reproducible analysis pipeline.

### 1. Initial Setup

```text
"Check if opencv-python is installed. If not, install it."
```

### 2. Image Preprocessing (if needed)

```text
"Denoise the image ./data/noisy_image.tif and save to ./data/denoised.tif"
```

### 3. Cell Segmentation

```text
"Segment cells in ./data/denoised.tif using cyto2 model with auto-estimated diameter"
```

### 4. Quality Verification

```text
"Verify the segmentation results with:
- minimum cell size: 15 pixels
- maximum cell size: 1000 pixels
Generate a verification report at ./results/verification_report.md"
```

### 5. Advanced Analysis with CellProfiler

```text
"Import the Cellpose masks to CellProfiler and run the measurement pipeline 
./pipelines/cell_morphology.cppipe"
```

### 6. Documentation

```text
"Create a comprehensive pipeline summary that includes:
- Denoising step
- Segmentation parameters
- Verification results
- CellProfiler measurements

Save to ./results/complete_analysis_summary.md"
```

### 7. Save for Reproducibility

```text
"Save the complete pipeline memory with ID 'morphology_analysis_2024_01' including:
- All parameters used
- Processing steps
- Results and metrics
- File paths

Save to ./pipeline_memory/"
```

### 8. Later: Reproduce Analysis

```text
"Load the analysis memory for 'morphology_analysis_2024_01' and show me the parameters 
that were used"
```

## Key Benefits

### 1. Documentation
- Automatically generate detailed markdown summaries of your analysis
- Track all parameters and steps
- Create reproducible research records

### 2. Verification
- Automated quality checks on segmentation results
- Calculate comprehensive cell metrics
- Identify potential issues early

### 3. Memory/Logging
- Save pipeline execution history
- Enable reproducibility
- Track experiments over time

### 4. CellProfiler Integration
- Seamlessly bridge Cellpose segmentation with CellProfiler measurements
- Use the best of both tools
- Extend capabilities beyond basic segmentation

### 5. Package Management
- Install additional image processing libraries as needed
- Whitelist ensures security
- Expand capabilities on-demand

## Security Features

The package management system includes:
- **Whitelist approach**: Only approved packages can be installed
- **Version control**: Specific versions can be requested
- **Safe defaults**: No arbitrary code execution

## Tips for Best Results

1. **Always verify**: Use verification tools after segmentation to catch issues early
2. **Document as you go**: Create summaries at major milestones
3. **Save memory**: Store pipeline parameters for reproducibility
4. **Use CellProfiler**: For measurements beyond basic cell counting
5. **Install packages proactively**: Get the tools you need before starting analysis

## Example Natural Language Prompts

Here are examples of how to ask an AI assistant to use these features:

```text
"I need to analyze a batch of microscopy images. First, check if opencv-python is installed. 
Then segment all TIFF files in ./data/ using the cyto2 model. After that, verify each 
segmentation with minimum cell size of 20 pixels and create a summary report."
```

```text
"Load the pipeline memory from experiment 'batch_002', use those same parameters to segment 
new images in ./new_data/, verify the results, and save as experiment 'batch_003'."
```

```text
"Segment cells, import masks to CellProfiler, run the measurement pipeline, then create a 
comprehensive summary document that includes all steps and results."
```

## Next Steps

1. Start the MCP server: `cellpose-mcp`
2. Connect your AI assistant (Claude, Cursor, etc.)
3. Try the example workflows above
4. Explore the 25+ available tools
5. Build your own custom analysis pipelines

For more information, see:
- README.md - Complete tool list and installation
- CLAUDE.md - Developer guide and architecture
- GitHub Issues - Report bugs or request features
