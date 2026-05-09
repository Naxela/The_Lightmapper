import bpy, os, datetime
from .. import build
from time import time, sleep


def _is_hidden_from_lightmap(obj):
    hidden = False

    if obj.hide_get():
        hidden = True
    if obj.hide_viewport:
        hidden = True
    if obj.hide_render:
        hidden = True

    collections = obj.users_collection
    for collection in collections:
        if collection.hide_viewport:
            hidden = True
        if collection.hide_render:
            hidden = True
        try:
            if collection.name in bpy.context.scene.view_layers[0].layer_collection.children:
                if bpy.context.scene.view_layers[0].layer_collection.children[collection.name].hide_viewport:
                    hidden = True
        except:
            print("Error: Could not find collection: " + collection.name)

    return hidden


def _bake_image_name_for_object(obj):
    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA" and obj.TLM_ObjectProperties.tlm_atlas_pointer != "":
        return obj.TLM_ObjectProperties.tlm_atlas_pointer + "_baked"
    return obj.name + "_baked"


def _valid_prepack_atlas_object(obj):
    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode != "AtlasGroupA":
        return True

    atlas = obj.TLM_ObjectProperties.tlm_atlas_pointer
    if atlas == "":
        print("TLM Bake warning: skipping " + obj.name + " because it uses Atlas Group (Prepack) but has no atlas group assigned.")
        return False

    if atlas not in bpy.context.scene.TLM_AtlasList:
        print("TLM Bake warning: skipping " + obj.name + " because atlas group '" + atlas + "' does not exist.")
        return False

    return True


def _uv_channel_for_object(obj):
    if not obj.TLM_ObjectProperties.tlm_use_default_channel:
        return obj.TLM_ObjectProperties.tlm_uv_channel
    return "UVMap_Lightmap"


def _activate_lightmap_uv(obj):
    uv_channel = _uv_channel_for_object(obj)
    uv_layers = obj.data.uv_layers
    for i, layer in enumerate(uv_layers):
        if layer.name == uv_channel:
            uv_layers.active_index = i
            return True
    print("TLM Bake warning: UV layer '" + uv_channel + "' not found for " + obj.name)
    return False


def _expected_bake_image_names():
    names = set()
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use and not _is_hidden_from_lightmap(obj) and _valid_prepack_atlas_object(obj):
                names.add(_bake_image_name_for_object(obj))
    return names


def _activate_bake_image_nodes(obj):
    image_name = _bake_image_name_for_object(obj)
    image = bpy.data.images.get(image_name)
    if image is None:
        print("TLM Bake warning: image '" + image_name + "' not found for " + obj.name)
        return False

    found = False
    for slot in obj.material_slots:
        mat = slot.material
        if mat is None or not mat.use_nodes:
            continue

        nodes = mat.node_tree.nodes
        bake_node = nodes.get("Baked Image")
        if bake_node is None:
            bake_node = nodes.get("TLM_Lightmap")
        if bake_node is None or bake_node.type != "TEX_IMAGE":
            print("TLM Bake warning: no image bake node found for " + obj.name + " / " + mat.name)
            continue

        bake_node.image = image
        bake_node.select = True
        nodes.active = bake_node
        found = True

    if not found:
        print("TLM Bake warning: no active image bake target for " + obj.name)
    return found


