import bpy, os, re, sys
from . import functions, function_constants
import numpy as np
from . import matcache

def saturate(num, floats=True):
    if num < 0:
        num = 0
    elif num > (1 if floats else 255):
        num = (1 if floats else 255)
    return num 

def lerpNodePoints(a, b, c):
    return (a + c * (b - a))

def load_library(asset_name):

    scriptDir = os.path.dirname(os.path.realpath(__file__))

    if bpy.data.filepath.endswith('tlm_data.blend'): # Prevent load in library itself
        return

    data_path = os.path.abspath(os.path.join(scriptDir, '..', 'Assets/tlm_data.blend'))
    data_names = [asset_name]

    # Import
    data_refs = data_names.copy()
    with bpy.data.libraries.load(data_path, link=False) as (data_from, data_to):
        data_to.node_groups = data_refs

    for ref in data_refs:
        ref.use_fake_user = True

def check_compatible_naming(self):
    for obj in bpy.data.objects:
        if "_" in obj.name:
            obj.name = obj.name.replace("_",".")
        if " " in obj.name:
            obj.name = obj.name.replace(" ",".")
        if "[" in obj.name:
            obj.name = obj.name.replace("[",".")
        if "]" in obj.name:
            obj.name = obj.name.replace("]",".")

        for slot in obj.material_slots:
            if "_" in slot.material.name:
                slot.material.name = slot.material.name.replace("_",".")
            if " " in slot.material.name:
                slot.material.name = slot.material.name.replace(" ",".")
            if "[" in slot.material.name:
                slot.material.name = slot.material.name.replace("[",".")
            if "[" in slot.material.name:
                slot.material.name = slot.material.name.replace("]",".")

def store_existing(cycles, scene, context):
    
    selected = []

    for obj in bpy.data.objects:
        if obj.select_get():
            selected.append(obj.name)

    prevCyclesSettings = [
        cycles.samples,
        cycles.max_bounces,
        cycles.diffuse_bounces,
        cycles.glossy_bounces,
        cycles.transparent_max_bounces,
        cycles.transmission_bounces,
        cycles.volume_bounces,
        cycles.caustics_reflective,
        cycles.caustics_refractive,
        cycles.device,
        scene.render.engine,
        bpy.context.view_layer.objects.active,
        selected
    ]
    return prevCyclesSettings

def set_settings(cycles, scene):
    sceneProperties = scene.TLM_SceneProperties
    cycles.device = sceneProperties.tlm_mode
    scene.render.engine = "CYCLES"
    
    if scene.TLM_SceneProperties.tlm_quality == "Preview":
        cycles.samples = 32
        cycles.max_bounces = 1
        cycles.diffuse_bounces = 1
        cycles.glossy_bounces = 1
        cycles.transparent_max_bounces = 1
        cycles.transmission_bounces = 1
        cycles.volume_bounces = 1
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.TLM_SceneProperties.tlm_quality == "Medium":
        cycles.samples = 256
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.TLM_SceneProperties.tlm_quality == "High":
        cycles.samples = 512
        cycles.max_bounces = 128
        cycles.diffuse_bounces = 128
        cycles.glossy_bounces = 128
        cycles.transparent_max_bounces = 128
        cycles.transmission_bounces = 128
        cycles.volume_bounces = 128
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.TLM_SceneProperties.tlm_quality == "Production":
        cycles.samples = 1024
        cycles.max_bounces = 256
        cycles.diffuse_bounces = 256
        cycles.glossy_bounces = 256
        cycles.transparent_max_bounces = 256
        cycles.transmission_bounces = 256
        cycles.volume_bounces = 256
        cycles.caustics_reflective = True
        cycles.caustics_refractive = True
    else: #Custom
        pass

def restore_settings(cycles, scene, prevCyclesSettings):
    cycles.samples = prevCyclesSettings[0]
    cycles.max_bounces = prevCyclesSettings[1]
    cycles.diffuse_bounces = prevCyclesSettings[2]
    cycles.glossy_bounces = prevCyclesSettings[3]
    cycles.transparent_max_bounces = prevCyclesSettings[4]
    cycles.transmission_bounces = prevCyclesSettings[5]
    cycles.volume_bounces = prevCyclesSettings[6]
    cycles.caustics_reflective = prevCyclesSettings[7]
    cycles.caustics_refractive = prevCyclesSettings[8]
    cycles.device = prevCyclesSettings[9]
    scene.render.engine = prevCyclesSettings[10]

    bpy.context.view_layer.objects.active = prevCyclesSettings[11]

    for obj in bpy.data.objects:
        if obj.name in prevCyclesSettings[12]:
            obj.select_set(True)
        else:
            obj.select_set(False)

