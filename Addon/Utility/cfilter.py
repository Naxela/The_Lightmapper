import bpy, os

module_pip = False
module_opencv = False

try:
    import pip
    module_pip = True
except ImportError:
    module_pip = False

try:
    import cv2
    module_opencv = True
except ImportError:
    pip 
    module_opencv = False

def filter_lightmaps(self, scene, module_opencv):
    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)

    for atlasgroup in scene.TLM_AtlasList:
        atlas_name = atlasgroup.name
        atlas_items = []

        img_name = atlas_name + '_baked'
        bakemap_path = os.path.join(dirpath, img_name)

        if scene.TLM_SceneProperties.tlm_filtering_use:
            filter_file_input = img_name + ".hdr"

            if module_opencv:

                filter_file_output = img_name + "_finalized.hdr"
                os.chdir(os.path.dirname(bakemap_path))
                opencv_process_image = cv2.imread(filter_file_input, -1)

                if scene.TLM_SceneProperties.tlm_filtering_mode == "Box":
                    if scene.TLM_SceneProperties.tlm_filtering_box_strength % 2 == 0:
                        kernel_size = (scene.TLM_SceneProperties.tlm_filtering_box_strength + 1,scene.TLM_SceneProperties.tlm_filtering_box_strength + 1)
                    else:
                        kernel_size = (scene.TLM_SceneProperties.tlm_filtering_box_strength,scene.TLM_SceneProperties.tlm_filtering_box_strength)
                    opencv_bl_result = cv2.blur(opencv_process_image, kernel_size)
                    if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                        for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                            opencv_bl_result = cv2.blur(opencv_bl_result, kernel_size)

                elif scene.TLM_SceneProperties.tlm_filtering_mode == "Gaussian":
                    if scene.TLM_SceneProperties.tlm_filtering_gaussian_strength % 2 == 0:
                        kernel_size = (scene.TLM_SceneProperties.tlm_filtering_gaussian_strength + 1,scene.TLM_SceneProperties.tlm_filtering_gaussian_strength + 1)
                    else:
                        kernel_size = (scene.TLM_SceneProperties.tlm_filtering_gaussian_strength,scene.TLM_SceneProperties.tlm_filtering_gaussian_strength)
                    sigma_size = 0
                    opencv_bl_result = cv2.GaussianBlur(opencv_process_image, kernel_size, sigma_size)
                    if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                        for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                            opencv_bl_result = cv2.GaussianBlur(opencv_bl_result, kernel_size, sigma_size)

                elif scene.TLM_SceneProperties.tlm_filtering_mode == "Bilateral":
                    diameter_size = scene.TLM_SceneProperties.tlm_filtering_bilateral_diameter
                    sigma_color = scene.TLM_SceneProperties.tlm_filtering_bilateral_color_deviation
                    sigma_space = scene.TLM_SceneProperties.tlm_filtering_bilateral_coordinate_deviation
                    opencv_bl_result = cv2.bilateralFilter(opencv_process_image, diameter_size, sigma_color, sigma_space)
                    if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                        for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                            opencv_bl_result = cv2.bilateralFilter(opencv_bl_result, diameter_size, sigma_color, sigma_space)
                else:

                    if scene.TLM_SceneProperties.tlm_filtering_median_kernel % 2 == 0:
                        kernel_size = (scene.TLM_SceneProperties.tlm_filtering_median_kernel + 1 , scene.TLM_SceneProperties.tlm_filtering_median_kernel + 1)
                    else:
                        kernel_size = (scene.TLM_SceneProperties.tlm_filtering_median_kernel, scene.TLM_SceneProperties.tlm_filtering_median_kernel)

                    opencv_bl_result = cv2.medianBlur(opencv_process_image, kernel_size[0])
                    if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                        for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                            opencv_bl_result = cv2.medianBlur(opencv_bl_result, kernel_size[0])

                cv2.imwrite(filter_file_output, opencv_bl_result)
                bpy.ops.image.open(filepath=os.path.join(os.path.dirname(bakemap_path),filter_file_output))
                bpy.data.images[atlas_name + "_baked"].name = atlas_name + "_temp"

                os.remove(filter_file_input)

                bpy.data.images[atlas_name + "_baked_finalized.hdr"].name = atlas_name + "_baked"

                os.rename(filter_file_input[:-4] + "_finalized.hdr", filter_file_input)
                
                bpy.data.images[atlas_name + "_baked"].filepath_raw = bpy.data.images[atlas_name + "_baked"].filepath_raw[:-14] + ".hdr"
                bpy.data.images.remove(bpy.data.images[atlas_name + "_temp"])

            else:
                print("Module missing: OpenCV. Filtering skipped")
                self.report({'INFO'}, "Missing OpenCV module - If you just installed it, please restart Blender")

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                if not obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup":

                    img_name = obj.name + '_baked'
                    bakemap_path = os.path.join(dirpath, img_name)

                    if scene.TLM_SceneProperties.tlm_filtering_use:
                        filter_file_input = img_name + ".hdr"

                        if module_opencv:

                            filter_file_output = img_name + "_finalized.hdr"
                            os.chdir(os.path.dirname(bakemap_path))
                            opencv_process_image = cv2.imread(filter_file_input, -1)

                            if scene.TLM_SceneProperties.tlm_filtering_mode == "Box":
                                if scene.TLM_SceneProperties.tlm_filtering_box_strength % 2 == 0:
                                    kernel_size = (scene.TLM_SceneProperties.tlm_filtering_box_strength + 1,scene.TLM_SceneProperties.tlm_filtering_box_strength + 1)
                                else:
                                    kernel_size = (scene.TLM_SceneProperties.tlm_filtering_box_strength,scene.TLM_SceneProperties.tlm_filtering_box_strength)
                                opencv_bl_result = cv2.blur(opencv_process_image, kernel_size)
                                if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                                    for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                                        opencv_bl_result = cv2.blur(opencv_bl_result, kernel_size)

                            elif scene.TLM_SceneProperties.tlm_filtering_mode == "Gaussian":
                                if scene.TLM_SceneProperties.tlm_filtering_gaussian_strength % 2 == 0:
                                    kernel_size = (scene.TLM_SceneProperties.tlm_filtering_gaussian_strength + 1,scene.TLM_SceneProperties.tlm_filtering_gaussian_strength + 1)
                                else:
                                    kernel_size = (scene.TLM_SceneProperties.tlm_filtering_gaussian_strength,scene.TLM_SceneProperties.tlm_filtering_gaussian_strength)
                                sigma_size = 0
                                opencv_bl_result = cv2.GaussianBlur(opencv_process_image, kernel_size, sigma_size)
                                if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                                    for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                                        opencv_bl_result = cv2.GaussianBlur(opencv_bl_result, kernel_size, sigma_size)

                            elif scene.TLM_SceneProperties.tlm_filtering_mode == "Bilateral":
                                diameter_size = scene.TLM_SceneProperties.tlm_filtering_bilateral_diameter
                                sigma_color = scene.TLM_SceneProperties.tlm_filtering_bilateral_color_deviation
                                sigma_space = scene.TLM_SceneProperties.tlm_filtering_bilateral_coordinate_deviation
                                opencv_bl_result = cv2.bilateralFilter(opencv_process_image, diameter_size, sigma_color, sigma_space)
                                if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                                    for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                                        opencv_bl_result = cv2.bilateralFilter(opencv_bl_result, diameter_size, sigma_color, sigma_space)
                            else:

                                if scene.TLM_SceneProperties.tlm_filtering_median_kernel % 2 == 0:
                                    kernel_size = (scene.TLM_SceneProperties.tlm_filtering_median_kernel + 1 , scene.TLM_SceneProperties.tlm_filtering_median_kernel + 1)
                                else:
                                    kernel_size = (scene.TLM_SceneProperties.tlm_filtering_median_kernel, scene.TLM_SceneProperties.tlm_filtering_median_kernel)

                                opencv_bl_result = cv2.medianBlur(opencv_process_image, kernel_size[0])
                                if scene.TLM_SceneProperties.tlm_filtering_iterations > 1:
                                    for x in range(scene.TLM_SceneProperties.tlm_filtering_iterations):
                                        opencv_bl_result = cv2.medianBlur(opencv_bl_result, kernel_size[0])

                            cv2.imwrite(filter_file_output, opencv_bl_result)
                            
                            bpy.ops.image.open(filepath=os.path.join(os.path.dirname(bakemap_path),filter_file_output))
                            bpy.data.images[obj.name +"_baked"].name = obj.name + "_temp"
                            os.remove(filter_file_input)

                            bpy.data.images[obj.name +"_baked_finalized.hdr"].name = obj.name + "_baked"
                            os.rename(filter_file_input[:-4] + "_finalized.hdr", filter_file_input)

                            bpy.data.images[obj.name + "_baked"].filepath_raw = bpy.data.images[obj.name + "_baked"].filepath_raw[:-14] + ".hdr"
                            bpy.data.images.remove(bpy.data.images[obj.name+"_temp"])

                        else:
                            print("Module missing: OpenCV. Filtering skipped")
                            self.report({'INFO'}, "Missing OpenCV module - If you just installed it, please restart Blender")

                else:
                    pass