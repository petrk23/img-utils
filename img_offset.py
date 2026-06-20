#!/usr/bin/env python3

# This script is part of image utils project
# https://github.com/petrk23/img-utils
# Copyright (c) 2026 Petr Krajník. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from typing  import Any, TypeGuard

import argparse
import functools
import numpy as np
import numpy.typing as npt
import sys
import tifffile

type ArrayU = npt.NDArray[np.unsignedinteger[Any]]
type ArrayF = npt.NDArray[np.floating[Any]]

type ImageF64 = npt.NDArray[np.float64]
type ImageFFT = npt.NDArray[np.complex128]
type ImageArray = ArrayU | ArrayF
type ImageShape = tuple[int, int]


def is_uint_array(arr: npt.NDArray[Any]) -> TypeGuard[ArrayU]:
    """Check if array type is any unsigned integer."""
    return np.issubdtype(arr.dtype, np.unsignedinteger)


def is_float_array(arr: npt.NDArray[Any]) -> TypeGuard[ArrayF]:
    """Check if array type is any float."""
    return np.issubdtype(arr.dtype, np.floating)


def normalize_values(img_array: ImageArray) -> ImageF64:
    """Normalize image to float64 values of 0.0-1.0."""
    if is_uint_array(img_array):
        type_max = np.iinfo(img_array.dtype).max
        return (img_array / type_max).astype(np.float64, copy=False)
    elif is_float_array(img_array):
        # Values unmodified, hdr support preserved
        return img_array.astype(np.float64, copy=False)
    raise ValueError(f"Unsupported image value type '{img_array.dtype}'")


def rgb_to_gray(img_array: ImageF64) -> ImageF64:
    """Convert RGB image to grayscale with normalization."""
    channel_count = img_array.shape[-1]
    if channel_count in (3, 4):  # RGB, RGBA
        img_rgb = img_array[..., :3]
        lum_weights = np.array([0.2989, 0.5870, 0.1140])
        img_gray: ImageF64 = np.matmul(img_rgb, lum_weights)
        return img_gray
    raise ValueError(f"Unsupported channel count {channel_count}")


def image_to_gray(img_array: ImageF64) -> ImageF64:
    """Convert image to grayscale with normalization."""
    if img_array.size == 0:
        raise ValueError("Empty image can't be converted")
    if img_array.ndim == 2:  # Already grayscale
        return img_array
    if img_array.ndim == 3:
        return rgb_to_gray(img_array)
    raise ValueError(
        f"Unsupported array dimensions: {img_array.ndim}. "
        "If you are using a TIFF hyperstack (e.g., Time, Z-stack, "
        "Channels, X, Y), slice the array to extract a 2D or 3D frame "
        "before passing it to this function.")


@functools.lru_cache(maxsize=2)
def get_hanning_mask(shape: ImageShape) -> ImageF64:
    """Generates a 2D Hanning window to reduce edge artifacts."""
    win_y = np.hanning(shape[0])
    win_x = np.hanning(shape[1])
    return np.outer(win_y, win_x)


@functools.lru_cache(maxsize=2)
def get_gaussian_rfft(shape: ImageShape, sigma: float) -> ImageF64:
    """Constructs a Gaussian filter in the frequency domain."""
    height, width = shape
    u = np.fft.fftfreq(height)
    v = np.fft.rfftfreq(width)
    U2 = u[:, np.newaxis] ** 2
    V2 = v[np.newaxis, :] ** 2
    return np.exp(-2 * np.pi**2 * sigma**2 * (U2 + V2))


def should_blur(blur_sigma: float) -> bool:
    """Indicates whether preblur should be applied."""
    return blur_sigma >= 0.1


def proc_error(filepath: Path, msg: str) -> None:
    print(f"ERROR processing '{filepath}': {msg}", file=sys.stderr)


def load_file_fft(
    filepath: Path, apply_hanning: bool, blur: float
) -> ImageFFT | None:
    """Loads an image, preprocesses it, and returns its FFT."""
    try:
        img = tifffile.imread(str(filepath))
        img = normalize_values(img)
        img = image_to_gray(img)
        if apply_hanning:
            img *= get_hanning_mask(img.shape)
        img_fft = np.fft.rfft2(img)  # To freq. domain switch
        if should_blur(blur):
            img_fft *= get_gaussian_rfft(img.shape, blur)
        return img_fft
    except Exception as e:
        proc_error(filepath, msg=f"{e}")
        return None


