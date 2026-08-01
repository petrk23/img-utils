Image offset calculation tool
=============================
The `img_offset.py` script uses phase correlation to calculate the
translation of images in a stack relative to a single anchor image.
It does not modify the images in any way. Only the registration is
done, which reveals the offsets between the images and anchor.

Usage
-----
```
python3 img_offset.py [options] anchor [remaining images]
```

It takes the first image as anchor image and calculates the offsets
to all remaining images.

We have two options that can be used independently:

_Hanning window_ is a mask (it's sort of a vignette) that will be
applied to all images. In the frequency domain, the opposite image
borders are connected, building a torus (or a donut if you like).
By applying it, we make the border connections continuous. This
should lead to more precise results.

_Gaussian preblur_ can be used to smooth out the fine noise, which
could fool the phase correlation algorithm. As we are already in the
frequency domain, we use the convolution theorem and apply the blur
very effectively.

See `python3 img_offset.py -h` for exact usage.

How to interpret the results
----------------------------
The script prints the results formatted to the standard output.

For every image, except the anchor, we get three numbers. The first
two are the found X and Y offsets. These resulting numbers mean how
to shift that particular image to align it with the anchor. Negative
correction means moving left/up and positive right/down.

The third number is the quality indicator, which tells us how good
the match is. In an ideal world, it should be `1.0`. Practically,
you will see something very close to this ideal for a good match.

Example output:
```
Processing anchor image 'anchor.tif'
Processing image 'shifted.tif':
  Offset x=0.21 y=-0.74
  Quality 1.1559
Processing image 'aligned.tif':
  Offset x=0.01 y=0.00
  Quality 1.0136
```

Limitations
-----------
* The script accepts only single-layer TIFF images.
* All input images must have the exact same size.
* Minimal Gaussian sigma is 0.1px. If it's lower, then the whole blur
  argument is ignored.
