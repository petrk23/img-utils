Image processing utilities
==========================
This project is a collection of standalone image processing scripts
written in Python.

Image median
-----------
The script `img_median.py` takes input images, stacks them as layers
and computes median across the layers of the image stack (Z-axis)
for every pixel position.

See script [documentation](doc/img_median.md).

Image offset
------------
The script `img_offset.py` uses phase correlation to calculate the
translation of images in a stack relative to a single anchor image.
It does not modify the images but only finds the offsets.

See script [documentation](doc/img_offset.md).

Dependencies
------------
* Modern Python version (>=3.12).
* `numpy` as math engine.
* `tifffile` with `imagecodecs` to read compressed TIFFs.

Install them with `pip install -r requirements.txt`, or any package
manager you like. Best practice is to do that in an independent Python
virtual environment (venv).

No other, usually heavyweight, image processing packages are needed!

License
-------
BSD-3-Clause license. See the [LICENSE](LICENSE) file for full text.
