import bpy, os, json, math
#
def createBakeImages(obj, setActive):
    
    img_name = "TLM-" + obj.name
    
    if not img_name in bpy.data.images:

        #bpy.data.scenes["Scene"].TLM_SceneProperties.tlm_setting_scale

        resolution = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) / int(bpy.context.scene.TLM_SceneProperties.tlm_setting_scale) 
        
        image = bpy.data.images.new(img_name, int(resolution), int(resolution), alpha=True, float_buffer=True)
    
    #For each slot in the objects
    for slot in obj.material_slots:
        
        mat = slot.material
        
        #If there's a node setup
        #OBS! WE ONLY WANT 1 TEXTURE pr. OBJECT!
        if mat.use_nodes:
            
            nodes = mat.node_tree.nodes
            
            if "TLM-Lightmap" in nodes:
                
                #bk = nodes["TLM-Lightmap"]
                
                nodes.get("TLM-Lightmap").image = bpy.data.images[img_name]
                
                nodes.active = nodes.get("TLM-Lightmap")
                
                #Set active
                
            else:
                
                img_node = nodes.new('ShaderNodeTexImage')
                img_node.name = 'TLM-Lightmap'
                img_node.location = (100, 100)
                img_node.image = bpy.data.images[img_name]
                
                nodes.active = nodes.get("TLM-Lightmap")
                #Set active
            
        else:
            
            print("No nodes in: " + obj.name + " w/ " + mat.name)
            
def bakeObject(obj):
    # Ensure correct context setup
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Attempt a direct bake call (this might need context adjustments)
    print("[TLM]:1:Baking " + obj.name, flush=True)
    try:
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=16, use_clear=True)
    except RuntimeError as e:
        print(f"Error baking {obj.name}: {e}")

def createLinkProperties(obj):
    
    for slot in obj.material_slots:
        
        mat = slot.material
        
        #If there's a node setup
        if mat.use_nodes:
            
            for node in mat.node_tree.nodes:
                
                if node.name == "TLM-Lightmap":
                    
                    image = mat.node_tree.nodes.get("TLM-Lightmap").image
                    
                    obj["TLM-Lightmap"] = image.name
                    
                    print("Property for " + obj.name + " set to: " + image.name)
    

def saveLightmaps(obj):
    
    #First make sure directory exists
    relative_directory = "//Lightmaps"
    
    absolute_directory = bpy.path.abspath(relative_directory)
    if not os.path.exists(absolute_directory):
        os.makedirs(absolute_directory)
    
    #For each slot in the objects
    for slot in obj.material_slots:
        
        mat = slot.material
        
        #If there's a node setup
        if mat.use_nodes:
            
            for node in mat.node_tree.nodes:
                
                if node.name == "TLM-Lightmap":
                    
                    image = mat.node_tree.nodes.get("TLM-Lightmap").image
                    
                    file_extension = ".hdr"
                    
                    image_path = os.path.join(absolute_directory, image.name + file_extension)
                    
                    if image is not None:
                        # Save the image
                        if not os.path.exists(image_path):

                            bpy.context.scene.render.image_settings.file_format = 'HDR'
                            bpy.context.scene.render.image_settings.color_depth = '32'
                            # Save the image
                            image.save_render(filepath=image_path, scene=bpy.context.scene)

                            #image.save_render(filepath=image_path)

                            print(f"Image saved to {image_path}")
                        else:
                            print(f"Image already exist at {image_path}")
                        
                    else:
                        print(f"Image '{image_name}' not found.")

#What this does is create a group named glTF Material Output that can be parsed
#TODO - Use Occlusion input at first, but see if a custom Lightmap output can be read
#TODO - Nevermind, just create a custom lightmap property per object (path)
#TODO - Check if materials can have properties?
#TODO - Apply the material property as a custom property "TLM-Lightmap" : "TLM-ObjName"
#- Inside NX Engine, iterate material. The extension + path is applied automatically
def applyLightmap(obj):
    
    #For each slot in the objects
    for slot in obj.material_slots:
        
        mat = slot.material
        
        #If there's a node setup
        if mat.use_nodes:
            
            if mat.node_tree.nodes.get("TLM-Lightmap") is not None and mat.node_tree.nodes.get("Principled BSDF") is not None:
                
                mat.node_tree.links.new(mat.node_tree.nodes.get("TLM-Lightmap").outputs[0], mat.node_tree.nodes.get("Principled BSDF").inputs[0])

def compileManifest(obj_list):

    print("Compiling manifest")

    #First make sure directory exists
    relative_directory = "//Lightmaps"
    
    absolute_directory = bpy.path.abspath(relative_directory)
    if not os.path.exists(absolute_directory):
        os.makedirs(absolute_directory)

    file_path = os.path.join(absolute_directory, "manifest.json")

    manifest = {}

    manifest["EXT"] = "hdr"

    for index, obj_name in enumerate(obj_list):
        obj = bpy.data.objects[obj_name]

        if obj["TLM-Lightmap"]:

            manifest[obj.name] = obj["TLM-Lightmap"]

    print(manifest)

    with open(file_path, "w") as f:
        json.dump(manifest, f)

####################################################
################## FUNCTION RUN ####################

#TODO - SHOULD IT ACTUALLY BAKE PER MATERIAL PER OBJECT?
#RECOMMENDED WORKFLOW - MERGE TO SINGULAR MATERIAL PBR SETUP
#ESPECIALLY SINCE IT'S INTENDED FOR STATIC SETUP

def bakeObjectsAndReportProgress(obj_list):

    print("[TLM]:1:Starting bake...", flush=True)
    print(f"[TLM]:0:0.0", flush=True)
    print(obj_list)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"

    total = len(obj_list)
    for index, obj_name in enumerate(obj_list):
        obj = bpy.data.objects[obj_name]
        createBakeImages(obj, True)
        bakeObject(obj)
        saveLightmaps(obj)
        print(f"[TLM]:0: {(index + 1) / total}", flush=True)
        
    for index, obj_name in enumerate(obj_list):
        obj = bpy.data.objects[obj_name]
        
        #applyLightmap(obj)
        
        createLinkProperties(obj)

    compileManifest(obj_list)

    print("[TLM]:1:Finished bake...", flush=True)

obj_list = []
    
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
            obj_list.append(obj.name)

bakeObjectsAndReportProgress(obj_list)