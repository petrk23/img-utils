Image median tool
=================
The script `img_median.py` takes input images, stacks them as layers
and computes median across the layers of the image stack (Z-axis)
for every pixel position. Minimum 3 valid input images are required.
All input images must have the same size, channel count, pixel bit
depth and data type. Therefore no conversions must be done and the
median only picks unmodified values from the input images.

Usage
-----
```
python3 img_median.py [options] img1 img2 img3 [remaining images]
```

Running the line above calculates median of all images given on the
command line and stores the resulting median image as `median.tif`
in the current working directory.

Output file path can be set with the `-o` or `--output` option.

See `python3 img_median.py -h` for exact usage.

Limitations
-----------
* Works only with single-layer TIFF images.
* All input images must have exact the same shape and data type.
* Minimum 3 images needed.
