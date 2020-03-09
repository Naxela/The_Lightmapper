import bpy, math, os
from . import utility

def encodeImageRGBM(image, maxRange, outDir, quality):
    input_image = bpy.data.images[image.name]
    image_name = input_image.name

    if input_image.colorspace_settings.name != 'Linear':
        input_image.colorspace_settings.name = 'Linear'

    # Removing .exr or .hdr prefix
    if image_name[-4:] == '.exr' or image_name[-4:] == '.hdr':
        image_name = image_name[:-4]

    target_image = bpy.data.images.get(image_name + '_encoded')
    print(image_name + '_encoded')
    if not target_image:
        target_image = bpy.data.images.new(
                name = image_name + '_encoded',
                width = input_image.size[0],
                height = input_image.size[1],
                alpha = True,
                float_buffer = False
                )
    
    num_pixels = len(input_image.pixels)
    result_pixel = list(input_image.pixels)

    for i in range(0,num_pixels,4):
        for j in range(3):
            result_pixel[i+j] *= 1.0 / maxRange;
        result_pixel[i+3] = utility.saturate(max(result_pixel[i], result_pixel[i+1], result_pixel[i+2], 1e-6))
        result_pixel[i+3] = math.ceil(result_pixel[i+3] * 255.0) / 255.0
        for j in range(3):
            result_pixel[i+j] /= result_pixel[i+3]
    
    target_image.pixels = result_pixel
    input_image = target_image
    
    #Save RGBM
    input_image.filepath_raw = outDir + "_encoded.png"
    input_image.file_format = "PNG"
    bpy.context.scene.render.image_settings.quality = quality
    input_image.save_render(filepath = input_image.filepath_raw, scene = bpy.context.scene)
    #input_image.
    #input_image.save()

def encodeImageRGBD(image, maxRange, outDir, quality):
    input_image = bpy.data.images[image.name]
    image_name = input_image.name

    if input_image.colorspace_settings.name != 'Linear':
        input_image.colorspace_settings.name = 'Linear'

    # Removing .exr or .hdr prefix
    if image_name[-4:] == '.exr' or image_name[-4:] == '.hdr':
        image_name = image_name[:-4]

    target_image = bpy.data.images.get(image_name + '_encoded')
    if not target_image:
        target_image = bpy.data.images.new(
                name = image_name + '_encoded',
                width = input_image.size[0],
                height = input_image.size[1],
                alpha = True,
                float_buffer = False
                )
    
    num_pixels = len(input_image.pixels)
    result_pixel = list(input_image.pixels)

    for i in range(0,num_pixels,4):

        m = utility.saturate(max(result_pixel[i], result_pixel[i+1], result_pixel[i+2], 1e-6))
        d = max(maxRange / m, 1)
        d = utility.saturate(math.floor(d) / 255 )

        result_pixel[i] = result_pixel[i] * d * 255 / maxRange
        result_pixel[i+1] = result_pixel[i+1] * d * 255 / maxRange
        result_pixel[i+2] = result_pixel[i+2] * d * 255 / maxRange
        result_pixel[i+3] = d
    
    target_image.pixels = result_pixel
    
    input_image = target_image

    #Save RGBD
    input_image.filepath_raw = outDir + "_encoded.png"
    input_image.file_format = "PNG"
    bpy.context.scene.render.image_settings.quality = quality
    input_image.save_render(filepath = input_image.filepath_raw, scene = bpy.context.scene)

def encode_lightmaps(scene):
    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                img_name = obj.name + '_baked'
                bakemap_path = os.path.join(dirpath, img_name)

                if scene.TLM_SceneProperties.tlm_encoding_mode == "RGBM":
                    encodeImageRGBM(bpy.data.images[obj.name+"_baked"], 6.0, bakemap_path, scene.TLM_SceneProperties.tlm_compression)
                    bpy.data.images[obj.name+"_baked"].name = obj.name + "_temp"
                    bpy.data.images[obj.name+"_baked_encoded"].name = obj.name + "_baked"
                    bpy.data.images.remove(bpy.data.images[obj.name+"_temp"])
                elif scene.TLM_SceneProperties.tlm_encoding_mode == "RGBD":
                    encodeImageRGBD(bpy.data.images[obj.name+"_baked"], 6.0, bakemap_path, scene.TLM_SceneProperties.tlm_compression)
                    bpy.data.images[obj.name+"_baked"].name = obj.name + "_temp"
                    bpy.data.images[obj.name+"_baked_encoded"].name = obj.name + "_baked"
                    bpy.data.images.remove(bpy.data.images[obj.name+"_temp"])