def preprocess_material(obj, scene):
    if len(obj.material_slots) == 0:
        single = False
        number = 0
        while single == False:
            matname = obj.name + ".00" + str(number)
            if matname in bpy.data.materials:
                single = False
                number = number + 1
            else:
                mat = bpy.data.materials.new(name=matname)
                mat.use_nodes = True
                obj.data.materials.append(mat)
                single = True

    #Make the materials unique if multiple users (Prevent baking over existing)
    for slot in obj.material_slots:
        mat = slot.material
        if mat.users > 1:
                copymat = mat.copy()
                slot.material = copymat 

    #Make a material backup and restore original if exists
    if scene.TLM_SceneProperties.tlm_caching_mode == "Copy":
        for slot in obj.material_slots:
            matname = slot.material.name
            originalName = "." + matname + "_Original"
            hasOriginal = False
            if originalName in bpy.data.materials:
                hasOriginal = True
            else:
                hasOriginal = False

            if hasOriginal:
                matcache.backup_material_restore(slot)

            matcache.backup_material_copy(slot)
    else: #Cache blend
        print("Warning: Cache blend not supported")

    # for mat in bpy.data.materials:
    #     if mat.name.endswith('_baked'):
    #         bpy.data.materials.remove(mat, do_unlink=True)
    # for img in bpy.data.images:
    #     if img.name == obj.name + "_baked":
    #         bpy.data.images.remove(img, do_unlink=True)


    #SOME ATLAS EXCLUSION HERE?
    ob = obj
    for slot in ob.material_slots:
        #If temporary material already exists
        if slot.material.name.endswith('_temp'):
            continue
        n = slot.material.name + '_' + ob.name + '_temp'
        if not n in bpy.data.materials:
            slot.material = slot.material.copy()
        slot.material.name = n

    #Add images for baking
    img_name = obj.name + '_baked'
    #Resolution is object lightmap resolution divided by global scaler
    
    if (obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup" and obj.TLM_ObjectProperties.tlm_atlas_pointer != ""):

        atlas_image_name = obj.TLM_ObjectProperties.tlm_atlas_pointer + "_baked"

        res = int(scene.TLM_AtlasList[obj.TLM_ObjectProperties.tlm_atlas_pointer].tlm_atlas_lightmap_resolution) / int(scene.TLM_SceneProperties.tlm_lightmap_scale)

        #If image not in bpy.data.images or if size changed, make a new image
        if atlas_image_name not in bpy.data.images or bpy.data.images[atlas_image_name].size[0] != res or bpy.data.images[atlas_image_name].size[1] != res:
            img = bpy.data.images.new(img_name, res, res, alpha=True, float_buffer=True)

            num_pixels = len(img.pixels)
            result_pixel = list(img.pixels)

            for i in range(0,num_pixels,4):
                result_pixel[i+0] = scene.TLM_SceneProperties.tlm_default_color[0]
                result_pixel[i+1] = scene.TLM_SceneProperties.tlm_default_color[1]
                result_pixel[i+2] = scene.TLM_SceneProperties.tlm_default_color[2]
                result_pixel[i+3] = 1.0

            img.pixels = result_pixel

            img.name = atlas_image_name
        else:
            img = bpy.data.images[atlas_image_name]

        for slot in obj.material_slots:
            mat = slot.material
            mat.use_nodes = True
            nodes = mat.node_tree.nodes

            if "Baked Image" in nodes:
                img_node = nodes["Baked Image"]
            else:
                img_node = nodes.new('ShaderNodeTexImage')
                img_node.name = 'Baked Image'
                img_node.location = (100, 100)
                img_node.image = img
            img_node.select = True
            nodes.active = img_node

    else:

        res = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) / int(scene.TLM_SceneProperties.tlm_lightmap_scale)

        #If image not in bpy.data.images or if size changed, make a new image
        if img_name not in bpy.data.images or bpy.data.images[img_name].size[0] != res or bpy.data.images[img_name].size[1] != res:
            img = bpy.data.images.new(img_name, res, res, alpha=True, float_buffer=True)

            num_pixels = len(img.pixels)
            result_pixel = list(img.pixels)

            for i in range(0,num_pixels,4):
                result_pixel[i+0] = scene.TLM_SceneProperties.tlm_default_color[0]
                result_pixel[i+1] = scene.TLM_SceneProperties.tlm_default_color[1]
                result_pixel[i+2] = scene.TLM_SceneProperties.tlm_default_color[2]
                result_pixel[i+3] = 1.0

            img.pixels = result_pixel

            img.name = img_name
        else:
            img = bpy.data.images[img_name]

        for slot in obj.material_slots:
            mat = slot.material
            mat.use_nodes = True
            nodes = mat.node_tree.nodes

            if "Baked Image" in nodes:
                img_node = nodes["Baked Image"]
            else:
                img_node = nodes.new('ShaderNodeTexImage')
                img_node.name = 'Baked Image'
                img_node.location = (100, 100)
                img_node.image = img
            img_node.select = True
            nodes.active = img_node

