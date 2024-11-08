import bpy, shutil, os, json, webbrowser, subprocess
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
    webbrowser.open(absolute_directory)

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

                ktx_command = [
                    ktx_path,
                    "create",
                    "--format", "R32G32B32A32_SFLOAT",
                    exr_path,
                    ktx_output_path
                ]

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
    TLMNode.location = -400, 300
    TLMNode.name = "TLM-Node"

# Add a lightmap texture node to the material
def addLightmapNode(mat, path):
    nodes = mat.node_tree.nodes
    image = bpy.data.images.load(path, check_existing=True)
    img_node = nodes.new('ShaderNodeTexImage')
    img_node.name = 'TLM-Lightmap'
    img_node.location = (100, 100)
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
def removeLightmap(directly=False):
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

                TLMNodeInput2 = TLMNode.inputs[1].links[0].from_socket if TLMNode and TLMNode.inputs[1].is_linked else None

                if TLMNode:
                    node_tree.nodes.remove(TLMNode)
                if LightmapNode:
                    node_tree.nodes.remove(LightmapNode)
                if UVMapNode:
                    node_tree.nodes.remove(UVMapNode)

                if TLMNodeInput2:
                    node_tree.links.new(TLMNodeInput2, PrincipledNode.inputs[0])

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

# Apply lightmaps to objects based on a manifest file
def applyLightmap(folder, directly=False):
    # Check if lightmaps are already applied and toggle them accordingly
    if "Lightmapped" in bpy.context.scene:
        if bpy.context.scene["Lightmapped"]:
            print("Lightmaps are currently applied - removing lightmap")
            removeLightmap(directly)
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

        #TODO - We want to try and store the original material name as a property?
        #SOMETHING WITH THE UV THAT NEEDS TO BE RESET??

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

        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
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

            if mat.node_tree.nodes.get("Principled BSDF"):
                base_color = None
                base_input = None

                if mat.node_tree.nodes.get("TLM-Node"):
                    mat.node_tree.nodes.remove(mat.node_tree.nodes.get("TLM-Node"))

                if len(mat.node_tree.nodes.get("Principled BSDF").inputs[0].links) < 1:
                    base_color = mat.node_tree.nodes.get("Principled BSDF").inputs[0].default_value
                else:
                    base_input = mat.node_tree.nodes.get("Principled BSDF").inputs[0].links[0]

                if mat.node_tree.nodes.get("TLM-Lightmap"):
                    mat.node_tree.nodes.remove(mat.node_tree.nodes.get("TLM-Lightmap"))

                addTLMNode(mat)
                addLightmapNode(mat, lightmapPath)
                addUVMapNode(mat)

                PrincipledNode = mat.node_tree.nodes.get("Principled BSDF")
                TLMNode = mat.node_tree.nodes.get("TLM-Node")
                LightmapNode = mat.node_tree.nodes.get("TLM-Lightmap")
                UVMapNode = mat.node_tree.nodes.get("TLM-UVMap")

                if directly:
                    mat.node_tree.links.new(TLMNode.outputs[0], PrincipledNode.inputs[0])
                    mat.node_tree.links.new(LightmapNode.outputs[0], TLMNode.inputs[0])
                    mat.node_tree.links.new(UVMapNode.outputs[0], LightmapNode.inputs[0])
                else:
                    if base_color is not None:
                        mat.node_tree.links.new(TLMNode.outputs[0], PrincipledNode.inputs[0])
                        mat.node_tree.links.new(LightmapNode.outputs[0], TLMNode.inputs[0])
                        mat.node_tree.links.new(UVMapNode.outputs[0], LightmapNode.inputs[0])
                        TLMNode.inputs[1].default_value = base_color
                        TLMNode.inputs[2].default_value = 1.0
                    else:
                        mat.node_tree.links.new(TLMNode.outputs[0], PrincipledNode.inputs[0])
                        mat.node_tree.links.new(LightmapNode.outputs[0], TLMNode.inputs[0])
                        mat.node_tree.links.new(UVMapNode.outputs[0], LightmapNode.inputs[0])
                        mat.node_tree.links.new(TLMNode.inputs[1], base_input.from_socket)
                        TLMNode.inputs[2].default_value = 1.0