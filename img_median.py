#!/usr/bin/env python3

# This script is part of image utils project
# https://github.com/petrk23/img-utils
# Copyright (c) 2026 Petr Krajník. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import sys
from pathlib import Path

import numpy as np
import tifffile


def print_err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def load_images(img_paths: list[Path]) -> list[np.ndarray]:
    """Load input images as a list."""
    img_count = len(img_paths)
    ref_shape = None
    ref_dtype = None
    images = []
    for img_index, path in enumerate(img_paths, start=1):
        print(f"Loading image {img_index}/{img_count} '{path}'")
        try:
            img = tifffile.imread(path)
            if ref_shape is None:
                ref_shape = img.shape
                ref_dtype = img.dtype
                images.append(img)
            elif img.shape != ref_shape:
                print_err(
                    f"Skipped '{path}': Dimensions {img.shape} do not "
                    f"match reference {ref_shape}.")
            elif img.dtype != ref_dtype:
                print_err(
                    f"Skipped '{path}': Data type {img.dtype} does not "
                    f"match reference {ref_dtype}.")
            else:
                images.append(img)
        except (OSError, ValueError, NotImplementedError) as e:
            print_err(f"Failed to read '{path}': {e}")
    return images


def write_output_image(out_path: Path, image: np.ndarray) -> None:
    try:
        tifffile.imwrite(out_path, image)
        print(f"Median image saved to '{out_path}'")
    except (OSError, ValueError) as e:
        print_err(f"Failed to write '{out_path}': {e}")
        sys.exit(1)


def median_images(img_paths: list[Path], output: Path) -> None:
    """Load files, calculate median, and write the result."""
    images = load_images(img_paths)

    if len(images) < 3:
        print_err("Minimum of 3 valid images required.")
        sys.exit(1)

    print(f"Running median on {len(images)} images, this may take a while...")
    image_stack = np.stack(images, axis=0)
    median = np.median(image_stack, axis=0).astype(image_stack.dtype)

    write_output_image(output, median)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculation of median from TIFF image stack",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-o", "--output", type=Path, default="median.tif",
        help="Output median TIFF image storage path")
    parser.add_argument(
        "images", type=Path, nargs="+",
        help="Input TIFF images for the stack (minimum 3 required)")
    args = parser.parse_args()

    if len(args.images) < 3:
        parser.error("Too few input images provided. Minimum is 3.")

    median_images(args.images, args.output)
