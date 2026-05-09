import bpy.ops as O
import bpy, os, re, sys, importlib, struct, platform, subprocess, threading, string, bmesh, shutil, glob, uuid, time
from io import StringIO
from threading  import Thread
from queue import Queue, Empty
from dataclasses import dataclass
from dataclasses import field
from typing import List

###########################################################
###########################################################
# This set of utility functions are courtesy of LorenzWieseke
#
# Modified by Naxela
#   
# https://github.com/Naxela/The_Lightmapper/tree/Lightmap-to-GLB
###########################################################

class Node_Types:
    output_node = 'OUTPUT_MATERIAL'
    ao_node = 'AMBIENT_OCCLUSION'
    image_texture = 'TEX_IMAGE'
    pbr_node = 'BSDF_PRINCIPLED'
    diffuse = 'BSDF_DIFFUSE'
    mapping = 'MAPPING'
    normal_map = 'NORMAL_MAP'
    bump_map = 'BUMP'
    attr_node = 'ATTRIBUTE'

class Shader_Node_Types:
    emission = "ShaderNodeEmission"
    image_texture = "ShaderNodeTexImage"
    mapping = "ShaderNodeMapping"
    normal = "ShaderNodeNormalMap"
    ao = "ShaderNodeAmbientOcclusion"
    uv = "ShaderNodeUVMap"
    mix = "ShaderNodeMixRGB"

def tlm_set_active_uv_layer_by_name(mesh, name):
    """Select UV layer by name for unwrap/bake. Returns False if the layer does not exist."""
    layers = mesh.uv_layers
    for i, layer in enumerate(layers):
        if layer.name == name:
            layers.active_index = i
            return True
    return False


def tlm_active_uv_layer_name(mesh):
    layers = mesh.uv_layers
    if not layers:
        return None
    act = layers.active
    return act.name if act else None


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
    
    image.save()

def get_file_size(filepath):
    size = "Unpack Files"
    try:
        path = bpy.path.abspath(filepath)
        size = os.path.getsize(path)
        size /= 1024
    except:
        if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
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
    for obj in bpy.context.scene.objects:
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
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


###########################################################
###########################################################
# This utility function is modified from blender_xatlas
# and calls the object without any explicit object context
# thus allowing blender_xatlas to pack from background.
###########################################################
# Code is courtesy of mattedicksoncom
# Modified by Naxela
#
# https://github.com/mattedicksoncom/blender-xatlas/
###########################################################

def gen_safe_name():
    genId = uuid.uuid4().hex
    # genId = "u_" + genId.replace("-","_")
    return "u_" + genId

def _tlm_target_uv_name_from_object(obj):
    if hasattr(obj, "TLM_ObjectProperties"):
        props = obj.TLM_ObjectProperties
        if not props.tlm_use_default_channel and props.tlm_uv_channel:
            return props.tlm_uv_channel
    return "UVMap_Lightmap"

def _tlm_uv_diagnostic(layer):
    if layer is None or len(layer.data) == 0:
        return "missing-or-empty"

    xs = [loop.uv.x for loop in layer.data]
    ys = [loop.uv.y for loop in layer.data]
    signature = 0
    samples = []

    for index, loop in enumerate(layer.data):
        x = round(loop.uv.x, 6)
        y = round(loop.uv.y, 6)
        signature += int((x * 1000003) + (y * 917609)) * (index + 1)
        if index < 5:
            samples.append("(" + str(x) + "," + str(y) + ")")

    return (
        "loops=" + str(len(layer.data)) +
        ", bounds=(" + str(round(min(xs), 6)) + "," + str(round(min(ys), 6)) + ")-(" + str(round(max(xs), 6)) + "," + str(round(max(ys), 6)) + ")" +
        ", signature=" + str(signature) +
        ", samples=[" + ", ".join(samples) + "]"
    )

