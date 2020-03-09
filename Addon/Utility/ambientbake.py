import bpy, os, platform, subprocess
from . import utility, functions, function_constants
import numpy as np

def TLM_Build_AO():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"

    prevObjRenderset = []

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_bake_ao:
                print("AOSELECT: " + obj.name)

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

                for mat in bpy.data.materials:
                    if mat.name.endswith('_bakedAO'):
                        bpy.data.materials.remove(mat, do_unlink=True)
                for img in bpy.data.images:
                    if img.name == obj.name + "_bakedAO":
                        bpy.data.images.remove(img, do_unlink=True)

                #Single user materials?
                ob = obj
                for slot in ob.material_slots:
                    # Temp material already exists
                    if slot.material.name.endswith('_tempAO'):
                        continue
                    n = slot.material.name + '_' + ob.name + '_tempAO'
                    if not n in bpy.data.materials:
                        slot.material = slot.material.copy()
                    slot.material.name = n

                #Add images for baking
                img_name = obj.name + '_bakedAO'
                res = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) / int(scene.TLM_SceneProperties.tlm_lightmap_scale)
                if img_name not in bpy.data.images or bpy.data.images[img_name].size[0] != res or bpy.data.images[img_name].size[1] != res:
                    img = bpy.data.images.new(img_name, res, res, alpha=False, float_buffer=False)
                    img.name = img_name
                else:
                    img = bpy.data.images[img_name]

                for slot in obj.material_slots:
                    mat = slot.material
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes

                    if "Baked AO Image" in nodes:
                        img_node = nodes["Baked AO Image"]
                    else:
                        img_node = nodes.new('ShaderNodeTexImage')
                        img_node.name = 'Baked AO Image'
                        img_node.location = (100, 100)
                        img_node.image = img
                    img_node.select = True
                    nodes.active = img_node

                #Configure selection
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                obs = bpy.context.view_layer.objects
                active = obs.active

                if scene.TLM_SceneProperties.tlm_apply_on_unwrap:
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                uv_layers = obj.data.uv_layers
                if not "UVMap_Lightmap" in uv_layers:
                    uvmap = uv_layers.new(name="UVMap_Lightmap")
                    uv_layers.active_index = len(uv_layers) - 1
                    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Lightmap":
                        bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin)
                    elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Smart Project":
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(True)
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
                    else:
                        pass
                else:
                    for i in range(0, len(uv_layers)):
                        if uv_layers[i].name == 'UVMap_Lightmap':
                            uv_layers.active_index = i
                            break

                for slot in obj.material_slots:

                    nodetree = slot.material.node_tree
                    bpy.context.active_object.active_material = slot.material

                    n = slot.material.name[:-5] + '_bakedAO'
                    if not n in bpy.data.materials:
                        mat = bpy.data.materials.new(name=n)
                        mat.use_nodes = True
                        nodes = mat.node_tree.nodes
                        img_node = nodes.new('ShaderNodeTexImage')
                        img_node.name = "Baked AO Image"
                        img_node.location = (100, 100)
                        img_node.image = bpy.data.images[img_name]
                        mat.node_tree.links.new(img_node.outputs[0], nodes['Principled BSDF'].inputs[0])
                    else:
                        mat = bpy.data.materials[n]
                        nodes = mat.node_tree.nodes
                        nodes['Baked AO Image'].image = bpy.data.images[img_name]

                for slot in obj.material_slots:

                    nodetree = bpy.data.materials[slot.name].node_tree
                    nodes = nodetree.nodes
                    mainNode = nodetree.nodes[0].inputs[0].links[0].from_node

                    for n in nodes:
                        if "LM" in n.name:
                            nodetree.links.new(n.outputs[0], mainNode.inputs[0])

                    for n in nodes:
                        if "Lightmap" in n.name:
                                nodes.remove(n)

                print("Baking AO for: " + bpy.context.view_layer.objects.active.name)

                bpy.ops.object.bake(type="AO", margin=scene.TLM_SceneProperties.tlm_dilation_margin)

                #TODO! MULTIPLE MATERIALS WITH AO ISN'T WORKING!

                for slot in obj.material_slots:
                    mat = slot.material
                    if mat.name.endswith('_tempAO'):
                        old = slot.material
                        slot.material = bpy.data.materials[old.name.split('_' + obj.name)[0]]
                        bpy.data.materials.remove(old, do_unlink=True)

                uv_layers = obj.data.uv_layers
                uv_layers.active_index = 0

                for slot in obj.material_slots:

                    nodetree = bpy.data.materials[slot.name].node_tree

                    outputNode = nodetree.nodes[0]

                    if(outputNode.type != "OUTPUT_MATERIAL"):
                            for node in nodetree.nodes:
                                if node.type == "OUTPUT_MATERIAL":
                                    outputNode = node
                                    break

                    if len(outputNode.inputs[0].links) > 0:
                        mainNode = outputNode.inputs[0].links[0].from_node
                    else:
                        print("Tuple out of index...1")

                    if len(mainNode.inputs[0].links) > 0:
                        baseColorNode = mainNode.inputs[0].links[0].from_node
                        baseColorNode.name = "AO_P"
                    else:
                        print("Tuple out of index...: ")
                        print("Main: " + mainNode.name)
                        print("Out: " + outputNode.name)

                    nodePos1 = mainNode.location
                    nodePos2 = baseColorNode.location

                    mixNode = nodetree.nodes.new(type="ShaderNodeMixRGB")
                    mixNode.name = "AO_Multiplication"
                    mixNode.location = ((-300, -500))
                    mixNode.location = utility.lerpNodePoints(nodePos1, nodePos2, 0.5)
                    if scene.TLM_SceneProperties.tlm_indirect_only:
                        mixNode.blend_type = 'ADD'
                    else:
                        mixNode.blend_type = 'MULTIPLY'
                    
                    mixNode.inputs[0].default_value = 1.0

                    LightmapNode = nodetree.nodes.new(type="ShaderNodeTexImage")
                    LightmapNode.location = ((baseColorNode.location[0]-300,baseColorNode.location[1] + 300))
                    LightmapNode.image = bpy.data.images[obj.name + "_bakedAO"]
                    LightmapNode.name = "AO_Image"

                    UVLightmap = nodetree.nodes.new(type="ShaderNodeUVMap")
                    UVLightmap.uv_map = "UVMap_Lightmap"
                    UVLightmap.name = "AO_UV"
                    UVLightmap.location = ((-1000, baseColorNode.location[1] + 300))

                    nodetree.links.new(baseColorNode.outputs[0], mixNode.inputs[1]) 
                    nodetree.links.new(LightmapNode.outputs[0], mixNode.inputs[2])
                    nodetree.links.new(mixNode.outputs[0], mainNode.inputs[0]) 
                    nodetree.links.new(UVLightmap.outputs[0], LightmapNode.inputs[0]) #Link Baked AO and UVMap node

                #SAVE/DENOISE AO

                dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)
                bakemap_path = os.path.join(dirpath, img_name)

                if(scene.TLM_SceneProperties.tlm_denoise_ao):
                    denoiseAO = True
                else:
                    denoiseAO = False

                if(denoiseAO):
                    print("denoising AO")
                    image = bpy.data.images[img_name]
                    width = image.size[0]
                    height = image.size[1]

                    image_output_array = np.zeros([width, height, 3], dtype="float32")
                    image_output_array = np.array(image.pixels)
                    image_output_array = image_output_array.reshape(height, width, 4)
                    image_output_array = np.float32(image_output_array[:,:,:3])

                    image_output_destination = bakemap_path + ".pfm"

                    with open(image_output_destination, "wb") as fileWritePFM:
                        utility.save_pfm(fileWritePFM, image_output_array)

                    denoise_output_destination = bakemap_path + "_denoised.pfm"

                    Scene = scene

                    verbose = Scene.TLM_SceneProperties.tlm_oidn_verbose
                    affinity = Scene.TLM_SceneProperties.tlm_oidn_affinity

                    if verbose:
                        print("Denoiser search: " + os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise.exe"))
                        v = "3"
                    else:
                        v = "0"

                    if affinity:
                        a = "1"
                    else:
                        a = "0"

                    threads = str(Scene.TLM_SceneProperties.tlm_oidn_threads)
                    maxmem = str(Scene.TLM_SceneProperties.tlm_oidn_maxmem)

                    if platform.system() == 'Windows':
                        oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise.exe")
                        pipePath = [oidnPath, '-f', 'RTLightmap', '-hdr', image_output_destination, '-o', denoise_output_destination, '-verbose', v, '-threads', threads, '-affinity', a, '-maxmem', maxmem]
                    elif platform.system() == 'Darwin':
                        oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise")
                        pipePath = [oidnPath + ' -f ' + ' RTLightmap ' + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + v]
                    else:
                        oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise")
                        pipePath = [oidnPath + ' -f ' + ' RTLightmap ' + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + v]
                        
                    if not verbose:
                        denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)
                    else:
                        denoisePipe = subprocess.Popen(pipePath, shell=True)

                    denoisePipe.communicate()[0]

                    with open(denoise_output_destination, "rb") as f:
                        denoise_data, scale = utility.load_pfm(f)

                    ndata = np.array(denoise_data)
                    ndata2 = np.dstack((ndata, np.ones((width,height))))
                    img_array = ndata2.ravel()
                    bpy.data.images[image.name].pixels = img_array
                    bpy.data.images[image.name].filepath_raw = bakemap_path + "_denoised.hdr"
                    bpy.data.images[image.name].file_format = "HDR"
                    bpy.data.images[image.name].save()

                else:
                    print("Not denoising AO")
                    for img in bpy.data.images:
                        if img.name.endswith("_bakedAO"):
                            if img.filepath_raw == "":
                                bpy.data.images[img.name].filepath_raw = bakemap_path + ".png"
                                bpy.data.images[img.name].file_format = "PNG"
                                bpy.data.images[img.name].save()

    for mat in bpy.data.materials:
        if mat.name.endswith('_bakedAO'):
            bpy.data.materials.remove(mat, do_unlink=True)

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
            if image.name.endswith("_bakedAO"):
                image.save()