def unwrap_offset(offset: float, dimension: int) -> float:
    """Correct possibly wrapped phase correlation offset."""
    if offset >= (dimension / 2):
        offset = offset - dimension
    return offset


def get_subpixel_peak(
    corr_map: ImageF64, centroid_radius: int = 2
) -> tuple[float, float, float]:
    """Calculates subpixel shift of the peak with a centroid."""
    y_int, x_int = np.unravel_index(np.argmax(corr_map), corr_map.shape)

    # Generate centroid indices
    r_start, r_end = y_int - centroid_radius, y_int + centroid_radius + 1
    c_start, c_end = x_int - centroid_radius, x_int + centroid_radius + 1
    rows = np.arange(r_start, r_end)
    cols = np.arange(c_start, c_end)

    # Subregion under centroid with 'wrap' at borders
    sub_region = corr_map.take(rows, mode="wrap", axis=0)
    sub_region = sub_region.take(cols, mode="wrap", axis=1)
    sub_region = np.maximum(sub_region, 0)  # Clip negative numbers to zero

    # Create coordinate grids for the region
    yy, xx = np.mgrid[r_start:r_end, c_start:c_end]

    # Main centroid calculation
    total_intensity = np.sum(sub_region)
    y_sub = np.sum(yy * sub_region) / total_intensity
    x_sub = np.sum(xx * sub_region) / total_intensity

    # Wrap around correction
    y_sub = unwrap_offset(y_sub, corr_map.shape[0])
    x_sub = unwrap_offset(x_sub, corr_map.shape[1])

    return x_sub, y_sub, total_intensity


def phase_correlation(
    anchor_fft: ImageFFT, img_fft: ImageFFT
) -> tuple[float, float, float]:
    """Calculate phase correlation between anchor and img."""
    phase_diff = anchor_fft * np.conj(img_fft)
    norm = np.abs(phase_diff)
    norm += 1e-10  # prevent div by zero
    phase_diff /= norm
    corr_map = np.fft.irfft2(phase_diff)
    return get_subpixel_peak(corr_map)


def process_img(
    anchor_fft: ImageFFT, img_path: Path, apply_hanning: bool, blur: float
) -> None:
    """Calculate offset of image relative to anchor."""
    print(f"Processing image '{img_path}':")
    img_fft = load_file_fft(img_path, apply_hanning, blur)
    if img_fft is not None:
        if img_fft.shape == anchor_fft.shape:
            s, t, q = phase_correlation(anchor_fft, img_fft)
            print(f"  Offset x={s:.2f} y={t:.2f}")
            print(f"  Quality {q:.4f}")
        else:
            proc_error(img_path, "Image dimensions mismatch with anchor")
        del img_fft


def find_offsets(args: argparse.Namespace) -> None:
    """Entry function for the phase correlation offset search."""
    print(f"Processing anchor image '{args.anchor}'")
    anchor_fft = load_file_fft(args.anchor, args.apply_hanning, args.blur)
    if anchor_fft is not None:
        for img_path in args.images:
            process_img(anchor_fft, img_path, args.apply_hanning, args.blur)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Image offset calculation relative to anchor",
        epilog="See project 'README.md' for additional information.")
    parser.add_argument(
        "-b", "--blur", type=float, default=0.0,
        help="preblur Gaussian sigma to reduce impact of noise")
    parser.add_argument(
        "-m", "--hann", action="store_true", dest="apply_hanning",
        help="apply Hanning mask to clean edges")
    parser.add_argument(
        "anchor", type=Path, help="anchor image used as reference")
    parser.add_argument(
        "images", type=Path, nargs="+",
        help="other images to be compared to anchor")
    args = parser.parse_args()

    if args.apply_hanning:
        print("Hanning window used")
    if should_blur(args.blur):
        print(f"Gaussian preblur with sigma={args.blur}px")
    find_offsets(args)
