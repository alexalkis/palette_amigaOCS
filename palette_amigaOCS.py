#!/usr/bin/env python

#   Try to make the palette have 4-bit resolution per r,g,b
#   Inputs:
#       - Dithering
#       - Number of bitplanes
#
#   2018 Alex Argiropoulos
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gimpfu import *
import time
from array import array

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def palette_AmigaOCS(img, layer, dither, bp):
    gimp.progress_init("Processing" + layer.name + "...")
    pdb.gimp_undo_push_group_start(img)

    numcolors = 2**bp
    # Convert to for example 32 colors (if bp is 5)
    pdb.gimp_image_convert_indexed(img, dither, MAKE_PALETTE, numcolors, False, True, '')
    # Convert back to RGB (but having 32 distinct colors) so the loop that follows work
    pdb.gimp_image_convert_rgb(img)
    
    layername = "render " + layer.name

    # Create the new layer:
    srcWidth, srcHeight = layer.width, layer.height

    destDrawable = gimp.Layer(img, layername, srcWidth, srcHeight,
                              layer.type, layer.opacity, layer.mode)
    img.add_layer(destDrawable, 0)
    xoff, yoff = layer.offsets

    destDrawable.translate(xoff, yoff)

    srcRgn = layer.get_pixel_rgn(0, 0, srcWidth, srcHeight, False, False)
    src_pixels = array("B", srcRgn[0:srcWidth, 0:srcHeight])

    dstRgn = destDrawable.get_pixel_rgn(0, 0, srcWidth, srcHeight, True, True)
    p_size = len(srcRgn[0,0])
    dest_pixels = array("B", [0] * (srcWidth * srcHeight * p_size))

    # Finally, loop over the region:
    for x in xrange(0, srcWidth - 1) :
        for y in xrange(0, srcHeight) :
            src_pos = (x + srcWidth * y) * p_size
            dest_pos = src_pos

            newval = src_pixels[src_pos: src_pos + p_size]
            newval[0] = min((int(newval[0]+8)/16) * 16,255)
            newval[1] = min((int(newval[1]+8)/16) * 16,255)
            newval[2] = min((int(newval[2]+8)/16) * 16,255)
            dest_pixels[dest_pos : dest_pos + p_size] = newval

        progress = float(x)/layer.width
        if (int(progress * 100) % 200 == 0) :
            gimp.progress_update(progress)

    # Copy the whole array back to the pixel region:
    dstRgn[0:srcWidth, 0:srcHeight] = dest_pixels.tostring()

    
    
    destDrawable.flush()
    destDrawable.merge_shadow(True)
    destDrawable.update(0, 0, srcWidth,srcHeight)

    # Remove the old layer
    img.remove_layer(layer)
    #layer.visible = False

    pdb.gimp_selection_none(img)
    
    # Convert it back to numcolors.  Note dither is zero, cause the actual dither (whatever user chosed)
    #  happened at the first conversion
    pdb.gimp_image_convert_indexed(img, 0, MAKE_PALETTE, numcolors, False, True, '')
    pdb.gimp_image_undo_group_end(img)


register(
    "python-fu-palette_AmigaOCS",
    N_("Reducing color resolution to 4-bits per r,g,b"),
    "Simulates an Amiga OCS' palette",
    "Alex Argiropoulos",
    "Alex Argiropoulos",
    "2018",
    N_("Palette Amiga OCS..."),
    "RGB*",
    [
        (PF_IMAGE, "image",       "Input image", None),
        (PF_DRAWABLE, "drawable", "Input drawable", None),
        (PF_OPTION, "dither", _("Dither"), 0,
            [
                "None",
                "Floyd-Steinberg (normal)",
                "Floyd-Steinberg (reduced color bleeding)",
                "Positioned"
            ]),
        (PF_SPINNER, "bp",    _("Bitplanes "),    5, (1, 5, 1)),
    ],
    [],
    palette_AmigaOCS,
    menu=N_("<Image>/Filters/Render"),
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
