#!/usr/bin/python3

import argparse
from ppm import export_ppm
from scene_3d import *


def main():
    input_filename = args["filename"]
    output_filename = args["output"]
    width, height = tuple(map(int, args["dims"]))
    camera, ambient_light, lights, objs = parse_input_data(input_filename)
    scene = Scene(camera, ambient_light, lights, objs)
    image_data = scene.render_image(width, height)
    export_ppm(output_filename, image_data, width, height, 255)


ap = argparse.ArgumentParser()
ap.add_argument("-f", "--filename", required=True,
                help="path to the input file")
ap.add_argument("-o", "--output", required=True,
                help="path to the output (.ppm) file")
ap.add_argument("-d", "--dims", required=False, nargs=2, default=["800", "600"],
                help="dimensions (width and height) of the output image (default: 800x600)")
args = vars(ap.parse_args())


# Call main function
if __name__ == "__main__":
    main()
