#!/usr/bin/env python3
"""Create a side-by-side plot: original image (left) and segmented overlay (right)."""

import numpy as np
import matplotlib.pyplot as plt
from cellpose import io, utils
from pathlib import Path


def make_overlay(img, masks, alpha=0.35):
    """Blend colored cell masks and white outlines onto the original image."""
    overlay = img.copy().astype(np.float64)

    np.random.seed(42)
    n_cells = masks.max()
    colors = np.random.randint(50, 255, size=(n_cells + 1, 3)).astype(np.float64)
    colors[0] = [0, 0, 0]

    color_mask = colors[masks]
    for i in range(3):
        overlay[:, :, i] = np.where(
            masks > 0,
            overlay[:, :, i] * (1 - alpha) + color_mask[:, :, i] * alpha,
            overlay[:, :, i],
        )

    outlines = utils.masks_to_outlines(masks)
    overlay[outlines > 0] = [255, 255, 255]

    return np.clip(overlay, 0, 255).astype(np.uint8)


def main():
    img_path = "demo_images/img00.png"
    mask_path = "demo_images/img00_masks.png"

    img = io.imread(img_path)
    masks = io.imread(mask_path)
    overlay = make_overlay(img, masks)
    n_cells = masks.max()

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    axes[0].imshow(img)
    axes[0].set_title("Original Image", fontsize=14, fontweight="bold")
    axes[0].axis("off")

    axes[1].imshow(overlay)
    axes[1].set_title(f"Segmented Overlay ({n_cells} cells)", fontsize=14, fontweight="bold")
    axes[1].axis("off")

    plt.tight_layout()
    out = "demo_images/segmentation_comparison.png"
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
