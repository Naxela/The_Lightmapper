import bpy, os

from .prepare import lightmap_uv_channel, find_uv_layer_index
from . import cache

def apply_lightmaps():
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                hidden = False

                if obj.hide_get():
                    hidden = True
                if obj.hide_viewport:
                    hidden = True
                if obj.hide_render:
                    hidden = True

                if not hidden:

                    for slot in obj.material_slots:
                        mat = slot.material
                        node_tree = mat.node_tree
                        nodes = mat.node_tree.nodes

                        scene = bpy.context.scene

                        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_EngineProperties.tlm_lightmap_savedir)

                        #Find nodes
                        for node in nodes:
                            if node.name == "Baked Image":

                                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                    print("Finding node source for material: " + mat.name + " @ " + obj.name)

                                extension = ".hdr"

                                postfix = "_baked"

                                if scene.TLM_SceneProperties.tlm_denoise_use:
                                    postfix = "_denoised"
                                if scene.TLM_SceneProperties.tlm_filtering_use:
                                    postfix = "_filtered"

                                if node.image:
                                    node.image.source = "FILE"

                                    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA":
                                        print("Atlas object image")
                                        image_name = obj.TLM_ObjectProperties.tlm_atlas_pointer + postfix + extension #TODO FIX EXTENSION
                                    elif obj.TLM_ObjectProperties.tlm_postpack_object:
                                        print("Atlas object image (postpack)")
                                        image_name = obj.TLM_ObjectProperties.tlm_postatlas_pointer + postfix + extension #TODO FIX EXTENSION
                                    else:
                                        print("Baked object image")
                                        image_name = obj.name + postfix + extension #TODO FIX EXTENSION
                                    
                                    node.image.filepath_raw = os.path.join(dirpath, image_name)

def apply_preview_materials():
    scene = bpy.context.scene
    props = scene.TLM_SceneProperties

    for obj in cache.iter_lightmap_objects():
        if not any(cache.is_preview_material(s.material) for s in obj.material_slots):
            continue

        for slot in obj.material_slots:
            mat = slot.material
            if not cache.is_preview_material(mat) or mat.TLM_ignore:
                continue

            tree = mat.node_tree
            tree.nodes.clear()
            nodes = tree.nodes
            links = tree.links

            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (400, 0)
            emission = nodes.new(type='ShaderNodeEmission')
            emission.name = "TLM_Preview_Emission"
            emission.location = (100, 0)
            emission.inputs['Strength'].default_value = 1.0

            if scene.TLM_EngineProperties.tlm_target == "vertex":
                lightmap = nodes.new(type='ShaderNodeVertexColor')
                lightmap.name = "TLM_Lightmap"
                lightmap.location = (-300, 0)
                lightmap.layer_name = "TLM"
            else:
                lightmap = nodes.new(type='ShaderNodeTexImage')
                lightmap.name = "TLM_Lightmap"
                lightmap.location = (-300, 0)
                lightmap.interpolation = props.tlm_texture_interpolation
                lightmap.extension = props.tlm_texture_extrapolation

                img_name = obj.name + '_baked'
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA" and obj.TLM_ObjectProperties.tlm_atlas_pointer != "":
                    img_name = obj.TLM_ObjectProperties.tlm_atlas_pointer + "_baked"
                if img_name in bpy.data.images:
                    lightmap.image = bpy.data.images[img_name]

                uv = nodes.new(type='ShaderNodeUVMap')
                uv.name = "Lightmap_UV"
                uv.location = (-600, 0)
                uv.uv_map = lightmap_uv_channel(obj)
                links.new(uv.outputs['UV'], lightmap.inputs['Vector'])

            links.new(lightmap.outputs['Color'], emission.inputs['Color'])
            links.new(emission.outputs['Emission'], output.inputs['Surface'])