def _tlm_diag_path():
    base_path = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else bpy.app.tempdir
    return os.path.join(base_path, "tlm_xatlas_diag_latest.txt")

def _tlm_write_diag(path, lines):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as diag_file:
            diag_file.write("\n".join(lines))
            diag_file.write("\n")
    except Exception as e:
        print("TLM_XATLAS_DIAG: failed to write diagnostic report: " + str(e))

def _unwrap_objects_with_xatlas_python(objects):
    diag_lines = []
    diag_path = _tlm_diag_path()

    def diag(message):
        line = "TLM_XATLAS_DIAG: " + message
        diag_lines.append(line)
        print(line)
        _tlm_write_diag(diag_path, diag_lines)

    diag("report=" + diag_path)
    diag("blend=" + (bpy.data.filepath if bpy.data.filepath else "<unsaved>"))

    try:
        import numpy as np
        import xatlas
    except Exception as e:
        diag("IMPORT_FAILED: xatlas-python is not available in Blender Python: " + str(e))
        diag("Install xatlas-python with Blender's Python to use the Xatlas unwrap mode.")
        return False

    selected_objects = [
        selected_obj for selected_obj in objects
        if selected_obj and selected_obj.type == 'MESH'
    ]

    if not selected_objects:
        diag("skipped: no mesh objects were provided")
        return False

    diag("starting xatlas-python unwrap for " + str(len(selected_objects)) + " object(s): " + ", ".join([obj.name for obj in selected_objects]))

    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    combined_vertices = []
    combined_indices = []
    combined_loop_triangles = []
    target_layers = {}
    vertex_offset = 0

    for selected_obj in selected_objects:
        mesh = selected_obj.data
        target_uv = _tlm_target_uv_name_from_object(selected_obj)
        if target_uv not in mesh.uv_layers:
            mesh.uv_layers.new(name=target_uv)
        tlm_set_active_uv_layer_by_name(mesh, target_uv)
        diag("before " + selected_obj.name + " target=" + target_uv + " " + _tlm_uv_diagnostic(mesh.uv_layers.get(target_uv)))

        mesh.calc_loop_triangles()
        if len(mesh.loop_triangles) == 0:
            diag("skipped " + selected_obj.name + " because it has no triangles.")
            continue

        diag("mesh " + selected_obj.name + " vertices=" + str(len(mesh.vertices)) + ", polygons=" + str(len(mesh.polygons)) + ", loop_triangles=" + str(len(mesh.loop_triangles)) + ", matrix_world_translation=(" + str(round(selected_obj.matrix_world.translation.x, 6)) + "," + str(round(selected_obj.matrix_world.translation.y, 6)) + "," + str(round(selected_obj.matrix_world.translation.z, 6)) + ")")

        target_layers[selected_obj.name] = mesh.uv_layers.get(target_uv)

        for vertex in mesh.vertices:
            co = selected_obj.matrix_world @ vertex.co
            combined_vertices.append((co.x, co.y, co.z))

        for loop_tri in mesh.loop_triangles:
            combined_indices.append((
                loop_tri.vertices[0] + vertex_offset,
                loop_tri.vertices[1] + vertex_offset,
                loop_tri.vertices[2] + vertex_offset
            ))
            combined_loop_triangles.append((selected_obj, tuple(loop_tri.loops)))

        vertex_offset += len(mesh.vertices)

    if not combined_indices:
        _tlm_write_diag(diag_path, diag_lines)
        return False

    diag("combined mesh vertices=" + str(len(combined_vertices)) + ", triangles=" + str(len(combined_indices)))

    atlas = xatlas.Atlas()
    vertices = np.asarray(combined_vertices, dtype=np.float64)
    indices = np.asarray(combined_indices, dtype=np.uint32)
    atlas.add_mesh(vertices, indices)

    chart_options = xatlas.ChartOptions()
    pack_options = xatlas.PackOptions()

    try:
        atlas.generate(chart_options, pack_options, True)
    except TypeError:
        atlas.generate(chart_options, pack_options)

    _vertex_mapping, xatlas_indices, xatlas_uvs = atlas[0]
    diag("xatlas output indices=" + str(len(xatlas_indices)) + ", uvs=" + str(len(xatlas_uvs)) + ", vmapping=" + str(len(_vertex_mapping)))

    if len(xatlas_indices) != len(combined_loop_triangles):
        diag("WARNING triangle count mismatch, input=" + str(len(combined_loop_triangles)) + ", output=" + str(len(xatlas_indices)))

    for triangle_index, triangle_ref in enumerate(combined_loop_triangles):
        selected_obj, loop_indices = triangle_ref
        layer = target_layers.get(selected_obj.name)
        if layer is None:
            continue

        for corner_index, loop_index in enumerate(loop_indices):
            uv = xatlas_uvs[xatlas_indices[triangle_index][corner_index]]
            layer.data[loop_index].uv = (float(uv[0]), float(uv[1]))

    for selected_obj in selected_objects:
        selected_obj.data.update()
        target_uv = _tlm_target_uv_name_from_object(selected_obj)
        diag("after " + selected_obj.name + " target=" + target_uv + " " + _tlm_uv_diagnostic(selected_obj.data.uv_layers.get(target_uv)))

    diagnostics = {}
    for selected_obj in selected_objects:
        layer = selected_obj.data.uv_layers.get(_tlm_target_uv_name_from_object(selected_obj))
        diagnostics[selected_obj.name] = _tlm_uv_diagnostic(layer)

    names = list(diagnostics.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if diagnostics[names[i]] == diagnostics[names[j]]:
                diag("WARNING identical UV diagnostics for " + names[i] + " and " + names[j])

    _tlm_write_diag(diag_path, diag_lines)
    print("TLM_XATLAS_DIAG: wrote diagnostic report to " + diag_path)

    del atlas
    return True

def Unwrap_Lightmap_Group_Xatlas_2_headless_call(obj, use_python=False, objects=None):

    unwrap_objects = objects if objects is not None else [obj]

    if use_python:
        if _unwrap_objects_with_xatlas_python(unwrap_objects):
            return {'FINISHED'}
        return {'CANCELLED'}

    blender_xatlas = importlib.util.find_spec("blender_xatlas")

    if blender_xatlas is not None:
        import blender_xatlas
    else:
        print("TLM: Xatlas addon is not installed or enabled.")
        return 0

    target_uv = _tlm_target_uv_name_from_object(obj)
    sharedProperties = getattr(bpy.context.scene, "shared_properties", None)

    if hasattr(bpy.ops.object, "unwrap_lightmap_group_xatlas_2") and sharedProperties is not None:
        starting_active = bpy.context.view_layer.objects.active
        starting_mode = bpy.context.object.mode if bpy.context.object else "OBJECT"

        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        selected_objects = list(bpy.context.selected_objects)
        if not selected_objects:
            obj.select_set(True)
            selected_objects = [obj]

        sharedProperties.unwrapSelection = "SELECTED"
        sharedProperties.lightmapUVChoiceType = "NAME"
        sharedProperties.lightmapUVName = target_uv
        sharedProperties.mainUVChoiceType = "NAME"
        sharedProperties.mainUVName = "UVMap"
        sharedProperties.atlasLayout = "OVERLAP"

        bpy.context.view_layer.objects.active = obj
        for selected_obj in selected_objects:
            selected_obj.select_set(True)

        try:
            result = bpy.ops.object.unwrap_lightmap_group_xatlas_2()
        except Exception as e:
            print("TLM: Bundled blender_xatlas operator failed: " + str(e))
            result = 0

        bpy.ops.object.select_all(action="DESELECT")
        for selected_obj in selected_objects:
            selected_obj.select_set(True)
        if starting_active:
            bpy.context.view_layer.objects.active = starting_active
        if bpy.context.object and starting_mode != "OBJECT":
            try:
                bpy.ops.object.mode_set(mode=starting_mode)
            except Exception as e:
                print("TLM: Could not restore mode after xatlas unwrap: " + str(e))

        return result

    if not hasattr(blender_xatlas, "export_obj_simple"):
        print("TLM: Xatlas addon API is not compatible; missing unwrap operator and export_obj_simple.")
        return 0

    packOptions = bpy.context.scene.pack_tool
    chartOptions = bpy.context.scene.chart_tool

    sharedProperties = bpy.context.scene.shared_properties
    #sharedProperties.unwrapSelection

    context = bpy.context

    #save whatever mode the user was in
    startingMode = bpy.context.object.mode
    selected_objects = bpy.context.selected_objects

    #check something is actually selected
    #external function/operator will select them
    if len(selected_objects) == 0:
        print("Nothing Selected")
        self.report({"WARNING"}, "Nothing Selected, please select Something")
        return {'FINISHED'}

    #store the names of objects to be lightmapped
    rename_dict = dict()
    safe_dict = dict()

    #make sure all the objects have ligthmap uvs
    for obj in selected_objects:
        if obj.type == 'MESH':
            safe_name = gen_safe_name();
            rename_dict[obj.name] = (obj.name,safe_name)
            safe_dict[safe_name] = obj.name
            context.view_layer.objects.active = obj
            if obj.data.users > 1:
                obj.data = obj.data.copy() #make single user copy
            uv_layers = obj.data.uv_layers

            #setup the lightmap uvs
            uvName = "UVMap_Lightmap"
            if sharedProperties.lightmapUVChoiceType == "NAME":
                uvName = sharedProperties.lightmapUVName
            elif sharedProperties.lightmapUVChoiceType == "INDEX":
                if sharedProperties.lightmapUVIndex < len(uv_layers):
                    uvName = uv_layers[sharedProperties.lightmapUVIndex].name

            if not uvName in uv_layers:
                uvmap = uv_layers.new(name=uvName)
                uv_layers.active_index = len(uv_layers) - 1
            else:
                for i in range(0, len(uv_layers)):
                    if uv_layers[i].name == uvName:
                        uv_layers.active_index = i
            obj.select_set(True)

    #save all the current edges
    if sharedProperties.packOnly:
        edgeDict = dict()
        for obj in selected_objects:
            if obj.type == 'MESH':
                tempEdgeDict = dict()
                tempEdgeDict['object'] = obj.name
                tempEdgeDict['edges'] = []
                print(len(obj.data.edges))
                for i in range(0,len(obj.data.edges)):
                    setEdge = obj.data.edges[i]
                    tempEdgeDict['edges'].append(i)
                edgeDict[obj.name] = tempEdgeDict

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='FIXED', ngon_method='BEAUTY')
    else:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='FIXED', ngon_method='BEAUTY')

    bpy.ops.object.mode_set(mode='OBJECT')

    #Create a fake obj export to a string
    #Will strip this down further later
    fakeFile = StringIO()
    blender_xatlas.export_obj_simple.save(
        rename_dict=rename_dict,
        context=bpy.context,
        filepath=fakeFile,
        mainUVChoiceType=sharedProperties.mainUVChoiceType,
        uvIndex=sharedProperties.mainUVIndex,
        uvName=sharedProperties.mainUVName,
        use_selection=True,
        use_animation=False,
        use_mesh_modifiers=True,
        use_edges=True,
        use_smooth_groups=False,
        use_smooth_groups_bitflags=False,
        use_normals=True,
        use_uvs=True,
        use_materials=False,
        use_triangles=False,
        use_nurbs=False,
        use_vertex_groups=False,
        use_blen_objects=True,
        group_by_object=False,
        group_by_material=False,
        keep_vertex_order=False,
    )

    #print just for reference
    # print(fakeFile.getvalue())

    #get the path to xatlas
    #file_path = os.path.dirname(os.path.abspath(__file__))
    scriptsDir = os.path.join(bpy.utils.user_resource('SCRIPTS'), "addons")
    file_path = os.path.join(scriptsDir, "blender_xatlas")
    if platform.system() == "Windows":
        xatlas_path = os.path.join(file_path, "xatlas", "xatlas-blender.exe")
    elif platform.system() == "Linux":
        xatlas_path = os.path.join(file_path, "xatlas", "xatlas-blender")
        #need to set permissions for the process on linux
        subprocess.Popen(
            'chmod u+x "' + xatlas_path + '"',
            shell=True
        )

    #setup the arguments to be passed to xatlas-------------------
    arguments_string = ""
    for argumentKey in packOptions.__annotations__.keys():
        key_string = str(argumentKey)
        if argumentKey is not None:
            print(getattr(packOptions,key_string))
            attrib = getattr(packOptions,key_string)
            if type(attrib) == bool:
                if attrib == True:
                    arguments_string = arguments_string + " -" + str(argumentKey)
            else:
                arguments_string = arguments_string + " -" + str(argumentKey) + " " + str(attrib)

    for argumentKey in chartOptions.__annotations__.keys():
        if argumentKey is not None:
            key_string = str(argumentKey)
            print(getattr(chartOptions,key_string))
            attrib = getattr(chartOptions,key_string)
            if type(attrib) == bool:
                if attrib == True:
                    arguments_string = arguments_string + " -" + str(argumentKey)
            else:
                arguments_string = arguments_string + " -" + str(argumentKey) + " " + str(attrib)

    #add pack only option
    if sharedProperties.packOnly:
        arguments_string = arguments_string + " -packOnly"

    arguments_string = arguments_string + " -atlasLayout" + " " + sharedProperties.atlasLayout

    print(arguments_string)
    #END setup the arguments to be passed to xatlas-------------------

    #RUN xatlas process
    xatlas_process = subprocess.Popen(
        r'"{}"'.format(xatlas_path) + ' ' + arguments_string,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True
    )

    print(xatlas_path)

    #shove the fake file in stdin
    stdin = xatlas_process.stdin
    value = bytes(fakeFile.getvalue() + "\n", 'UTF-8') #The \n is needed to end the input properly
    stdin.write(value)
    stdin.flush()

    #Get the output from xatlas
    outObj = ""
    while True:
        output = xatlas_process.stdout.readline()
        if not output:
                break
        outObj = outObj + (output.decode().strip() + "\n")

    #the objects after xatlas processing
    # print(outObj)


    #Setup for reading the output
    @dataclass
    class uvObject:
        obName: string = ""
        uvArray: List[float] = field(default_factory=list)
        faceArray: List[int] = field(default_factory=list)

    convertedObjects = []
    uvArrayComplete = []


    #search through the out put for STARTOBJ
    #then start reading the objects
    obTest = None
    startRead = False
    for line in outObj.splitlines():

        line_split = line.split()

        if not line_split:
            continue

        line_start = line_split[0]  # we compare with this a _lot_
        # print(line_start)
        if line_start == "STARTOBJ":
            print("Start reading the objects----------------------------------------")
            startRead = True
            # obTest = uvObject()

        if startRead:
            #if it's a new obj
            if line_start == 'o':
                #if there is already an object append it
                if obTest is not None:
                    convertedObjects.append(obTest)

                obTest = uvObject() #create new uv object
                obTest.obName = line_split[1]

            if obTest is not None:
                #the uv coords
                if line_start == 'vt':
                    newUv = [float(line_split[1]),float(line_split[2])]
                    obTest.uvArray.append(newUv)
                    uvArrayComplete.append(newUv)

                #the face coords index
                #faces are 1 indexed
                if line_start == 'f':
                    #vert/uv/normal
                    #only need the uvs
                    newFace = [
                        int(line_split[1].split("/")[1]),
                        int(line_split[2].split("/")[1]),
                        int(line_split[3].split("/")[1])
                    ]
                    obTest.faceArray.append(newFace)

    #append the final object
    convertedObjects.append(obTest)
    print(convertedObjects)


    #apply the output-------------------------------------------------------------
    #copy the uvs to the original objects
    # objIndex = 0
    print("Applying the UVs----------------------------------------")
    # print(convertedObjects)
    for importObject in convertedObjects:
        bpy.ops.object.select_all(action='DESELECT')

        obTest = importObject
        obTest.obName = safe_dict[obTest.obName] #probably shouldn't just replace it
        bpy.context.scene.objects[obTest.obName].select_set(True)
        context.view_layer.objects.active = bpy.context.scene.objects[obTest.obName]
        bpy.ops.object.mode_set(mode = 'OBJECT')

        obj = bpy.context.active_object
        me = obj.data
        #convert to bmesh to create the new uvs
        bm = bmesh.new()
        bm.from_mesh(me)

        uv_layer = bm.loops.layers.uv.verify()

        nFaces = len(bm.faces)
        #need to ensure lookup table for some reason?
        if hasattr(bm.faces, "ensure_lookup_table"):
            bm.faces.ensure_lookup_table()

        #loop through the faces
        for faceIndex in range(nFaces):
            faceGroup = obTest.faceArray[faceIndex]

            bm.faces[faceIndex].loops[0][uv_layer].uv = (
                uvArrayComplete[faceGroup[0] - 1][0],
                uvArrayComplete[faceGroup[0] - 1][1])

            bm.faces[faceIndex].loops[1][uv_layer].uv = (
                uvArrayComplete[faceGroup[1] - 1][0],
                uvArrayComplete[faceGroup[1] - 1][1])

            bm.faces[faceIndex].loops[2][uv_layer].uv = (
                uvArrayComplete[faceGroup[2] - 1][0],
                uvArrayComplete[faceGroup[2] - 1][1])

            # objIndex = objIndex + 3

        # print(objIndex)
        #assign the mesh back to the original mesh
        bm.to_mesh(me)
    #END apply the output-------------------------------------------------------------


    #Start setting the quads back again-------------------------------------------------------------
    if sharedProperties.packOnly:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        for edges in edgeDict:
            edgeList = edgeDict[edges]
            currentObject = bpy.context.scene.objects[edgeList['object']]
            bm = bmesh.new()
            bm.from_mesh(currentObject.data)
            if hasattr(bm.edges, "ensure_lookup_table"):
                bm.edges.ensure_lookup_table()

            #assume that all the triangulated edges come after the original edges
            newEdges = []
            for edge in range(len(edgeList['edges']), len(bm.edges)):
                newEdge = bm.edges[edge]
                newEdge.select = True
                newEdges.append(newEdge)

            bmesh.ops.dissolve_edges(bm, edges=newEdges, use_verts=False, use_face_split=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            bm.to_mesh(currentObject.data)
            bm.free()
            bpy.ops.object.mode_set(mode='EDIT')

    #End setting the quads back again-------------------------------------------------------------

    #select the original objects that were selected
    for objectName in rename_dict:
        if objectName[0] in bpy.context.scene.objects:
            current_object = bpy.context.scene.objects[objectName[0]]
            current_object.select_set(True)
            context.view_layer.objects.active = current_object

    bpy.ops.object.mode_set(mode=startingMode)

    print("Finished Xatlas----------------------------------------")
    return {'FINISHED'}

def transfer_assets(copy, source, destination):
    for filename in glob.glob(os.path.join(source, '*.*')):
        try:
            shutil.copy(filename, destination)
        except shutil.SameFileError:
            pass

def transfer_load():
    load_folder = bpy.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_SceneProperties.tlm_load_folder))
    lightmap_folder = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)
    print(load_folder)
    print(lightmap_folder)
    transfer_assets(True, load_folder, lightmap_folder)
