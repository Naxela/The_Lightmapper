import bpy, shutil, os, json, webbrowser, subprocess, platform
from ..denoiser import oidn
from ..ui.text_field import NX_Text_Display
from types import SimpleNamespace

# Get the path of the Blender add-on
def get_addon_path():
    current_file_path = os.path.realpath(__file__)
    addon_path = os.path.dirname(current_file_path)
    parent_path = os.path.dirname(addon_path)
    return parent_path

# Ensure the current Blender file is saved
def ensureFilesave():
    currentSavePath = bpy.data.filepath
    return bool(currentSavePath)

# Copy the build script to the current Blender file directory
def copyBuildScript():
    module_path = os.path.join(get_addon_path(), "utility", "_build_script.py")
    shutil.copy(module_path, bpy.path.abspath("//"))

# Remove the build script from the current Blender file directory
def removeBuildScript():
    script_path = bpy.path.abspath("//_build_script.py")
    if os.path.exists(script_path):
        os.remove(script_path)

# Open the lightmaps directory in the system file browser
def exploreLightmaps():
    relative_directory = "//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir
    absolute_directory = bpy.path.abspath(relative_directory)
    
    if not os.path.exists(absolute_directory):
        os.makedirs(absolute_directory)
    
    # Cross-platform folder opening
    system = platform.system()
    
    try:
        if system == "Windows":
            os.startfile(absolute_directory)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", absolute_directory])
        else:  # Linux and other Unix-like systems
            subprocess.Popen(["xdg-open", absolute_directory])
    except Exception as e:
        print(f"Error opening folder: {e}")

# Remove the entire lightmap folder
def removeLightmapFolder():
    relative_directory = "//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir
    absolute_directory = bpy.path.abspath(relative_directory)
    if os.path.exists(absolute_directory):
        shutil.rmtree(absolute_directory)

# Load a specific node group from the add-on's library blend file
def load_library(asset_name):
    if bpy.data.filepath.endswith('TLMNode'):
        return

    data_path = os.path.abspath(os.path.join(get_addon_path(), "utility", "TLMNode.blend"))
    data_names = [asset_name]

    with bpy.data.libraries.load(data_path, link=False) as (data_from, data_to):
        data_to.node_groups = data_names

    for ref in data_names:
        ref.use_fake_user = True

# Display a processing message while denoising
text_display = NX_Text_Display(x=10, y=12, message="Processing Denoising...", font_size=10)