def get_lightmap_output_suffix(scene=None):
    scene = scene or bpy.context.scene
    sceneProperties = scene.TLM_SceneProperties

    end = "_baked"
    if sceneProperties.tlm_denoise_use:
        end = "_denoised"
    if sceneProperties.tlm_filtering_use:
        end = "_filtered"

    formatEnc = ".hdr"
    if sceneProperties.tlm_encoding_use and scene.TLM_EngineProperties.tlm_bake_mode != "Background":
        if sceneProperties.tlm_encoding_device == "CPU":
            if sceneProperties.tlm_encoding_mode_a == "HDR" and sceneProperties.tlm_format == "EXR":
                formatEnc = ".exr"
            elif sceneProperties.tlm_encoding_mode_a == "RGBM":
                formatEnc = "_encoded.png"
            elif sceneProperties.tlm_encoding_mode_a == "RGBD":
                formatEnc = "_encoded.png"
            elif sceneProperties.tlm_encoding_mode_a == "SDR":
                formatEnc = ".png"
        else:
            if sceneProperties.tlm_encoding_mode_b == "HDR":
                if sceneProperties.tlm_format == "KTX":
                    formatEnc = ".ktx2"
                elif sceneProperties.tlm_format == "EXR":
                    formatEnc = ".exr"
            elif sceneProperties.tlm_encoding_mode_b == "LogLuv":
                formatEnc = "_encoded.png"
            elif sceneProperties.tlm_encoding_mode_b == "RGBM":
                formatEnc = "_encoded.png"
            elif sceneProperties.tlm_encoding_mode_b == "RGBD":
                formatEnc = "_encoded.png"
            elif sceneProperties.tlm_encoding_mode_b == "SDR":
                formatEnc = ".png"

    return end, formatEnc

def set_active_lightmap_uv_layers(context=None):
    for obj in cache.iter_lightmap_objects(context):
        layer_index = find_uv_layer_index(obj.data.uv_layers, lightmap_uv_channel(obj))
        if layer_index >= 0:
            obj.data.uv_layers.active_index = layer_index

def set_active_texture_uv_layers(context=None):
    for obj in cache.iter_lightmap_objects(context):
        if obj.data.uv_layers:
            obj.data.uv_layers.active_index = 0

def exchangeLightmapsToPostfix(ext_postfix, new_postfix, formatHDR=".hdr"):

    if not bpy.context.scene.TLM_EngineProperties.tlm_target == "vertex":

        if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
            print(ext_postfix, new_postfix, formatHDR)

        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                    #Here
                    #If the object is part of atlas
                    print("CHECKING FOR REPART")
                    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA": #TODO, ALSO CONFIGURE FOR POSTATLAS

                        if bpy.context.scene.TLM_AtlasList[obj.TLM_ObjectProperties.tlm_atlas_pointer].tlm_atlas_merge_samemat:

                            #For each material we check if it ends with a number
                            for slot in obj.material_slots:

                                part = slot.name.rpartition('.')
                                if part[2].isnumeric() and part[0] in bpy.data.materials:

                                    print("Material for obj: " + obj.name + " was numeric, and the material: " + part[0] + " was found.")
                                    slot.material = bpy.data.materials.get(part[0])


                            
                            # for slot in obj.material_slots:
                            #     mat = slot.material
                            #     node_tree = mat.node_tree
                            #     nodes = mat.node_tree.nodes

                    try:

                        hidden = False

                        if obj.hide_get():
                            hidden = True
                        if obj.hide_viewport:
                            hidden = True
                        if obj.hide_render:
                            hidden = True

                        if not hidden:

                            for slot in obj.material_slots:
                                mat = slot.material
                                node_tree = mat.node_tree
                                nodes = mat.node_tree.nodes

                                for node in nodes:
                                    if node.name == "Baked Image" or (node.name.startswith("TLM_Lightmap") and node.name != "TLM_Lightmap_Extra"):

                                        if node.image != None:

                                            print("Node: " + node.name + " in " + mat.name )

                                            dirpath = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)

                                            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA" and obj.TLM_ObjectProperties.tlm_atlas_pointer != "":
                                                base = obj.TLM_ObjectProperties.tlm_atlas_pointer
                                            elif obj.TLM_ObjectProperties.tlm_postpack_object and obj.TLM_ObjectProperties.tlm_postatlas_pointer:
                                                base = obj.TLM_ObjectProperties.tlm_postatlas_pointer
                                            else:
                                                base = obj.name

                                            stem_prefix = base + new_postfix
                                            best_file = stem_prefix + formatHDR
                                            best_num = -1

                                            if os.path.isdir(dirpath):
                                                for fname in os.listdir(dirpath):
                                                    if not fname.endswith(formatHDR):
                                                        continue
                                                    name_stem = fname[:-len(formatHDR)]
                                                    for prefix in (stem_prefix, base):
                                                        if name_stem == prefix:
                                                            if 0 > best_num:
                                                                best_file = fname
                                                                best_num = 0
                                                        elif name_stem.startswith(prefix + ".") and name_stem[len(prefix) + 1:].isdigit():
                                                            num = int(name_stem[len(prefix) + 1:])
                                                            if num > best_num:
                                                                best_num = num
                                                                best_file = fname

                                            filepath = bpy.path.abspath(os.path.join(dirpath, best_file))
                                            if not os.path.isfile(filepath):
                                                baked_key = base + "_baked"
                                                if baked_key in bpy.data.images and bpy.data.images[baked_key].filepath_raw:
                                                    filepath = bpy.path.abspath(bpy.data.images[baked_key].filepath_raw)

                                            print("Node1: " + node.name + " => " + filepath)
                                            if os.path.isfile(filepath):
                                                node.image = bpy.data.images.load(filepath, check_existing=True)
                                                node.image.filepath_raw = filepath
                                                node.image.reload()

                                for node in nodes:
                                    if bpy.context.scene.TLM_SceneProperties.tlm_encoding_use and bpy.context.scene.TLM_SceneProperties.tlm_encoding_mode_b == "LogLuv": 
                                        if bpy.context.scene.TLM_SceneProperties.tlm_split_premultiplied:
                                            if node.name.startswith("TLM_Lightmap"):

                                                if node.image != None:

                                                    img_name = node.image.filepath_raw
                                                    print("PREM Main: " + img_name)
                                                    if node.image.filepath_raw.endswith("_encoded.png"):
                                                        print(node.image.filepath_raw + " => " + node.image.filepath_raw[:-4] + "_XYZ.png")
                                                    if not node.image.filepath_raw.endswith("_XYZ.png"):
                                                        node.image.filepath_raw = node.image.filepath_raw[:-4] + "_XYZ.png"

                                            if node.name.startswith("TLM_Lightmap_Extra"):

                                                if node.image != None:

                                                    img_path = node.image.filepath_raw[:-8] + "_W.png"
                                                    img = bpy.data.images.load(img_path)
                                                    node.image = img
                                                    bpy.data.images.load(img_path)
                                                    print("PREM Extra: " + img_path)
                                                    node.image.filepath_raw = img_path
                                                    node.image.colorspace_settings.name = "Linear"

                    except Exception as e:

                        print("Error occured with postfix change for obj: " + obj.name)
                        print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

    for image in bpy.data.images:
        image.reload()

