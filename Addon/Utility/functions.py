import bpy.ops as O
import bpy, os
from .function_constants import *

def select_object(self,obj):
    C = bpy.context
    try:
        O.object.select_all(action='DESELECT')
        C.view_layer.objects.active = obj
        obj.select_set(True)
    except:
        self.report({'INFO'},"Object not in View Layer")


def select_obj_by_mat(self,mat):
    D = bpy.data
    for obj in D.objects:
        if obj.type == "MESH":
            object_materials = [
                slot.material for slot in obj.material_slots]
            if mat in object_materials:
                select_object(self,obj)


def save_image(image):

    filePath = bpy.data.filepath
    path = os.path.dirname(filePath)

    try:
        os.mkdir(path + "/tex")
    except FileExistsError:
        pass

    try:
        os.mkdir(path + "/tex/" + str(image.size[0]))
    except FileExistsError:
        pass

    if image.file_format == "JPEG" :
        file_ending = ".jpg"
    elif image.file_format == "PNG" :
        file_ending = ".png"
    
    savepath = path + "/tex/" + \
        str(image.size[0]) + "/" + image.name + file_ending

    image.filepath_raw = savepath
    
    # if "Normal" in image.name:
    #     bpy.context.scene.render.image_settings.quality = 90
    #     image.save_render( filepath = image.filepath_raw, scene = bpy.context.scene )
    # else:
    image.save()

  


def get_file_size(filepath):
    size = "Unpack Files"
    try:
        path = bpy.path.abspath(filepath)
        size = os.path.getsize(path)
        size /= 1024
    except:
        print("error getting file path for " + filepath)
        
    return (size)


def scale_image(image, newSize):
    if (image.org_filepath != ''):
        image.filepath = image.org_filepath

    image.org_filepath = image.filepath
    image.scale(newSize[0], newSize[1])
    save_image(image)


def check_only_one_pbr(self,material):
    check_ok = True
    # get pbr shader
    nodes = material.node_tree.nodes
    pbr_node_type = Node_Types.pbr_node
    pbr_nodes = find_node_by_type(nodes,pbr_node_type)

    # check only one pbr node
    if len(pbr_nodes) == 0:
        self.report({'INFO'}, 'No PBR Shader Found')
        check_ok = False

    if len(pbr_nodes) > 1:
        self.report({'INFO'}, 'More than one PBR Node found ! Clean before Baking.')
        check_ok = False

    return check_ok

# is material already the baked one
def check_is_org_material(self,material):     
    check_ok = True   
    if "_Bake" in material.name:
        self.report({'INFO'}, 'Change back to org. Material')
        check_ok = False
    
    return check_ok


def clean_empty_materials(self):
    for obj in bpy.data.objects:
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                print("Removed Empty Materials from " + obj.name)
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.ops.object.material_slot_remove()

def get_pbr_inputs(pbr_node):

    base_color_input = pbr_node.inputs["Base Color"]
    metallic_input = pbr_node.inputs["Metallic"]
    specular_input = pbr_node.inputs["Specular"]
    roughness_input = pbr_node.inputs["Roughness"]
    normal_input = pbr_node.inputs["Normal"]

    pbr_inputs = {"base_color_input":base_color_input, "metallic_input":metallic_input,"specular_input":specular_input,"roughness_input":roughness_input,"normal_input":normal_input}
    return pbr_inputs    

def find_node_by_type(nodes, node_type):
    nodes_found = [n for n in nodes if n.type == node_type]
    return nodes_found

def find_node_by_type_recusivly(material, note_to_start, node_type, del_nodes_inbetween=False):
    nodes = material.node_tree.nodes
    if note_to_start.type == node_type:
        return note_to_start

    for input in note_to_start.inputs:
        for link in input.links:
            current_node = link.from_node
            if (del_nodes_inbetween and note_to_start.type != Node_Types.normal_map and note_to_start.type != Node_Types.bump_map):
                nodes.remove(note_to_start)
            return find_node_by_type_recusivly(material, current_node, node_type, del_nodes_inbetween)


def find_node_by_name_recusivly(node, idname):
    if node.bl_idname == idname:
        return node

    for input in node.inputs:
        for link in input.links:
            current_node = link.from_node
            return find_node_by_name_recusivly(current_node, idname)

def make_link(material, socket1, socket2):
    links = material.node_tree.links
    links.new(socket1, socket2)