# Post-process after the build, including denoising and UV reset
def postprocessBuild():

    if bpy.context.scene.TLM_SceneProperties.tlm_denoise_engine == "OIDN":
        text_display.toggle()

    denoiseList = []
    relative_directory = "//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir
    absolute_directory = bpy.path.abspath(relative_directory)
    manifest_file = os.path.join(absolute_directory, "manifest.json")

    if not os.path.exists(absolute_directory):
        print("No lightmap directory")
        return

    if not os.path.exists(manifest_file):
        print("No lightmap manifest")
        return

    with open(manifest_file, 'r') as file:
        data = json.load(file)

    for index, key in enumerate(data["lightmaps"]):

        print(key)
        print(data["lightmaps"][key])
        denoiseList.append(data["lightmaps"][key] + "." + data["ext"])

    # Denoising with OIDN if enabled
    if bpy.context.scene.TLM_SceneProperties.tlm_denoise_engine == "OIDN":
        denoiser_path = os.path.join(get_addon_path(), "binaries", "oidn")
        props = SimpleNamespace(
            tlm_oidn_path=denoiser_path,
            tlm_oidn_verbose=False,
            tlm_oidn_affinity=0,
            tlm_oidn_threads=0,
            tlm_oidn_maxmem=0
        )

        denoiser = oidn.TLM_OIDN_Denoise(props, denoiseList, absolute_directory)
        denoiser.denoise()
        denoiser.clean()
        text_display.toggle()
        text_display.remove()
        del denoiser

    # Reset UV layers for lightmapped objects
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
            mesh = obj.data
            mesh.uv_layers.active = mesh.uv_layers[0]
            mesh.uv_layers[0].active_render = True

    # KTX Conversion regardless of denoising
    if bpy.context.scene.TLM_SceneProperties.tlm_format == "KTX":

        ktx_outdir = os.path.join(absolute_directory, "KTX")

        if not os.path.exists(ktx_outdir):
            os.makedirs(ktx_outdir)

        ktx_path = os.path.join(get_addon_path(), "binaries", "ktx", "ktx.exe")
        if not os.path.exists(ktx_path):
            print(f"KTX tool not found at {ktx_path}")
            return

        for exr_file in os.listdir(absolute_directory):
            if exr_file.endswith(".exr"):

                exr_path = os.path.join(absolute_directory, exr_file)
                ktx_output_path = os.path.join(ktx_outdir, os.path.basename(exr_file).replace(".exr",".ktx2"))

                if bpy.context.scene.TLM_SceneProperties.tlm_tex_format == "F32":

                    if bpy.context.scene.TLM_SceneProperties.tlm_tex_compression:

                        ktx_command = [
                            ktx_path,
                            "create",
                            "--format", "R32G32B32A32_SFLOAT",
                            "--zstd", bpy.context.scene.TLM_SceneProperties.tlm_tex_compression_level,
                            exr_path,
                            ktx_output_path
                        ]

                    else:

                        ktx_command = [
                            ktx_path,
                            "create",
                            "--format", "R32G32B32A32_SFLOAT",
                            exr_path,
                            ktx_output_path
                        ]

                elif bpy.context.scene.TLM_SceneProperties.tlm_tex_format == "F16":

                    if bpy.context.scene.TLM_SceneProperties.tlm_tex_compression:

                        ktx_command = [
                            ktx_path,
                            "create",
                            "--format", "R16G16B16A16_SFLOAT",
                            "--zstd", bpy.context.scene.TLM_SceneProperties.tlm_tex_compression_level,
                            exr_path,
                            ktx_output_path
                        ]

                    else:

                        ktx_command = [
                            ktx_path,
                            "create",
                            "--format", "R16G16B16A16_SFLOAT",
                            exr_path,
                            ktx_output_path
                        ]

                elif bpy.context.scene.TLM_SceneProperties.tlm_tex_format == "VK":

                    if bpy.context.scene.TLM_SceneProperties.tlm_tex_compression:

                        ktx_command = [
                            ktx_path,
                            "create",
                            "--format", "B10G11R11_UFLOAT_PACK32",
                            "--zstd", bpy.context.scene.TLM_SceneProperties.tlm_tex_compression_level,
                            exr_path,
                            ktx_output_path
                        ]

                    else:

                        ktx_command = [
                            ktx_path,
                            "create",
                            "--format", "B10G11R11_UFLOAT_PACK32",
                            exr_path,
                            ktx_output_path
                        ]

                # ktx_command = [
                #     ktx_path,
                #     "create",
                #     "--format", "R32G32B32A32_SFLOAT",
                #     exr_path,
                #     ktx_output_path
                # ]

                # ktx_command = [
                #     ktx_path,
                #     "create",
                #     "--format", "B10G11R11_UFLOAT_PACK32",
                #     "--zstd", "18",
                #     exr_path,
                #     ktx_output_path
                # ]

                # Execute the KTX conversion command
                try:
                    subprocess.run(ktx_command, check=True)
                    print(f"Converted {exr_path} to {ktx_output_path} in KTX2 format.")
                except subprocess.CalledProcessError as e:
                    print(f"Error during KTX conversion for {exr_path}: {e}")

            # We also want to edit the EXR to a KTX
            manifest_path = os.path.join(absolute_directory, "manifest.json")
            shutil.copy(manifest_path, ktx_outdir)

            # Update the manifest file to reflect the new extension
            updated_manifest_path = os.path.join(ktx_outdir, "manifest.json")
            with open(updated_manifest_path, 'r') as file:
                manifest_data = json.load(file)

            manifest_data["ext"] = "ktx"

            with open(updated_manifest_path, 'w') as file:
                json.dump(manifest_data, file, indent=4)

# Add a TLM node group to the material
def addTLMNode(mat):
    node_tree = mat.node_tree
    if bpy.data.node_groups.get("TLM-Node") is None:
        load_library("TLM-Node")
    TLMNode = node_tree.nodes.new(type="ShaderNodeGroup")
    TLMNode.node_tree = bpy.data.node_groups["TLM-Node"]
    TLMNode.location = -200, 700
    TLMNode.name = "TLM-Node"

# Add a lightmap texture node to the material
def addLightmapNode(mat, path):
    nodes = mat.node_tree.nodes
    image = bpy.data.images.load(path, check_existing=True)
    img_node = nodes.new('ShaderNodeTexImage')
    img_node.name = 'TLM-Lightmap'
    img_node.location = (-700, 700)
    img_node.image = image

# Add a UV map node to the material
def addUVMapNode(mat):
    nodes = mat.node_tree.nodes
    uv_node = nodes.new('ShaderNodeUVMap')
    uv_node.name = 'TLM-UVMap'
    uv_node.location = (300, 300)
    uv_node.uv_map = "UVMap-Lightmap"

