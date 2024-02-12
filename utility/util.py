import bpy, shutil, os, json

def get_addon_path():

    #Get the path of the blender addon
    current_file_path = os.path.realpath(__file__)
    
    # Get the directory containing the current file, which is the addon's directory.
    addon_path = os.path.dirname(current_file_path)
    
    # Get the parent directory of the addon's directory.
    parent_path = os.path.dirname(addon_path)

    return parent_path

def ensureFilesave():

    currentSavePath = bpy.data.filepath

    if currentSavePath:
        return True
    else:
        return False

def copyBuildScript():
    module_path = os.path.join(get_addon_path(), "utility","_build_script.py")
    shutil.copy(module_path, bpy.path.abspath("//"))

def removeBuildScript():
    if os.path.exists(bpy.path.abspath("//_build_script.py")):
        os.remove(bpy.path.abspath("//_build_script.py"))

def load_library(asset_name):

    scriptDir = os.path.dirname(os.path.realpath(__file__))

    if bpy.data.filepath.endswith('TLMNode'): # Prevent load in library itself
        return

    data_path = os.path.abspath(os.path.join(get_addon_path(), "utility","TLMNode.blend"))
    data_names = [asset_name]

    # Import
    data_refs = data_names.copy()
    with bpy.data.libraries.load(data_path, link=False) as (data_from, data_to):
        data_to.node_groups = data_refs

    for ref in data_refs:
        ref.use_fake_user = True

def addTLMNode(mat):
    
    node_tree = mat.node_tree
    
    TLMNodeGroup = bpy.data.node_groups.get("TLM-Node")
    
    if TLMNodeGroup == None:
        load_library("TLM-Node")
        
    TLMNode = node_tree.nodes.new(type="ShaderNodeGroup")
    TLMNode.node_tree = bpy.data.node_groups["TLM-Node"]
    TLMNode.location = -400, 300
    TLMNode.name = "TLM-Node"
    
def addLightmapNode(mat, path):
    
    nodes = mat.node_tree.nodes
    
    image = bpy.data.images.load(path, check_existing=True)
    
    img_node = nodes.new('ShaderNodeTexImage')
    img_node.name = 'TLM-Lightmap'
    img_node.location = (100, 100)
    img_node.image = image

def linkLightmap(folder):
    #First make sure directory exists
    relative_directory = folder
    
    absolute_directory = bpy.path.abspath(relative_directory)
    manifest_file = os.path.join(absolute_directory,"manifest.json")

    if not os.path.exists(absolute_directory):
        print("No lightmap directory")
        return
    
    if not os.path.exists(manifest_file):
        print("No lightmap manifest")
        return
    
    with open(manifest_file, 'r') as file:
        # Load JSON data from file
        data = json.load(file)

    for index, key in enumerate(data):
        
        if index == 0 or key == "EXT":
            continue
        
        obj = bpy.data.objects.get(key)
        
        lightmap = data[key]

        obj["TLM-Lightmap"] = lightmap
    

def applyLightmap(folder, directly=False):
    
    #First make sure directory exists
    relative_directory = folder
    
    absolute_directory = bpy.path.abspath(relative_directory)
    manifest_file = os.path.join(absolute_directory,"manifest.json")
    
    if not os.path.exists(absolute_directory):
        print("No lightmap directory")
        return
    
    if not os.path.exists(manifest_file):
        print("No lightmap manifest")
        return
    
    with open(manifest_file, 'r') as file:
        # Load JSON data from file
        data = json.load(file)

    #print(data)
    
    for index, key in enumerate(data):
        
        if index == 0 or key == "EXT":
            continue
        
        obj = bpy.data.objects.get(key)
        
        extension = "." + data["EXT"]
        
        lightmap = data[key]
        
        lightmapPath = os.path.join(absolute_directory, lightmap + extension)
        
        #For each slot in the objects
        for slot in obj.material_slots:
            
            mat = slot.material
            
            #If there's a node setup
            if mat.use_nodes:
                
                if mat.node_tree.nodes.get("Principled BSDF") is not None:
                    
                    base_color = None
                    base_input = None
                    
                    if mat.node_tree.nodes.get("TLM-Node") is not None:
                        
                        #TODO: Store the connected base
                        #print(len(mat.node_tree.nodes.get("Principled BSDF").inputs[0].links))
                        #print(x)
                        
                        mat.node_tree.nodes.remove(mat.node_tree.nodes.get("TLM-Node"))
                        
                    if len(mat.node_tree.nodes.get("Principled BSDF").inputs[0].links) < 1:
                        print("BASE COLOR SET - NO LINKS")
                        base_color = mat.node_tree.nodes.get("Principled BSDF").inputs[0].default_value
                    else:
                        base_input = mat.node_tree.nodes.get("Principled BSDF").inputs[0].links[0]
                        print("BASE COLOR NOT SET - TEXTURE LINKS")
                        
                    if mat.node_tree.nodes.get("TLM-Lightmap") is not None:
                        
                        mat.node_tree.nodes.remove(mat.node_tree.nodes.get("TLM-Lightmap"))
                
                    addTLMNode(mat)
                    addLightmapNode(mat, lightmapPath)
                    
                    PrincipledNode = mat.node_tree.nodes.get("Principled BSDF")
                    TLMNode = mat.node_tree.nodes.get("TLM-Node")
                    LightmapNode = mat.node_tree.nodes.get("TLM-Lightmap")
                    
                    if directly:
                    
                        mat.node_tree.links.new(TLMNode.outputs[0], PrincipledNode.inputs[0])
                        mat.node_tree.links.new(LightmapNode.outputs[0], TLMNode.inputs[0])
                        
                    else:
                        
                        if base_color is not None:
                        
                            mat.node_tree.links.new(TLMNode.outputs[0], PrincipledNode.inputs[0])
                            mat.node_tree.links.new(LightmapNode.outputs[0], TLMNode.inputs[0])
                        
                            TLMNode.inputs[1].default_value = base_color
                            TLMNode.inputs[2].default_value = 1.0
                            
                        else:
                            
                            mat.node_tree.links.new(TLMNode.outputs[0], PrincipledNode.inputs[0])
                            mat.node_tree.links.new(LightmapNode.outputs[0], TLMNode.inputs[0])
                            mat.node_tree.links.new(TLMNode.inputs[1], base_input.from_socket)
                            TLMNode.inputs[2].default_value = 1.0
                        
                else:
                    
                    print("Not using principled setup!")
                    
            else:
                
                print("Not using nodes enabled")