def add_gamma_node(material, pbrInput):
    nodeToPrincipledOutput = pbrInput.links[0].from_socket

    gammaNode = material.node_tree.nodes.new("ShaderNodeGamma")
    gammaNode.inputs[1].default_value = 2.2
    gammaNode.name = "Gamma Bake"

    # link in gamma
    make_link(material, nodeToPrincipledOutput, gammaNode.inputs["Color"])
    make_link(material, gammaNode.outputs["Color"], pbrInput)


def remove_gamma_node(material, pbrInput):
    nodes = material.node_tree.nodes
    gammaNode = nodes.get("Gamma Bake")
    nodeToPrincipledOutput = gammaNode.inputs[0].links[0].from_socket

    make_link(material, nodeToPrincipledOutput, pbrInput)
    material.node_tree.nodes.remove(gammaNode)

def apply_ao_toggle(self,context): 
    all_materials = bpy.data.materials
    ao_toggle = context.scene.toggle_ao
    for mat in all_materials:
        nodes = mat.node_tree.nodes
        ao_node = nodes.get("AO Bake")
        if ao_node is not None:
            if ao_toggle:
                emission_setup(mat,ao_node.outputs["Color"])
            else:
                pbr_node = find_node_by_type(nodes,Node_Types.pbr_node)[0]   
                remove_node(mat,"Emission Bake")
                reconnect_PBR(mat, pbr_node)
        

def emission_setup(material, node_output):
    nodes = material.node_tree.nodes
    emission_node = add_node(material,Shader_Node_Types.emission,"Emission Bake")

    # link emission to whatever goes into current pbrInput
    emission_input = emission_node.inputs[0]
    make_link(material, node_output, emission_input)

    # link emission to materialOutput
    surface_input = nodes.get("Material Output").inputs[0]
    emission_output = emission_node.outputs[0]
    make_link(material, emission_output, surface_input)

def link_pbr_to_output(material,pbr_node):
    nodes = material.node_tree.nodes
    surface_input = nodes.get("Material Output").inputs[0]
    make_link(material,pbr_node.outputs[0],surface_input)

    
def reconnect_PBR(material, pbrNode):
    nodes = material.node_tree.nodes
    pbr_output = pbrNode.outputs[0]
    surface_input = nodes.get("Material Output").inputs[0]
    make_link(material, pbr_output, surface_input)

def mute_all_texture_mappings(material, do_mute):
    nodes = material.node_tree.nodes
    for node in nodes:
        if node.bl_idname == "ShaderNodeMapping":
            node.mute = do_mute

def add_node(material,shader_node_type,node_name):
    nodes = material.node_tree.nodes
    new_node = nodes.get(node_name)
    if new_node is None:
        new_node = nodes.new(shader_node_type)
        new_node.name = node_name
        new_node.label = node_name
    return new_node

def remove_node(material,node_name):
    nodes = material.node_tree.nodes
    node = nodes.get(node_name)
    if node is not None:
        nodes.remove(node)

def lightmap_to_ao(material,lightmap_node):
        nodes = material.node_tree.nodes
        # -----------------------AO SETUP--------------------#
        # create group data
        gltf_settings = bpy.data.node_groups.get('glTF Settings')
        if gltf_settings is None:
            bpy.data.node_groups.new('glTF Settings', 'ShaderNodeTree')
        
        # add group to node tree
        ao_group = nodes.get('glTF Settings')
        if ao_group is None:
            ao_group = nodes.new('ShaderNodeGroup')
            ao_group.name = 'glTF Settings'
            ao_group.node_tree = bpy.data.node_groups['glTF Settings']

        # create group inputs
        if ao_group.inputs.get('Occlusion') is None:
            ao_group.inputs.new('NodeSocketFloat','Occlusion')

        # mulitply to control strength
        mix_node = add_node(material,Shader_Node_Types.mix,"Adjust Lightmap")
        mix_node.blend_type = "MULTIPLY"
        mix_node.inputs["Fac"].default_value = 1
        mix_node.inputs["Color2"].default_value = [3,3,3,1]

        # position node
        ao_group.location = (lightmap_node.location[0]+600,lightmap_node.location[1])
        mix_node.location = (lightmap_node.location[0]+300,lightmap_node.location[1])
    
        make_link(material,lightmap_node.outputs['Color'],mix_node.inputs['Color1'])
        make_link(material,mix_node.outputs['Color'],ao_group.inputs['Occlusion'])