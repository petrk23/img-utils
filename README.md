Image processing utilities
==========================
This project is a collection of standalone image processing scripts
written in Python.

Image median
-----------
Takes input images as a stack and compute median for every pixel.
Minimum 3 valid input images are required. All input images must have
the same size, channel count, pixel bit depth and data type.

Basic usage:
```
python3 img_median.py data/*.tif
```
This does median from the data directory images and stores the output
to a file named `median.tif` in the current working directory.

Image offset
------------
Uses phase correlation to calculate translation of images in a stack
relative to a single anchor image. It does not modify the images, but
only find the offsets.

For more info see scripts own
[repository](https://github.com/petrk23/img-offset).

Basic usage:
```
python3 img_offset data/*.tif
```
It takes the first image as anchor image and calculates offset to all
remaining images in the data directory.

Dependencies
------------
* Modern Python version (>=3.12).
* `numpy` as math engine.
* `tifffile` with `imagecodecs` to read compressed TIFFs.

Install them with `pip install -r requirements.txt`, or any package
manager you like. Best practice is to do that in an independent Python
virtual environment (venv).

No other, usually heavyweight, image processing packages needed!

Limitations
-----------
* The scripts accepts only single-layer TIFF images.

License
-------
BSD-3-Clause license. See the `LICENSE` file for full text.