def bake(plus_pass=0):

    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("Initializing lightmap baking.")

    for obj in bpy.context.scene.objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(False)

    iterNum = 0
    currentIterNum = 0

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:

            hidden = False

            #We check if the object is hidden
            if obj.hide_get():
                hidden = True
            if obj.hide_viewport:
                hidden = True
            if obj.hide_render:
                hidden = True

            #We check if the object's collection is hidden
            collections = obj.users_collection

            for collection in collections:

                if collection.hide_viewport:
                    hidden = True
                if collection.hide_render:
                    hidden = True
                    
                try:
                    if collection.name in bpy.context.scene.view_layers[0].layer_collection.children:
                        if bpy.context.scene.view_layers[0].layer_collection.children[collection.name].hide_viewport:
                            hidden = True
                except:
                    print("Error: Could not find collection: " + collection.name)

                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use and not hidden and _valid_prepack_atlas_object(obj):
                    iterNum = iterNum + 1

    if iterNum > 1:
        iterNum = iterNum - 1

    for obj in bpy.context.scene.objects:

        if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
            print("Checking visibility status for object and collections: " + obj.name)

        hidden = False

        #We check if the object is hidden
        if obj.hide_get():
            hidden = True
        if obj.hide_viewport:
            hidden = True
        if obj.hide_render:
            hidden = True

        #We check if the object's collection is hidden
        collections = obj.users_collection

        for collection in collections:

            if collection.hide_viewport:
                hidden = True
            if collection.hide_render:
                hidden = True
                
            try:
                if collection.name in bpy.context.scene.view_layers[0].layer_collection.children:
                    if bpy.context.scene.view_layers[0].layer_collection.children[collection.name].hide_viewport:
                        hidden = True
            except:
                print("Error: Could not find collection: " + collection.name)

        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use and not hidden and _valid_prepack_atlas_object(obj):

                scene = bpy.context.scene

                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                obs = bpy.context.view_layer.objects
                active = obs.active
                obj.hide_render = False
                scene.render.bake.use_clear = False
                _activate_lightmap_uv(obj)
                _activate_bake_image_nodes(obj)

                #os.system("cls")

                #if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                print("Baking " + str(currentIterNum) + "/" + str(iterNum) + " (" + str(round(currentIterNum/iterNum*100, 2)) + "%) : " + obj.name)
                #elapsed = build.sec_to_hours((time() - bpy.app.driver_namespace["tlm_start_time"]))
                #print("Baked: " + str(currentIterNum) + " | Left: " + str(iterNum-currentIterNum))
                elapsedSeconds = time() - bpy.app.driver_namespace["tlm_start_time"]
                bakedObjects = currentIterNum
                bakedLeft = iterNum-currentIterNum
                if bakedObjects == 0:
                    bakedObjects = 1
                averagePrBake = elapsedSeconds / bakedObjects
                remaining = averagePrBake * bakedLeft
                print("Elapsed time: " + str(round(elapsedSeconds, 2)) + "s | ETA remaining: " + str(round(remaining, 2)) + "s "+ "(" + str(datetime.timedelta(seconds=remaining)) + ")") #str(elapsed[0])

                if scene.TLM_EngineProperties.tlm_target == "vertex":
                    scene.render.bake.target = "VERTEX_COLORS"

                if scene.TLM_EngineProperties.tlm_lighting_mode == "combined" or scene.TLM_EngineProperties.tlm_lighting_mode == "combinedneutral":
                    print("Baking combined: Direct + Indirect")
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)
                elif scene.TLM_EngineProperties.tlm_lighting_mode == "indirect":
                    print("Baking combined: Indirect")
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"INDIRECT"}, margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)
                elif scene.TLM_EngineProperties.tlm_lighting_mode == "ao":
                    print("Baking combined: AO")
                    bpy.ops.object.bake(type="AO", margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)
                elif scene.TLM_EngineProperties.tlm_lighting_mode == "combinedao":

                    if bpy.app.driver_namespace["tlm_plus_mode"] == 1:
                        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)
                    elif bpy.app.driver_namespace["tlm_plus_mode"] == 2:
                        bpy.ops.object.bake(type="AO", margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)

                elif scene.TLM_EngineProperties.tlm_lighting_mode == "indirectao":

                    print("IndirAO")
                    
                    if bpy.app.driver_namespace["tlm_plus_mode"] == 1:
                        print("IndirAO: 1")
                        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"INDIRECT"}, margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)
                    elif bpy.app.driver_namespace["tlm_plus_mode"] == 2:
                        print("IndirAO: 2")
                        bpy.ops.object.bake(type="AO", margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)
                
                elif scene.TLM_EngineProperties.tlm_lighting_mode == "complete":
                    bpy.ops.object.bake(type="COMBINED", margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)
                else:
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=scene.TLM_EngineProperties.tlm_dilation_margin, use_clear=False)
                
                #Save between baking (to avoid lost textures)
                #TODO! ATLASGROUP!

                print("Saving textures - Stage 1")
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA" or obj.TLM_ObjectProperties.tlm_postpack_object:
                    print("Saving textures - Stage 1: Atlas Groups")
                    for image in bpy.data.images:
                        if image.name != "Render Result" or image.name != "Viewer Node":
                            if image.size[0] > 0 and image.size[1] > 0:
                                if image.name.startswith(obj.name):
                                    print("Saving texture: " + image.name)
                                    image.file_format = "HDR"
                                    image.save()
                            else:
                                print("Skipping texture: " + image.name)
                        else:
                            print("Skipping texture: " + image.name)
                else:
                    print("Saving textures - Stage 1: Objects")
                    for image in bpy.data.images:
                        if image.name != "Render Result" or image.name != "Viewer Node":
                            if image.size[0] > 0 and image.size[1] > 0:
                                if image.name.startswith(obj.name):
                                    print("Saving texture: " + image.name)
                                    image.file_format = "HDR"
                                    image.save()
                            else:
                                print("Skipping texture: " + image.name)
                        else:
                            print("Skipping texture: " + image.name)
                
                bpy.ops.object.select_all(action='DESELECT')
                currentIterNum = currentIterNum + 1

    print("Saving textures - Stage 2")
    expected_image_names = _expected_bake_image_names()
    for image in bpy.data.images:
        if image.name != "Render Result" or image.name != "Viewer Node":
            if image.name in expected_image_names:

                print("Saving baked texture: " + image.name)

                saveDir = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)
                bakemap_path = os.path.join(saveDir, image.name)
                filepath_ext = ".hdr"
                image.filepath_raw = bakemap_path + filepath_ext
                image.file_format = "HDR"
                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                    print("Saving to: " + image.filepath_raw)
                image.save()