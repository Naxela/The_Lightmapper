import bpy, os, time, cv2

class TLM_ImageUpscale(bpy.types.Operator):
    bl_idname = "tlm.image_upscale"
    bl_label = "Upscale image"
    bl_description = "Upscales the image to double resolution"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):

        for area in bpy.context.screen.areas:
            if area.type == "IMAGE_EDITOR":
                active_image = area.spaces.active.image

        if active_image.source == "FILE":
            img_path = active_image.filepath_raw
            filename = os.path.basename(img_path)

            basename = os.path.splitext(filename)[0]
            extension = os.path.splitext(filename)[1]

            size_x = active_image.size[0]
            size_y = active_image.size[1]

            dir_path = os.path.dirname(os.path.realpath(img_path))

            #newfile = os.path.join(dir_path, basename + "_" + str(size_x) + "_" + str(size_y) + extension)
            newfile = os.path.join(dir_path, basename + extension)
            os.rename(img_path, newfile)

            basefile = cv2.imread(newfile, cv2.IMREAD_UNCHANGED)

            scale_percent = 200 # percent of original size
            width = int(basefile.shape[1] * scale_percent / 100)
            height = int(basefile.shape[0] * scale_percent / 100)
            dim = (width, height)

            if active_image.TLM_ImageProperties.tlm_image_scale_method == "Nearest":
                interp = cv2.INTER_NEAREST
            elif active_image.TLM_ImageProperties.tlm_image_scale_method == "Area":
                interp = cv2.INTER_AREA
            elif active_image.TLM_ImageProperties.tlm_image_scale_method == "Linear":
                interp = cv2.INTER_LINEAR
            elif active_image.TLM_ImageProperties.tlm_image_scale_method == "Cubic":
                interp = cv2.INTER_CUBIC
            elif active_image.TLM_ImageProperties.tlm_image_scale_method == "Lanczos":
                interp = cv2.INTER_LANCZOS4

            resized = cv2.resize(basefile, dim, interpolation = interp)

            #resizedFile = os.path.join(dir_path, basename + "_" + str(width) + "_" + str(height) + extension)
            resizedFile = os.path.join(dir_path, basename + extension)

            cv2.imwrite(resizedFile, resized)

            active_image.filepath_raw = resizedFile
            bpy.ops.image.reload()

            print(newfile)
            print(img_path)
        
        else:

            print("Please save image")

        print("Upscale")

        return {'RUNNING_MODAL'}

class TLM_ImageDownscale(bpy.types.Operator):
    bl_idname = "tlm.image_downscale"
    bl_label = "Downscale image"
    bl_description = "Downscales the image to double resolution"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):

        for area in bpy.context.screen.areas:
            if area.type == "IMAGE_EDITOR":
                active_image = area.spaces.active.image

        if active_image.source == "FILE":
            img_path = active_image.filepath_raw
            filename = os.path.basename(img_path)

            basename = os.path.splitext(filename)[0]
            extension = os.path.splitext(filename)[1]

            size_x = active_image.size[0]
            size_y = active_image.size[1]

            dir_path = os.path.dirname(os.path.realpath(img_path))

            #newfile = os.path.join(dir_path, basename + "_" + str(size_x) + "_" + str(size_y) + extension)
            newfile = os.path.join(dir_path, basename + extension)
            os.rename(img_path, newfile)

            basefile = cv2.imread(newfile, cv2.IMREAD_UNCHANGED)

            scale_percent = 50 # percent of original size
            width = int(basefile.shape[1] * scale_percent / 100)
            height = int(basefile.shape[0] * scale_percent / 100)
            dim = (width, height)

            if dim[0] > 1 or dim[1] > 1:

                if active_image.TLM_ImageProperties.tlm_image_scale_method == "Nearest":
                    interp = cv2.INTER_NEAREST
                elif active_image.TLM_ImageProperties.tlm_image_scale_method == "Area":
                    interp = cv2.INTER_AREA
                elif active_image.TLM_ImageProperties.tlm_image_scale_method == "Linear":
                    interp = cv2.INTER_LINEAR
                elif active_image.TLM_ImageProperties.tlm_image_scale_method == "Cubic":
                    interp = cv2.INTER_CUBIC
                elif active_image.TLM_ImageProperties.tlm_image_scale_method == "Lanczos":
                    interp = cv2.INTER_LANCZOS4

                resized = cv2.resize(basefile, dim, interpolation = interp)

                #resizedFile = os.path.join(dir_path, basename + "_" + str(width) + "_" + str(height) + extension)
                resizedFile = os.path.join(dir_path, basename + extension)

                cv2.imwrite(resizedFile, resized)

                active_image.filepath_raw = resizedFile
                bpy.ops.image.reload()

                print(newfile)
                print(img_path)
        
        else:

            print("Please save image")

        print("Upscale")

        return {'RUNNING_MODAL'}