# Link the lightmaps to objects based on a manifest file
def linkLightmap(folder):
    relative_directory = folder
    absolute_directory = bpy.path.abspath(relative_directory)
    manifest_file = os.path.join(absolute_directory, "manifest.json")

    #Remove existing links
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            if obj.get("TLM_Lightmap"):
                del obj["TLM_Lightmap"]

    if not os.path.exists(absolute_directory):
        print("No lightmap directory")
        return

    if not os.path.exists(manifest_file):
        print("No lightmap manifest")
        return

    with open(manifest_file, 'r') as file:
        data = json.load(file)

    for index, key in enumerate(data["lightmaps"]):
        obj = bpy.data.objects.get(key)
        lightmap = data["lightmaps"][key]
        obj["TLM_Lightmap"] = lightmap

def linkMat():

    pass

# Configure the Cycles rendering engine based on scene properties
def configureEngine():
    scene = bpy.context.scene
    cycles = scene.cycles
    bpy.context.scene.render.engine = 'CYCLES'
    cycles.device = scene.TLM_SceneProperties.tlm_setting_renderer

    if cycles.device == "GPU":
        cycles.tile_size = 256
    else:
        cycles.tile_size = 32

    quality_settings = {
        "0": (32, 1),
        "1": (64, 2),
        "2": (512, 2),
        "3": (1024, 256),
        "4": (2048, 512)
    }

    quality = scene.TLM_SceneProperties.tlm_quality
    if quality in quality_settings:
        samples, bounces = quality_settings[quality]
        cycles.samples = samples
        cycles.max_bounces = bounces
        cycles.diffuse_bounces = bounces
        cycles.glossy_bounces = bounces
        cycles.transparent_max_bounces = bounces
        cycles.transmission_bounces = bounces
        cycles.volume_bounces = bounces
        cycles.caustics_reflective = quality == "4"
        cycles.caustics_refractive = quality == "4"

# Remove lightmaps from all mesh objects
def removeLightmap():
    print("Removing Lightmaps")

    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    continue

                node_tree = mat.node_tree
                PrincipledNode = node_tree.nodes.get("Principled BSDF")
                TLMNode = node_tree.nodes.get("TLM-Node")
                LightmapNode = node_tree.nodes.get("TLM-Lightmap")
                UVMapNode = node_tree.nodes.get("TLM-UVMap")

                print("Removing lightmap for obj " + obj.name)

                TLMNodeInput = None

                #If there's a TLMNode
                if TLMNode:

                    #i:Base
                    #i:Lightmap
                    #i:Factor
                    #o:Result

                    #print("Found TLMNode")

                    if TLMNode.inputs["Base"].is_linked:

                        print("Linked base TLMNode")

                        TLMNodeInput = TLMNode.inputs["Base"].links[0].from_socket

                if TLMNode:
                    node_tree.nodes.remove(TLMNode)
                if LightmapNode:
                    node_tree.nodes.remove(LightmapNode)
                if UVMapNode:
                    node_tree.nodes.remove(UVMapNode)

                if TLMNode and TLMNodeInput:
                    node_tree.links.new(TLMNodeInput, PrincipledNode.inputs["Base Color"])
                    print("Connected from: " + TLMNodeInput.name + " to " + PrincipledNode.inputs["Base Color"].name)

def reassign_materials():

    for obj in bpy.data.objects:

        for slot in obj.material_slots:

            mat = slot.material
            if not mat or not mat.use_nodes:
                continue

            inherited_mat = mat.get("TLM_InheritedMaterial")

            if inherited_mat:

                print("Inherited Material: " + obj.name + " : " + inherited_mat.name + " child: " + mat.name)

                slot.material = inherited_mat

def safe_node_link(tree, output_node, output_socket_name, input_node, input_socket_name):
    try:
        if output_socket_name in output_node.outputs and input_socket_name in input_node.inputs:
            tree.links.new(output_node.outputs[output_socket_name], input_node.inputs[input_socket_name])
        else:
            print(f"Warning: Socket not found: {output_socket_name} -> {input_socket_name}")
    except Exception as e:
        print(f"Error creating link: {e}")

