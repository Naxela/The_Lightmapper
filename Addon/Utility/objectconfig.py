import bpy
from . import utility, functions, function_constants

def configure_world():
    pass

def configure_lights():
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            if obj.TLM_ObjectProperties.tlm_light_lightmap_use:
                if obj.TLM_ObjectProperties.tlm_light_casts_shadows:
                    bpy.data.lights[obj.name].cycles.cast_shadow = True
                else:
                    bpy.data.lights[obj.name].cycles.cast_shadow = False

                bpy.data.lights[obj.name].energy = bpy.data.lights[obj.name].energy * obj.TLM_ObjectProperties.tlm_light_intensity_scale

def configure_objects(self, scene):

    iterNum = 0
    currentIterNum = 0

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            for slot in obj.material_slots:
                if "." + slot.name + '_Original' in bpy.data.materials:
                    print("The material: " + slot.name + " shifted to " + "." + slot.name + '_Original')
                    slot.material = bpy.data.materials["." + slot.name + '_Original']

    for atlasgroup in scene.TLM_AtlasList:

        atlas = atlasgroup.name
        atlas_items = []

        bpy.ops.object.select_all(action='DESELECT')

        for obj in bpy.data.objects:
            #if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Atlas Group" and obj.TLM_ObjectProperties.tlm_atlas_pointer != "":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Atlas Group":

                uv_layers = obj.data.uv_layers
                if not "UVMap_Lightmap" in uv_layers:
                    print("UVMap made A")
                    uvmap = uv_layers.new(name="UVMap_Lightmap")
                    uv_layers.active_index = len(uv_layers) - 1
                else:
                    print("Existing found...skipping")
                    for i in range(0, len(uv_layers)):
                        if uv_layers[i].name == 'UVMap_Lightmap':
                            uv_layers.active_index = i
                            print("Lightmap shift A")
                            break

                atlas_items.append(obj)
                obj.select_set(True)

        if scene.TLM_SceneProperties.tlm_apply_on_unwrap:
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        if atlasgroup.tlm_atlas_lightmap_unwrap_mode == "SmartProject":
            print("Smart Project A for: " + str(atlas_items))
            for obj in atlas_items:
                print(obj.name + ": Active UV: " + obj.data.uv_layers[obj.data.uv_layers.active_index].name)
            bpy.context.view_layer.objects.active = atlas_items[0]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=atlasgroup.tlm_atlas_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
        elif atlasgroup.tlm_atlas_lightmap_unwrap_mode == "Lightmap":
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=atlasgroup.tlm_atlas_unwrap_margin)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
        else:
            print("Copied Existing A")
            pass #COPY EXISTING

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                iterNum = iterNum + 1

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                currentIterNum = currentIterNum + 1

                #Configure selection
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                obs = bpy.context.view_layer.objects
                active = obs.active

                #Provide material if none exists
                utility.preprocess_material(obj, scene)

                #UV Layer management here
                if not obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Atlas Group":
                    uv_layers = obj.data.uv_layers
                    if not "UVMap_Lightmap" in uv_layers:
                        print("UVMap made B")
                        uvmap = uv_layers.new(name="UVMap_Lightmap")
                        uv_layers.active_index = len(uv_layers) - 1

                        #if lightmap
                        if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Lightmap":
                            if scene.TLM_SceneProperties.tlm_apply_on_unwrap:
                                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                            bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin)
                        
                        #if smart project
                        elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Smart Project":
                            print("Smart Project B")
                            if scene.TLM_SceneProperties.tlm_apply_on_unwrap:
                                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='DESELECT')
                            bpy.ops.object.mode_set(mode='OBJECT')
                            bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
                        
                        elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Atlas Group":

                            print("ATLAS GROUP: " + obj.TLM_ObjectProperties.tlm_atlas_pointer)
                            
                        else: #if copy existing

                            print("Copied Existing B")

                            #Here we copy an existing map
                            pass
                    else:
                        print("Existing found...skipping")
                        for i in range(0, len(uv_layers)):
                            if uv_layers[i].name == 'UVMap_Lightmap':
                                uv_layers.active_index = i
                                print("Lightmap shift B")
                                break

                #print(x)

                #Sort out nodes
                for slot in obj.material_slots:

                    nodetree = slot.material.node_tree

                    outputNode = nodetree.nodes[0] #Presumed to be material output node

                    if(outputNode.type != "OUTPUT_MATERIAL"):
                        for node in nodetree.nodes:
                            if node.type == "OUTPUT_MATERIAL":
                                outputNode = node
                                break

                    mainNode = outputNode.inputs[0].links[0].from_node

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

                    #use albedo white
                    if scene.TLM_SceneProperties.tlm_baketime_material == "Blank":
                        if not len(mainNode.inputs[0].links) == 0:
                            ainput = mainNode.inputs[0].links[0]
                            aoutput = mainNode.inputs[0].links[0].from_node
                            nodetree.links.remove(aoutput.outputs[0].links[0])
                            mainNode.inputs[0].default_value = (1,0,0,1)
                        else:
                            mainNode.inputs[0].default_value = (1,0,0,1)

                    if (mainNode.type == "BSDF_PRINCIPLED"):
                        print("BSDF_Principled")
                        if scene.TLM_SceneProperties.tlm_directional_mode == "None":
                            if not len(mainNode.inputs[20].links) == 0:
                                ninput = mainNode.inputs[20].links[0]
                                noutput = mainNode.inputs[20].links[0].from_node
                                nodetree.links.remove(noutput.outputs[0].links[0])

                        #Clamp metallic
                        if(mainNode.inputs[4].default_value == 1 and scene.TLM_SceneProperties.tlm_clamp_metallic):
                            mainNode.inputs[4].default_value = 0.99
                        
                        #Unindent?
                        # node = slot.material.name[:-5] + '_baked'
                        # if not node in bpy.data.materials:
                        #     img_name = obj.name + '_baked'
                        #     mat = bpy.data.materials.new(name=node)
                        #     mat.use_nodes = True
                        #     nodes = mat.node_tree.nodes
                        #     img_node = nodes.new('ShaderNodeTexImage')
                        #     img_node.name = "Baked Image"
                        #     img_node.location = (100, 100)
                        #     img_node.image = bpy.data.images[img_name]
                        #     mat.node_tree.links.new(img_node.outputs[0], nodes['Principled BSDF'].inputs[0])
                        # else:
                        #     mat = bpy.data.materials[node]
                        #     nodes = mat.node_tree.nodes
                        #     nodes['Baked Image'].image = bpy.data.images[img_name]

                    if (mainNode.type == "BSDF_DIFFUSE"):
                        print("BSDF_Diffuse")

                for slot in obj.material_slots:

                    nodetree = bpy.data.materials[slot.name].node_tree
                    nodes = nodetree.nodes

                    #First search to get the first output material type
                    for node in nodetree.nodes:
                        if node.type == "OUTPUT_MATERIAL":
                            mainNode = node
                            break

                    #Fallback to get search
                    if not mainNode.type == "OUTPUT_MATERIAL":
                        mainNode = nodetree.nodes.get("Material Output")

                    #Last resort to first node in list
                    if not mainNode.type == "OUTPUT_MATERIAL":
                        mainNode = nodetree.nodes[0].inputs[0].links[0].from_node

                    for node in nodes:
                        if "LM" in node.name:
                            nodetree.links.new(node.outputs[0], mainNode.inputs[0])

                    for node in nodes:
                        if "Lightmap" in node.name:
                                nodes.remove(node)