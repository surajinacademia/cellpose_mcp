"""Segment image with cpsam model and display in GUI."""

import os

# Fix OpenMP threading conflicts
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
from pathlib import Path
from cellpose import io, models, utils
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.patches as mpatches

# Load image
image_path = "demo_images/img00.png"
img = io.imread(image_path)

print(f"Image shape: {img.shape}")
print(f"Image dtype: {img.dtype}")

# Initialize cpsam model
print("Loading cpsam model...")
model = models.CellposeModel(gpu=False, model_type="cpsam")

# Run segmentation
# Image has blue (nuclei) and green (cytoplasm) channels
print("Segmenting cells...")
result = model.eval(
    img,
    diameter=None,  # Auto-estimate
    channels=[0, 1],  # First channel (blue=nuclei), second channel (green=cyto)
    flow_threshold=0.4,
    cellprob_threshold=0.0,
    min_size=15,
    augment=False,
    normalize=True,
    invert=False,
)

# Handle Cellpose v4 API - returns 3 values (masks, flows, diams)
if isinstance(result, tuple):
    if len(result) == 3:
        masks, flows, diams = result
    elif len(result) == 4:
        masks, flows, styles, diams = result
    else:
        raise ValueError(f"Unexpected number of return values: {len(result)}")
else:
    masks = result
    flows = None
    diams = None

# Count cells
n_cells = len(np.unique(masks)) - 1
diameter_used = float(diams) if isinstance(diams, (int, float, np.number)) else float(diams[0]) if diams is not None else 0.0

print(f"Segmentation complete!")
print(f"Cells detected: {n_cells}")
print(f"Diameter used: {diameter_used:.2f} pixels")

# Save masks
mask_path = Path(image_path).parent / f"{Path(image_path).stem}_masks.png"
io.imsave(str(mask_path), masks)
print(f"Mask saved to: {mask_path}")

# Create GUI display
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.suptitle(f"Cellpose Segmentation (cpsam model) - {n_cells} cells detected", fontsize=14, fontweight='bold')

# Display original image
ax1 = axes[0]
if img.ndim == 3 and img.shape[2] >= 3:
    # RGB or multi-channel image
    display_img = img[:, :, :3] if img.shape[2] >= 3 else img
    # Normalize to 0-1 range
    display_img = display_img.astype(np.float32)
    display_img = (display_img - display_img.min()) / (display_img.max() - display_img.min() + 1e-8)
    ax1.imshow(display_img)
else:
    ax1.imshow(img, cmap='gray')
ax1.set_title("Original Image", fontsize=12)
ax1.axis('off')

# Display image with mask overlay
ax2 = axes[1]
if img.ndim == 3 and img.shape[2] >= 3:
    display_img = img[:, :, :3] if img.shape[2] >= 3 else img
    display_img = display_img.astype(np.float32)
    display_img = (display_img - display_img.min()) / (display_img.max() - display_img.min() + 1e-8)
    ax2.imshow(display_img)
else:
    ax2.imshow(img, cmap='gray')

# Overlay mask outlines
outlines = utils.outlines_list(masks)
for outline in outlines:
    ax2.plot(outline[:, 0], outline[:, 1], 'r-', linewidth=1.5, alpha=0.8)

ax2.set_title(f"Segmentation Overlay ({n_cells} cells)", fontsize=12)
ax2.axis('off')

# Add legend
legend_elements = [
    mpatches.Patch(facecolor='none', edgecolor='red', linewidth=1.5, label='Cell boundaries'),
]
ax2.legend(handles=legend_elements, loc='upper right', fontsize=10)

plt.tight_layout()
plt.show()

print("GUI displayed. Close the window when done.")
