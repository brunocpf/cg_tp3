import array
from geometry import clamp
import itertools


def export_ppm(filename, image_data, width, height, max_val):
    print("Exporting...")

    ppm_header = 'P6 ' + str(width) + ' ' + \
        str(height) + ' ' + str(max_val) + '\n'
    image = array.array('B', [0, 0, 0] * width * height)


    for (x, y), (red, green, blue) in image_data:
        mirrored_x = x
        image[(mirrored_x * 3 + 0) + width * 3 * y] = clamp(0, red, max_val)
        image[(mirrored_x * 3 + 1) + width * 3 * y] = clamp(0, green, max_val)
        image[(mirrored_x * 3 + 2) + width * 3 * y] = clamp(0, blue, max_val)

    with open(filename, 'wb') as f:
        f.write(bytearray(ppm_header, 'ascii'))
        image.tofile(f)


def import_ppm(filename):
    return []