# Apply lightmaps to objects based on a manifest file
def applyLightmap(folder):

    #Force update? Not needed?
    #bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

    # Check if lightmaps are already applied and toggle them accordingly
    if "Lightmapped" in bpy.context.scene:
        if bpy.context.scene["Lightmapped"]:
            print("Lightmaps are currently applied - removing lightmap")
            removeLightmap()
            bpy.context.scene["Lightmapped"] = False
            return
        else:
            print("Lightmaps are not applied - applying lightmap")
            bpy.context.scene["Lightmapped"] = True
    else:
        bpy.context.scene["Lightmapped"] = True
        print("Lightmaps are not applied initially - applying lightmap")

    # Apply lightmaps after setting the "Lightmapped" property to True
    relative_directory = folder
    absolute_directory = bpy.path.abspath(relative_directory)
    manifest_file = os.path.join(absolute_directory, "manifest.json")

    if not os.path.exists(absolute_directory):
        print("No lightmap directory")
        return

    if not os.path.exists(manifest_file):
        print("No lightmap manifest")
        return

    with open(manifest_file, 'r') as file:
        data = json.load(file)
        print(data)

    for index, key in enumerate(data["lightmaps"]):

        print("Trying to apply: " + data["lightmaps"][key])

        obj = bpy.data.objects.get(key)

        if data["ext"] == "ktx":

            extension = ".exr"

        else:

            extension = "." + data["ext"]

        lightmap = data["lightmaps"][key]
        lightmapPath = os.path.join(absolute_directory, lightmap + extension)

        #TODO - Weird crash to desktop, maybe when each material has been unique (ie. 033) and a baking was initiated
        #Also Decals => Mark as decal, thus copying the main/primary uv channel

        print("Check missing materials")
        if bpy.context.scene.TLM_SceneProperties.tlm_material_missing == "Create":
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

        if obj:
            print("Applying materials for: " + obj.name)
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    print("Not using mat nodes")
                    continue

                if bpy.context.scene.TLM_SceneProperties.tlm_material_multi_user == "Unique":

                    #If the material has more users, make it unique
                    if mat.users > 1:

                        original_material = mat
                        # Duplicate the material
                        new_mat = mat.copy()

                        new_mat["TLM_InheritedMaterial"] = original_material
                        # Rename the new material with the object's name as suffix
                        new_mat.name = f"{mat.name}-{obj.name}"
                        # Assign the new, uniquely named material to the slot
                        slot.material = new_mat

            #TODO - For now it needs to be named Principled BSDF, make it type based in the future. 
            if mat.node_tree.nodes.get("Principled BSDF"):
                print("Got principled BSDF: " + mat.name)
                base_color = None
                base_input_from_node = None
                base_input_from_socket_name = None

                if mat.node_tree.nodes.get("TLM-Node"):
                    print("Found TLM Node")
                    # Safely remove existing TLM-Node and its links
                    TLMNode_to_remove = mat.node_tree.nodes.get("TLM-Node")
                    for link in TLMNode_to_remove.inputs[0].links:
                        mat.node_tree.links.remove(link)
                    for link in TLMNode_to_remove.outputs[0].links:
                        mat.node_tree.links.remove(link)
                    mat.node_tree.nodes.remove(TLMNode_to_remove)

                if len(mat.node_tree.nodes.get("Principled BSDF").inputs[0].links) < 1:
                    print("No links - Adding default value base color")
                    base_color = mat.node_tree.nodes.get("Principled BSDF").inputs[0].default_value
                else:
                    base_input_link = mat.node_tree.nodes.get("Principled BSDF").inputs[0].links[0]
                    base_input_from_node = base_input_link.from_node
                    base_input_from_socket_name = base_input_link.from_socket.name
                    print("Found link - Adding link to base input - From node: " + base_input_from_node.name)

                if mat.node_tree.nodes.get("TLM-Lightmap"):
                    print("Removing TLM Lightmap?")
                    mat.node_tree.nodes.remove(mat.node_tree.nodes.get("TLM-Lightmap"))

                addTLMNode(mat)
                addLightmapNode(mat, lightmapPath)
                addUVMapNode(mat)

                PrincipledNode = mat.node_tree.nodes.get("Principled BSDF")
                TLMNode = mat.node_tree.nodes.get("TLM-Node")
                LightmapNode = mat.node_tree.nodes.get("TLM-Lightmap")
                UVMapNode = mat.node_tree.nodes.get("TLM-UVMap")

                if base_color is not None:
                    safe_node_link(mat.node_tree, TLMNode, "Result", PrincipledNode, "Base Color")
                    safe_node_link(mat.node_tree, LightmapNode, "Color", TLMNode, "Lightmap")
                    safe_node_link(mat.node_tree, UVMapNode, "UV", LightmapNode, "Vector")
                    TLMNode.inputs["Base"].default_value = base_color
                    TLMNode.inputs["Factor"].default_value = 1.0
                else:
                    safe_node_link(mat.node_tree, TLMNode, "Result", PrincipledNode, "Base Color")
                    safe_node_link(mat.node_tree, LightmapNode, "Color", TLMNode, "Lightmap")
                    safe_node_link(mat.node_tree, UVMapNode, "UV", LightmapNode, "Vector")
                    TLMNode.inputs["Factor"].default_value = 1.0

                    if base_input_from_node != TLMNode:
                        safe_node_link(mat.node_tree, base_input_from_node, base_input_from_socket_name, TLMNode, "Base")
                    else:
                        print("Warning: Attempted to connect TLMNode output back to its input (Base). Skipping.")
                        print("From: " + base_input.from_node.name + " to: " + TLMNode.name)
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active = obj
                        obj.select_set(True)

    print("Lightmap applied")
