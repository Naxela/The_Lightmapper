import bpy

def apply_materials():
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                uv_layers = obj.data.uv_layers
                uv_layers.active_index = 0

                decoding = False

                #Sort name
                for slot in obj.material_slots:
                    mat = slot.material
                    if mat.name.endswith('_temp'):
                        old = slot.material
                        slot.material = bpy.data.materials[old.name.split('_' + obj.name)[0]]

                #Apply materials
                for slot in obj.material_slots:
                    mat = slot.material

                    node_tree = mat.node_tree
                    nodes = mat.node_tree.nodes

                    #Find nodes
                    for node in nodes:
                        if node.name == "Baked Image":
                            lightmapNode = node
                            lightmapNode.location = -600, 300
                            lightmapNode.name = "TLM_Lightmap"

                    #Find output node
                    outputNode = nodes[0]
                    if(outputNode.type != "OUTPUT_MATERIAL"):
                        for node in node_tree.nodes:
                            if node.type == "OUTPUT_MATERIAL":
                                outputNode = node
                                break

                    #Find mainnode
                    mainNode = outputNode.inputs[0].links[0].from_node

                    #Add all nodes first
                    #Add lightmap multipliction texture
                    mixNode = node_tree.nodes.new(type="ShaderNodeMixRGB")
                    mixNode.name = "Lightmap_Multiplication"
                    mixNode.location = -300, 300
                    mixNode.blend_type = 'MULTIPLY'
                    mixNode.inputs[0].default_value = 1.0

                    UVLightmap = node_tree.nodes.new(type="ShaderNodeUVMap")
                    UVLightmap.uv_map = "UVMap_Lightmap"
                    UVLightmap.name = "Lightmap_UV"
                    UVLightmap.location = -1000, 300

                    #Add Basecolor node
                    if len(mainNode.inputs[0].links) == 0:
                        baseColorValue = mainNode.inputs[0].default_value
                        baseColorNode = node_tree.nodes.new(type="ShaderNodeRGB")
                        baseColorNode.outputs[0].default_value = baseColorValue
                        baseColorNode.location = ((mainNode.location[0] - 500, mainNode.location[1] - 300))
                        baseColorNode.name = "Lightmap_BasecolorNode_A"
                    else:
                        baseColorNode = mainNode.inputs[0].links[0].from_node
                        baseColorNode.name = "LM_P"

                    #Linking
                    mat.node_tree.links.new(lightmapNode.outputs[0], mixNode.inputs[1]) #Connect lightmap node to mixnode
                    mat.node_tree.links.new(baseColorNode.outputs[0], mixNode.inputs[2]) #Connect basecolor to pbr node
                    mat.node_tree.links.new(mixNode.outputs[0], mainNode.inputs[0]) #Connect mixnode to pbr node
                    mat.node_tree.links.new(UVLightmap.outputs[0], lightmapNode.inputs[0]) #Connect uvnode to lightmapnode


def exchangeLightmapsToPostfix(ext_postfix, new_postfix):
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                for slot in obj.material_slots:
                    mat = slot.material
                    node_tree = mat.node_tree
                    nodes = mat.node_tree.nodes

                    for node in nodes:
                        if node.name == "Baked Image" or node.name == "TLM_Lightmap":
                            img_name = node.image.filepath_raw
                            cutLen = len(ext_postfix + ".hdr")

                            #Simple way to sort out objects with multiple materials
                            if not new_postfix in img_name:
                                node.image.filepath_raw = img_name[:-cutLen] + new_postfix + ".hdr"

    for image in bpy.data.images:
        image.reload()