def applyAOPass():

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                hidden = False

                if obj.hide_get():
                    hidden = True
                if obj.hide_viewport:
                    hidden = True
                if obj.hide_render:
                    hidden = True

                if not hidden:

                    for slot in obj.material_slots:
                        mat = slot.material
                        node_tree = mat.node_tree
                        nodes = mat.node_tree.nodes

                        for node in nodes:
                            if node.name == "Baked Image" or node.name == "TLM_Lightmap":

                                filepath = bpy.data.filepath
                                dirpath = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)

                                LightmapPath = node.image.filepath_raw

                                filebase = os.path.basename(LightmapPath)
                                filename = os.path.splitext(filebase)[0]
                                extension = os.path.splitext(filebase)[1]
                                AOImagefile = filename[:-4] + "_ao"
                                AOImagePath = os.path.join(dirpath, AOImagefile + extension)

                                AOMap = nodes.new('ShaderNodeTexImage')
                                AOMap.name = "TLM_AOMap"
                                AOImage = bpy.data.images.load(AOImagePath)
                                AOMap.image = AOImage
                                AOMap.location = -800, 0

                                AOMult = nodes.new(type="ShaderNodeMixRGB")
                                AOMult.name = "TLM_AOMult"
                                AOMult.blend_type = 'MULTIPLY'
                                AOMult.inputs[0].default_value = 1.0
                                AOMult.location = -300, 300

                                multyNode = nodes["Lightmap_Multiplication"]
                                mainNode = nodes["Principled BSDF"]
                                UVMapNode = nodes["Lightmap_UV"]

                                node_tree.links.remove(multyNode.outputs[0].links[0])

                                node_tree.links.new(multyNode.outputs[0], AOMult.inputs[1])
                                node_tree.links.new(AOMap.outputs[0], AOMult.inputs[2])
                                node_tree.links.new(AOMult.outputs[0], mainNode.inputs[0])
                                node_tree.links.new(UVMapNode.outputs[0], AOMap.inputs[0])