import bpy, os
from os import listdir
from os.path import isfile, join

class TLM_CV_Filtering:

    image_output_destination = ""

    def init(lightmap_dir, denoise=False):

        print("Beginning filtering for files: ")

        if denoise:
            file_ending = "_denoised.hdr"
        else:
            file_ending = "_baked.hdr"

        dirfiles = [f for f in listdir(lightmap_dir) if isfile(join(lightmap_dir, f))]

        for file in dirfiles:
            print(file)

            # if file.endswith(file_ending):
            #     print()
            #     baked_image_array.append(file)