def postmanage_materials(scene):
    for mat in bpy.data.materials:
        if mat.name.endswith('_baked'):
            has_user = False
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and mat.name.endswith('_' + obj.name + '_baked'):
                    has_user = True
                    break
            # if not has_user:
            #     bpy.data.materials.remove(mat, do_unlink=True)

    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)

    #Save
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                if (obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup" and obj.TLM_ObjectProperties.tlm_atlas_pointer != ""):
                    atlas_image_name = obj.TLM_ObjectProperties.tlm_atlas_pointer + "_baked"
                    img_name = atlas_image_name
                    bakemap_path = os.path.join(dirpath, img_name)
                else:
                    img_name = obj.name + '_baked'
                    bakemap_path = os.path.join(dirpath, img_name)

                bpy.data.images[img_name].filepath_raw = bakemap_path + ".hdr"
                bpy.data.images[img_name].file_format = "HDR"
                bpy.data.images[img_name].save()

def load_pfm(file, as_flat_list=False):
    #start = time()

    header = file.readline().decode("utf-8").rstrip()
    if header == "PF":
        color = True
    elif header == "Pf":
        color = False
    else:
        raise Exception("Not a PFM file.")

    dim_match = re.match(r"^(\d+)\s(\d+)\s$", file.readline().decode("utf-8"))
    if dim_match:
        width, height = map(int, dim_match.groups())
    else:
        raise Exception("Malformed PFM header.")

    scale = float(file.readline().decode("utf-8").rstrip())
    if scale < 0:  # little-endian
        endian = "<"
        scale = -scale
    else:
        endian = ">"  # big-endian

    data = np.fromfile(file, endian + "f")
    shape = (height, width, 3) if color else (height, width)
    if as_flat_list:
        result = data
    else:
        result = np.reshape(data, shape)
    #print("PFM import took %.3f s" % (time() - start))
    return result, scale

def save_pfm(file, image, scale=1):
    #start = time()

    if image.dtype.name != "float32":
        raise Exception("Image dtype must be float32 (got %s)" % image.dtype.name)

    if len(image.shape) == 3 and image.shape[2] == 3:  # color image
        color = True
    elif len(image.shape) == 2 or len(image.shape) == 3 and image.shape[2] == 1:  # greyscale
        color = False
    else:
        raise Exception("Image must have H x W x 3, H x W x 1 or H x W dimensions.")

    file.write(b"PF\n" if color else b"Pf\n")
    file.write(b"%d %d\n" % (image.shape[1], image.shape[0]))

    endian = image.dtype.byteorder

    if endian == "<" or endian == "=" and sys.byteorder == "little":
        scale = -scale

    file.write(b"%f\n" % scale)

    image.tofile(file)

    #print("PFM export took %.3f s" % (time() - start))

def apply_materials(self, scene):
    for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                    decoding = False

                    for slot in obj.material_slots:
                        mat = slot.material
                        if mat.name.endswith('_temp'):
                            old = slot.material
                            slot.material = bpy.data.materials[old.name.split('_' + obj.name)[0]]
                            #bpy.data.materials.remove(old, do_unlink=True)

                    uv_layers = obj.data.uv_layers
                    uv_layers.active_index = 0

                    for slot in obj.material_slots:

                        if(scene.TLM_SceneProperties.tlm_encoding_armory_setup):

                            tlm_rgbm = bpy.data.node_groups.get('RGBM Decode')
                            tlm_rgbd = bpy.data.node_groups.get('RGBD Decode')
                            tlm_logluv = bpy.data.node_groups.get('LogLuv Decode')

                            if tlm_rgbm == None:
                                load_library('RGBM Decode')

                            if tlm_rgbd == None:
                                load_library('RGBD Decode')

                            if tlm_logluv == None:
                                load_library('LogLuv Decode')

                        if(scene.TLM_SceneProperties.tlm_exposure_multiplier > 0):
                            tlm_exposure = bpy.data.node_groups.get('Exposure')

                            if tlm_exposure == None:
                                load_library('Exposure')

                        nodetree = bpy.data.materials[slot.name].node_tree

                        outputNode = nodetree.nodes[0]

                        if(outputNode.type != "OUTPUT_MATERIAL"):
                            for node in nodetree.nodes:
                                if node.type == "OUTPUT_MATERIAL":
                                    outputNode = node
                                    break

                        #TODO: Proper check

                        mainNode = outputNode.inputs[0].links[0].from_node
                        print("Mainnode: " + mainNode.name)

                        if mainNode.type not in ['BSDF_PRINCIPLED','BSDF_DIFFUSE','GROUP']:

                            #TODO! FIND THE PRINCIPLED PBR
                            self.report({'INFO'}, "The primary material node is not supported. Seeking first principled.")

                            if len(functions.find_node_by_type(nodetree.nodes, function_constants.Node_Types.pbr_node)) > 0: 
                                mainNode = functions.find_node_by_type(nodetree.nodes, function_constants.Node_Types.pbr_node)[0]
                            else:
                                self.report({'INFO'}, "No principled found. Seeking diffuse")
                                if len(functions.find_node_by_type(nodetree.nodes, function_constants.Node_Types.diffuse)) > 0: 
                                    mainNode = functions.find_node_by_type(nodetree.nodes, function_constants.Node_Types.diffuse)[0]
                                else:
                                    self.report({'INFO'}, "No supported nodes. Continuing anyway.")
                                    pass

                        if mainNode.type == 'GROUP':
                            if mainNode.node_tree != "Armory PBR":
                                print("The material group is not supported!")
                                pass

                        if len(mainNode.inputs[0].links) == 0:
                            baseColorValue = mainNode.inputs[0].default_value
                            baseColorNode = nodetree.nodes.new(type="ShaderNodeRGB")
                            baseColorNode.outputs[0].default_value = baseColorValue
                            baseColorNode.location = ((mainNode.location[0]-500,mainNode.location[1]))
                            baseColorNode.name = "Lightmap_BasecolorNode_A"
                        else:
                            baseColorNode = mainNode.inputs[0].links[0].from_node
                            baseColorNode.name = "LM_P"

                        nodePos1 = mainNode.location
                        nodePos2 = baseColorNode.location

                        mixNode = nodetree.nodes.new(type="ShaderNodeMixRGB")
                        mixNode.name = "Lightmap_Multiplication"
                        mixNode.location = lerpNodePoints(nodePos1, nodePos2, 0.5)
                        if scene.TLM_SceneProperties.tlm_indirect_only:
                            if scene.TLM_SceneProperties.tlm_indirect_mode == "Additive":
                                mixNode.blend_type = 'ADD'
                            else:
                                mixNode.blend_type = 'MULTIPLY'
                        else:
                            mixNode.blend_type = 'MULTIPLY'
                        
                        mixNode.inputs[0].default_value = 1.0

                        LightmapNode = nodetree.nodes.new(type="ShaderNodeTexImage")
                        LightmapNode.location = ((baseColorNode.location[0]-300,baseColorNode.location[1] + 300))

                        if (obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup" and obj.TLM_ObjectProperties.tlm_atlas_pointer != ""):
                            img_name = obj.TLM_ObjectProperties.tlm_atlas_pointer + "_baked"
                        else:
                            img_name = obj.name + '_baked'

                        LightmapNode.image = bpy.data.images[img_name]
                        LightmapNode.name = "Lightmap_Image"

                        if(scene.TLM_SceneProperties.tlm_encoding_armory_setup):
                            if scene.TLM_SceneProperties.tlm_encoding_mode == 'LogLuv':
                                LightmapNode.image.colorspace_settings.name = 'Linear'

                        UVLightmap = nodetree.nodes.new(type="ShaderNodeUVMap")
                        UVLightmap.uv_map = "UVMap_Lightmap"
                        UVLightmap.name = "Lightmap_UV"
                        UVLightmap.location = ((-1000, baseColorNode.location[1] + 300))

                        if(scene.TLM_SceneProperties.tlm_encoding_armory_setup):
                            if scene.TLM_SceneProperties.tlm_encoding_mode == 'RGBM':
                                DecodeNode = nodetree.nodes.new(type="ShaderNodeGroup")
                                DecodeNode.node_tree = bpy.data.node_groups["RGBM Decode"]
                                DecodeNode.location = lerpNodePoints(LightmapNode.location, mixNode.location, 0.5)
                                DecodeNode.name = "Lightmap_RGBM_Decode"
                                decoding = True
                            if scene.TLM_SceneProperties.tlm_encoding_mode == "RGBD":
                                DecodeNode = nodetree.nodes.new(type="ShaderNodeGroup")
                                DecodeNode.node_tree = bpy.data.node_groups["RGBD Decode"]
                                DecodeNode.location = lerpNodePoints(LightmapNode.location, mixNode.location, 0.5)
                                DecodeNode.name = "Lightmap_RGBD_Decode"
                                decoding = True
                            if scene.TLM_SceneProperties.tlm_encoding_mode == "LogLuv":
                                DecodeNode = nodetree.nodes.new(type="ShaderNodeGroup")
                                DecodeNode.node_tree = bpy.data.node_groups["LogLuv Decode"]
                                DecodeNode.location = lerpNodePoints(LightmapNode.location, mixNode.location, 0.5)
                                DecodeNode.name = "Lightmap_LogLuv_Decode"
                                decoding = True

                        if(scene.TLM_SceneProperties.tlm_exposure_multiplier > 0):
                            ExposureNode = nodetree.nodes.new(type="ShaderNodeGroup")
                            ExposureNode.node_tree = bpy.data.node_groups["Exposure"]
                            ExposureNode.inputs[1].default_value = scene.TLM_SceneProperties.tlm_exposure_multiplier
                            ExposureNode.location = lerpNodePoints(LightmapNode.location, mixNode.location, 0.4)
                            ExposureNode.name = "Lightmap_Exposure"

                        nodetree.links.new(baseColorNode.outputs[0], mixNode.inputs[1])   

                        if decoding:
                            if (scene.TLM_SceneProperties.tlm_exposure_multiplier > 0):
                                nodetree.links.new(LightmapNode.outputs[0], DecodeNode.inputs[0])
                                nodetree.links.new(LightmapNode.outputs[1], DecodeNode.inputs[1])
                                nodetree.links.new(DecodeNode.outputs[0], ExposureNode.inputs[0])
                                nodetree.links.new(ExposureNode.outputs[0],  mixNode.inputs[2])
                            else:
                                nodetree.links.new(LightmapNode.outputs[0], DecodeNode.inputs[0])
                                nodetree.links.new(LightmapNode.outputs[1], DecodeNode.inputs[1])
                                nodetree.links.new(DecodeNode.outputs[0], mixNode.inputs[2])
                        else:
                            if(scene.TLM_SceneProperties.tlm_exposure_multiplier > 0):
                                nodetree.links.new(LightmapNode.outputs[0], ExposureNode.inputs[0])
                                nodetree.links.new(ExposureNode.outputs[0],  mixNode.inputs[2])
                            else:
                                nodetree.links.new(LightmapNode.outputs[0], mixNode.inputs[2])

                        nodetree.links.new(mixNode.outputs[0], mainNode.inputs[0]) 
                        nodetree.links.new(UVLightmap.outputs[0], LightmapNode.inputs[0])

    for mat in bpy.data.materials:
        if mat.name.endswith('_baked'):
            pass
            #bpy.data.materials.remove(mat, do_unlink=True)

        if mat.name.endswith('_temp'):
            bpy.data.materials.remove(mat, do_unlink=True)

    #bpy.ops.image.save_all_modified()

    # for image in bpy.data.images:
    #     if image.filepath_raw.endswith('_finalized.hdr'):
    #         image.filepath_raw = image.filepath[:-14] + ".hdr"
    #         image.save()
    #     if image.filepath_raw.endswith('_denoised.hdr'):
    #         image.filepath_raw = image.filepath[:-13] + ".hdr"
    #         image.save()

    if not scene.TLM_SceneProperties.tlm_keep_cache_files:
        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)
        if os.path.isdir(dirpath):
            list = os.listdir(dirpath)
            for file in list:
                if file.endswith(".pfm"):
                    os.remove(os.path.join(dirpath,file))
                if file.endswith("denoised.hdr"):
                    os.remove(os.path.join(dirpath,file))
                #if file.endswith("finalized.hdr"):
                #        os.remove(os.path.join(dirpath,file))

        for image in bpy.data.images:
            if image.name.endswith("_baked"):
                image.save()

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            for slot in obj.material_slots:
                if slot.name.endswith('_Original'):
                    if slot.name[1:-9] in bpy.data.materials:
                        slot.material = bpy.data.materials[slot.name[1:-9]]