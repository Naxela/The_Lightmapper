import bpy, os, json, sys, time, shutil
import numpy as np

from ..ui.progress_bar import NX_Progress_Bar
from ..ui.text_field import NX_Text_Display
import subprocess
import threading
from queue import Queue, Empty
from ..utility import util
from ..utility.rectpack import newPacker, PackingMode, MaxRectsBssf
from ..utility import unwrap

bake_bar    = NX_Progress_Bar(10, 10, 100, 10, 0.0, (1.00, 0.00, 0.00, 1.0), label="Building Lightmaps")
denoise_bar = NX_Progress_Bar(10, 25, 100, 10, 0.0, (0.00, 1.00, 0.00, 1.0), label="Denoising")
atlas_bar   = NX_Progress_Bar(10, 40, 100, 10, 0.0, (0.00, 0.00, 1.00, 1.0), label="Atlasing")
atlas_text_display = NX_Text_Display(x=10, y=42, message="Atlasing lightmaps...", font_size=10)

# All UV layer name prefixes owned by TLM. Covers base names and numbered duplicates
# (e.g. UVMap-Atlas.001) that Blender creates when a layer with the same name already exists.
_TLM_UV_PREFIXES = ("UVMap-Lightmap", "UVMap_Lightmap", "UVMap-Atlas")

def remove_tlm_uv_layers(obj):
    """Remove all TLM-owned UV layers from a mesh object."""
    if obj.type != 'MESH':
        return
    uv_layers = obj.data.uv_layers
    to_remove = [l.name for l in uv_layers if l.name.startswith(_TLM_UV_PREFIXES)]
    for name in to_remove:
        layer = uv_layers.get(name)
        if layer:
            uv_layers.remove(layer)

# Draws the 2D progress bars in the Blender interface
def draw_callback_2d():
    bake_bar.progress = bpy.context.scene.get("baking_progress", 0.0)
    bake_bar.eta = bpy.context.scene.get("bake_eta", "")
    denoise_bar.progress = bpy.context.scene.get("denoise_progress", 0.0)
    atlas_bar.progress = bpy.context.scene.get("atlas_progress", 0.0)
    atlas_bar.draw()
    denoise_bar.draw()
    bake_bar.draw()
    
# Handles operations based on output from the subprocess, updating progress or printing messages
def callback_operations(argument):
    if argument.startswith("[TLM]"):
        call = argument.split(":")
        if len(call) < 3:
            return
        key_type = call[1].strip()
        value = ":".join(call[2:]).strip()

        if key_type == "0":
            try:
                progress_value = float(value)
                bpy.context.scene["baking_progress"] = progress_value
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            except ValueError:
                print(f"Invalid progress value: {value}")

        elif key_type == "1":
            print(value)

        elif key_type == "2": #ERROR - Popup dialogue?
            print(value)

        elif key_type == "3":  # ETA string from subprocess
            bpy.context.scene["bake_eta"] = value 

def realize_collection_instances(context):
    instance_empties = [
        obj for obj in context.scene.objects
        if obj.type == 'EMPTY'
        and obj.instance_type == 'COLLECTION'
        and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use
    ]
    if not instance_empties:
        return 0

    total_realized = 0
    for empty in instance_empties:
        empty.hide_set(False)
        empty.hide_viewport = False

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = empty
        empty.select_set(True)

        before = set(context.scene.objects)

        bpy.ops.object.duplicates_make_real(use_base_parent=True, use_hierarchy=True)
        bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=False, obdata=True)

        after = set(context.scene.objects)
        new_meshes = [obj for obj in (after - before) if obj.type == 'MESH']

        src = empty.TLM_ObjectProperties
        for mesh_obj in new_meshes:
            dst = mesh_obj.TLM_ObjectProperties
            dst.tlm_mesh_lightmap_use        = True
            dst.tlm_mesh_lightmap_resolution  = src.tlm_mesh_lightmap_resolution
            dst.tlm_mesh_lightmap_unwrap_mode = src.tlm_mesh_lightmap_unwrap_mode
            dst.tlm_mesh_unwrap_margin        = src.tlm_mesh_unwrap_margin
            total_realized += 1

        src.tlm_mesh_lightmap_use = False

    return total_realized

# Operator for building lightmaps, manages the subprocess and updates progress in Blender
class TLM_OT_build_lightmaps(bpy.types.Operator):
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps. Ctrl+Click to also toggle lightmaps on after building. Shift+Click to bake selected objects only"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _draw_handler = None
    apply_after: bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})
    selected_only: bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.apply_after = event.ctrl
        self.selected_only = event.shift
        return self.execute(context)

    # Remove __init__ completely and initialize queues in execute()
    def read_output(self, pipe, queue):
        try:
            for line in iter(pipe.readline, ''):
                queue.put(line)
        finally:
            pipe.close()

    def start_process(self, cmd):
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, bufsize=1, universal_newlines=True, encoding='utf-8')
        self.stdout_thread = threading.Thread(target=self.read_output, args=(self.process.stdout, self.output_queue), daemon=True)
        self.stderr_thread = threading.Thread(target=self.read_output, args=(self.process.stderr, self.error_queue), daemon=True)
        self.stdout_thread.start()
        self.stderr_thread.start()
        
    def execute(self, context):
        # Initialize queues here instead of in __init__
        self.output_queue = Queue()
        self.error_queue = Queue()

        # Reset all progress bars for a fresh bake
        bpy.context.scene["baking_progress"] = 0.0
        bpy.context.scene["denoise_progress"] = 0.0
        bpy.context.scene["atlas_progress"]   = 0.0
        bpy.context.scene["bake_eta"]         = ""
        
        args = ()

        if bpy.context.scene.TLM_SceneProperties.tlm_reset_lightmap_uv:
            for obj in bpy.context.scene.objects:
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    remove_tlm_uv_layers(obj)

        n = realize_collection_instances(context)
        if n > 0:
            self.report({'WARNING'},
                f"Realized {n} mesh object(s) from collection instances. "
                "Undo (Ctrl+Z) after baking to revert if needed.")

        if self.selected_only:
            selected_names = [
                obj.name for obj in context.selected_objects
                if obj.type == 'MESH' and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use
            ]
            context.scene["TLM_bake_selection"] = selected_names
        elif "TLM_bake_selection" in context.scene:
            del context.scene["TLM_bake_selection"]

        util.removeLightmapFolder()
        util.configureEngine()
        util.copyBuildScript()
        unwrap.prepareObjectsForBaking()

        script_path = bpy.path.abspath("//_build_script.py")
        blender_exe_path = bpy.app.binary_path
        blend_file_path = bpy.data.filepath
        cmd = f'"{blender_exe_path}" "{blend_file_path}" --background --python "{script_path}"'
        self._bake_start = time.time()
        self.start_process(cmd)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        self._draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d, args, 'WINDOW', 'POST_PIXEL')
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    # Rest of your methods remain the same...
    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                while True:
                    line = self.output_queue.get_nowait()
                    callback_operations(line)
            except Empty:
                pass

            if self.process.poll() is not None:
                try:
                    while True:
                        line = self.error_queue.get_nowait()
                        print("[stderr] " + line.strip())
                except Empty:
                    pass
                return self.cancel(context)
        return {'PASS_THROUGH'}

    def cancel(self, context):
        if hasattr(self, 'process') and self.process and self.process.poll() is None:
            self.process.terminate()
        if hasattr(self, 'stdout_thread') and self.stdout_thread.is_alive():
            self.stdout_thread.join()
        if hasattr(self, 'stderr_thread') and self.stderr_thread.is_alive():
            self.stderr_thread.join()

        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        if "TLM_bake_selection" in bpy.context.scene:
            del bpy.context.scene["TLM_bake_selection"]

        util.removeBuildScript()

        t_bake = time.time() - self._bake_start if hasattr(self, '_bake_start') else 0.0

        # Denoising — show progress in UI bar
        bpy.context.scene["bake_eta"] = ""
        bpy.context.scene["denoise_progress"] = 0.0
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        t0 = time.time()
        util.postprocessBuild()
        t_denoise = time.time() - t0
        bpy.context.scene["denoise_progress"] = 1.0
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        # Atlasing — show progress in UI bar
        t0 = time.time()
        if (hasattr(self, 'process') and self.process and self.process.returncode == 0
                and bpy.context.scene.TLM_SceneProperties.tlm_create_atlas):
            bpy.context.scene["atlas_progress"] = 0.0
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            createAtlases(int(bpy.context.scene.TLM_SceneProperties.tlm_atlas_max_resolution))
            bpy.context.scene["atlas_progress"] = 1.0
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        t_atlas = time.time() - t0

        # Now remove the draw handler
        if self._draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handler, 'WINDOW')
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        def _fmt(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            if h > 0:
                return f"{h}h {m:02d}m {s:02d}s"
            elif m > 0:
                return f"{m}m {s:02d}s"
            else:
                return f"{s}s"

        print("=== TLM Timing Summary ===")
        print(f"Rendering:  {_fmt(t_bake)}")
        print(f"Denoising:  {_fmt(t_denoise)}")
        print(f"Atlasing:   {_fmt(t_atlas)}")
        print(f"Total:      {_fmt(t_bake + t_denoise + t_atlas)}")

        # Reset the lightmap state flag after a fresh bake so apply always applies.
        bpy.context.scene["Lightmapped"] = False

        self.report({'INFO'}, "Lightmapping Finished")

        if self.apply_after and hasattr(self, 'process') and self.process and self.process.returncode == 0:
            bpy.ops.tlm.apply_lightmaps()

        return {'CANCELLED'}
    
# Operator to apply lightmaps, toggling them on the objects
class TLM_ApplyLightmaps(bpy.types.Operator):
    bl_idname = "tlm.apply_lightmaps"
    bl_label = "Toggle Lightmaps"
    bl_description = "Toggle Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):
        util.applyLightmap("//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir)
        return {'FINISHED'}

class TLM_CleanAndReassignMaterials(bpy.types.Operator):
    bl_idname = "tlm.clean_and_reassign_materials"
    bl_label = "Clean and Reassign Materials"
    bl_description = "Clean and reassign materials. Shift+Click to remove all TLM UV layers. Ctrl+Click to delete all files in the lightmap directory"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        if event.shift:
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH' and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    remove_tlm_uv_layers(obj)
            self.report({'INFO'}, "Lightmap UV layers removed")
            return {'FINISHED'}
        if event.ctrl:
            scene = context.scene
            dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_setting_savedir)
            if os.path.isdir(dirpath):
                for file in os.listdir(dirpath):
                    file_path = os.path.join(dirpath, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                self.report({'INFO'}, "Lightmap directory cleared")
            else:
                self.report({'WARNING'}, "Lightmap directory not found")
            return {'FINISHED'}
        return self.execute(context)

    def execute(self, context):

        # Revert materials to their original state before reassigning
        util.removeLightmap()

        # Reassign the materials
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    continue
                inherited_mat = mat.get("TLM_InheritedMaterial")
                if inherited_mat:
                    print("Inherited Material: " + obj.name + " : " + inherited_mat.name + " child: " + mat.name)
                    slot.material = inherited_mat

        # Remove 0-user materials
        for material in list(bpy.data.materials):
            if material.users == 0:
                matname = str(material.name)
                bpy.data.materials.remove(material)
                print(f"Removed material: {matname}")

        # Remove 0-user images
        for image in list(bpy.data.images):
            if image.users == 0:
                imgname = str(image.name)
                bpy.data.images.remove(image)
                print(f"Removed image: {imgname}")

        self.report({'INFO'}, "Materials cleaned and reassigned")
        return {'FINISHED'}

# Operator to explore the lightmaps directory
class TLM_ExploreLightmaps(bpy.types.Operator):
    bl_idname = "tlm.explore_lightmaps"
    bl_label = "Explore Lightmaps"
    bl_description = "Explore Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):
        util.exploreLightmaps()
        return {'FINISHED'}
    
# Operator to link lightmaps to the object properties
class TLM_LinkLightmaps(bpy.types.Operator):
    bl_idname = "tlm.link_lightmaps"
    bl_label = "Link Lightmaps"
    bl_description = "Link Lightmaps to object properties"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):
        util.linkLightmap("//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir)
        return {'FINISHED'}

# Operator to link lightmaps to the object properties
class TLM_MatProperties(bpy.types.Operator):
    bl_idname = "tlm.mat_links"
    bl_label = "Assign material links"
    bl_description = "Assign material links"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):

        tlm_objmat = {
            "materials_options" : []
        }

        for obj in bpy.context.selected_objects:

            if obj.type == "MESH":

                if len(obj.material_slots) > 0:

                    for slot in obj.material_slots:

                        mat = slot.material

                        options = {
                            "name" : mat.name,
                            "tex_animation_x" : None,
                            "tex_animation_y" : None,
                            "blend" : None,
                            "transmission" : None,
                            "parallax" : None,
                            "reflectance" : None
                        }

                        mat["tlm_matopt"] = options

        return {'FINISHED'}

class TLM_OBJECT_OT_lightmap_enable(bpy.types.Operator):
    bl_idname = "object.lightmap_enable"
    bl_label = "Enable Lightmapping"

    # Define properties for the modal
    enable_lightmap: bpy.props.BoolProperty(
        name="Enable Lightmap",
        description="Enable lightmapping for the selected objects",
        default=True,
    )

    lightmap_resolution: bpy.props.IntProperty(
        name="Lightmap Resolution",
        description="Resolution of the lightmap",
        default=256,
        min=32,
        max=4096,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enable_lightmap")
        layout.prop(self, "lightmap_resolution")

    def invoke(self, context, event):
        # Opens the modal pop-up
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if self.enable_lightmap:
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = True
                    obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = str(self.lightmap_resolution)

            self.report({'INFO'}, f"Lightmapping Enabled with resolution {self.lightmap_resolution}")
        else:
            self.report({'INFO'}, "Lightmapping Disabled")
        return {'FINISHED'}

class TLM_OBJECT_OT_lightmap_disable(bpy.types.Operator):
    bl_idname = "object.lightmap_disable"
    bl_label = "Disable Lightmapping"
    
    def execute(self, context):

        for obj in bpy.context.selected_objects:

            if obj.type == "MESH":

                obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = False

        self.report({'INFO'}, "Lightmapping Disabled")
        return {'FINISHED'}

class TLM_OBJECT_OT_lightmap_oneup(bpy.types.Operator):
    bl_idname = "object.lightmap_oneup"
    bl_label = "Increase lightmap resolution to double"
    
    def execute(self, context):

        for obj in bpy.context.selected_objects:

            if obj.type == "MESH":

                obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = str(int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) * 2)

        self.report({'INFO'}, "Lightmapping resolution doubled")
        return {'FINISHED'}

class TLM_OBJECT_OT_lightmap_removeuv(bpy.types.Operator):
    bl_idname = "object.lightmap_removeuv"
    bl_label = "Remove the lightmap UV of the selected objects"
    
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            remove_tlm_uv_layers(obj)
        self.report({'INFO'}, "Lightmap UV's removed")
        return {'FINISHED'}

class TLM_OBJECT_OT_lightmap_onedown(bpy.types.Operator):
    bl_idname = "object.lightmap_onedown"
    bl_label = "Decrease lightmap resolution to half"
    
    def execute(self, context):

        for obj in bpy.context.selected_objects:

            if obj.type == "MESH":

                obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = str(int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) / 2)

        self.report({'INFO'}, "Lightmapping resolution halved")
        return {'FINISHED'}

class TLM_removeMatLink(bpy.types.Operator):
    bl_idname = "tlm.remove_mat_links"
    bl_label = "Remove material links"
    
    def execute(self, context):

        for obj in bpy.context.scene.objects:

            if obj.type == "MESH":

                if "TLM_Lightmap" in obj.keys():
                    
                    del obj["TLM_Lightmap"]

        return {'FINISHED'}



class TLM_OBJECT_OT_selected_lightmapped(bpy.types.Operator):
    bl_idname = "object.selected_lightmapped"
    bl_label = "Select lightmapped"

    def execute(self, context):

        bpy.ops.object.select_all(action='DESELECT')

        for obj in bpy.context.scene.objects:

            if obj.type == "MESH":

                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use == True:

                    if obj.visible_get():
                        obj.select_set(True)

        print("Select lightmapped!")

        return {'FINISHED'}


#Todo:
# - Remove lightmap UV channel
# - Disable roughness
# - Disable specularity


class TLM_DisableSpec(bpy.types.Operator):
    bl_idname = "tlm.disable_spec"
    bl_label = "Disable specularity for object materials"
    bl_description = "Disable specularity for object materials"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):

        for obj in bpy.context.selected_objects:

            if obj.type == "MESH":

                if len(obj.material_slots) > 0:

                    for slot in obj.material_slots:

                        mat = slot.material

                        if mat.node_tree:

                            for node in mat.node_tree.nodes:

                                if node.type == "BSDF_PRINCIPLED":

                                    for inp in node.inputs:

                                        if inp.name == "Specular IOR Level":

                                            inp.default_value = 0.0

                                            if inp.links and bpy.context.scene.TLM_SceneProperties.tlm_remove_met_spec_link:

                                                mat.node_tree.links.remove(inp.links[0])

        return {'FINISHED'}


class TLM_DisableMetallic(bpy.types.Operator):
    bl_idname = "tlm.disable_metallic"
    bl_label = "Disable metallicity for object materials"
    bl_description = "Disable metallicity for object materials"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):

        for obj in bpy.context.selected_objects:

            if obj.type == "MESH":

                if len(obj.material_slots) > 0:

                    for slot in obj.material_slots:

                        mat = slot.material

                        if mat.node_tree:

                            for node in mat.node_tree.nodes:

                                if node.type == "BSDF_PRINCIPLED":

                                    for inp in node.inputs:

                                        if inp.name == "Metallic":

                                            inp.default_value = 0.0

                                            if inp.links and bpy.context.scene.TLM_SceneProperties.tlm_remove_met_spec_link:

                                                mat.node_tree.links.remove(inp.links[0])

        return {'FINISHED'}

def convertToKTX(absolute_directory, manifest_data):

    ktx_outdir = os.path.join(absolute_directory, "KTX")
    print("KTX output directory is: " + ktx_outdir)

    if not os.path.exists(ktx_outdir):
        os.makedirs(ktx_outdir)

    ktx_path = os.path.join(util.get_addon_path(), "binaries", "ktx", "ktx.exe")
    if not os.path.exists(ktx_path):
        print(f"KTX tool not found at {ktx_path}")
        return

    for hdr_file in os.listdir(absolute_directory):

        if hdr_file.startswith("atlas"):

            if hdr_file.endswith(".hdr"):

                hdr_path = os.path.join(absolute_directory, hdr_file)
                ktx_output_path = os.path.join(ktx_outdir, os.path.basename(hdr_file).replace(".hdr", ".ktx2"))

                ktx_command = [
                    ktx_path,
                    "create",
                    "--format", "R32G32B32A32_SFLOAT",
                    hdr_path,
                    ktx_output_path
                ]

                try:
                    subprocess.run(ktx_command, check=True)
                    print(f"Converted {hdr_path} to {ktx_output_path} in KTX2 format.")
                except subprocess.CalledProcessError as e:
                    print(f"Error during KTX conversion for {hdr_path}: {e}")

            if hdr_file.endswith(".exr"):

                hdr_path = os.path.join(absolute_directory, hdr_file)
                ktx_output_path = os.path.join(ktx_outdir, os.path.basename(hdr_file).replace(".exr", ".ktx2"))

                # ktx_command = [
                #     ktx_path,
                #     "create",
                #     "--format", "B10G11R11_UFLOAT_PACK32",
                #     hdr_path,
                #     ktx_output_path
                # ]

                if bpy.context.scene.TLM_SceneProperties.tlm_tex_compression:

                    ktx_command = [
                        ktx_path,
                        "create",
                        "--format", "R32G32B32A32_SFLOAT",
                        "--zstd", bpy.context.scene.TLM_SceneProperties.tlm_tex_compression_level,
                        hdr_path,
                        ktx_output_path
                    ]

                else:

                    ktx_command = [
                        ktx_path,
                        "create",
                        "--format", "R32G32B32A32_SFLOAT",
                        hdr_path,
                        ktx_output_path
                    ]

                try:
                    subprocess.run(ktx_command, check=True)
                    print(f"Converted {hdr_path} to {ktx_output_path} in KTX2 format.")
                except subprocess.CalledProcessError as e:
                    print(f"Error during KTX conversion for {hdr_path}: {e}")



                # if bpy.context.scene.TLM_SceneProperties.tlm_tex_format == "F32":

                #     if bpy.context.scene.TLM_SceneProperties.tlm_tex_compression:

                #         ktx_command = [
                #             ktx_path,
                #             "create",
                #             "--format", "R32G32B32A32_SFLOAT",
                #             "--zstd", bpy.context.scene.TLM_SceneProperties.tlm_tex_compression_level,
                #             exr_path,
                #             ktx_output_path
                #         ]

                #     else:

                #         ktx_command = [
                #             ktx_path,
                #             "create",
                #             "--format", "R32G32B32A32_SFLOAT",
                #             exr_path,
                #             ktx_output_path
                #         ]

                # elif bpy.context.scene.TLM_SceneProperties.tlm_tex_format == "F16":

                #     if bpy.context.scene.TLM_SceneProperties.tlm_tex_compression:

                #         ktx_command = [
                #             ktx_path,
                #             "create",
                #             "--format", "R16G16B16A16_SFLOAT",
                #             "--zstd", bpy.context.scene.TLM_SceneProperties.tlm_tex_compression_level,
                #             exr_path,
                #             ktx_output_path
                #         ]

                #     else:

                #         ktx_command = [
                #             ktx_path,
                #             "create",
                #             "--format", "R16G16B16A16_SFLOAT",
                #             exr_path,
                #             ktx_output_path
                #         ]

                # elif bpy.context.scene.TLM_SceneProperties.tlm_tex_format == "VK":

                #     if bpy.context.scene.TLM_SceneProperties.tlm_tex_compression:

                #         ktx_command = [
                #             ktx_path,
                #             "create",
                #             "--format", "B10G11R11_UFLOAT_PACK32",
                #             "--zstd", bpy.context.scene.TLM_SceneProperties.tlm_tex_compression_level,
                #             exr_path,
                #             ktx_output_path
                #         ]

                #     else:

                #         ktx_command = [
                #             ktx_path,
                #             "create",
                #             "--format", "B10G11R11_UFLOAT_PACK32",
                #             exr_path,
                #             ktx_output_path
                #         ]

                # try:
                #     subprocess.run(ktx_command, check=True)
                #     print(f"Converted {exr_path} to {ktx_output_path} in KTX2 format.")
                # except subprocess.CalledProcessError as e:
                #     print(f"Error during KTX conversion for {exr_path}: {e}")




    manifest_path = os.path.join(absolute_directory, "manifest.json")
    shutil.copy(manifest_path, ktx_outdir)

    updated_manifest_path = os.path.join(ktx_outdir, "manifest.json")
    with open(updated_manifest_path, 'r') as file:
        manifest_data = json.load(file)

    manifest_data["ext"] = "ktx"

    with open(updated_manifest_path, 'w') as file:
        json.dump(manifest_data, file, indent=4)

    #TODO - Remove lightmap folder and copy






























def loadImagesToAtlas():
    imagesToAtlas = []
    relative_directory = "//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir
    absolute_directory = bpy.path.abspath(relative_directory)
    manifest_file = os.path.join(absolute_directory, "manifest.json")

    if not os.path.exists(absolute_directory):
        print("No lightmap directory")
        return imagesToAtlas

    if not os.path.exists(manifest_file):
        print("No lightmap manifest")
        return imagesToAtlas

    with open(manifest_file, 'r') as file:
        data = json.load(file)

    ext = data.get("ext", "hdr")
    for key, value in data["lightmaps"].items():
        image_name = f"{value}.{ext}"
        imagesToAtlas.append({"name": image_name, "object": key})

    return imagesToAtlas

def createEmptyAtlas(atlas_index, file_format, max_resolution):
    image_name = f"Atlas_{atlas_index}"
    new_image = bpy.data.images.new(image_name, width=max_resolution, height=max_resolution, float_buffer=True)
    pixels = [0.0] * (max_resolution * max_resolution * 4)
    new_image.pixels = pixels
    new_image.alpha_mode = 'STRAIGHT'
    if file_format == "HDR":
        new_image.file_format = file_format #HDR
    else:
        new_image.file_format = "OPEN_EXR" #EXR or KTX will be converted from EXR

    return new_image

def invertPixelsY(source_image):
    # Blender stores pixels bottom-row-first, but rect-pack places rects top-row-first.
    # This first flip converts the source image from Blender's bottom-up order into top-down order
    # so that transferPixels can place it at the correct position in the atlas.
    source_pixels = list(source_image.pixels)
    source_width, source_height = source_image.size
    corrected_pixels = [0.0] * len(source_pixels)

    for y in range(source_height):
        for x in range(source_width):
            source_index = (y * source_width + x) * 4
            corrected_index = ((source_height - 1 - y) * source_width + x) * 4
            for c in range(4):
                corrected_pixels[source_index + c] = source_pixels[corrected_index + c]

    return corrected_pixels

def transferPixels(inverted_pixels, target_image, x_offset, y_offset, source_width, source_height, max_resolution):
    target_pixels = list(target_image.pixels)

    for y in range(source_height):
        for x in range(source_width):
            source_index = (y * source_width + x) * 4
            # Second flip: converts back from top-down order into Blender's bottom-up atlas storage,
            # while applying the y_offset from the rect-packer. Both flips together are intentional —
            # the two inversions cancel out to a net-zero flip, but are necessary to correctly map
            # the packer's top-down y coordinates into Blender's bottom-up pixel buffer.
            target_index = ((y_offset + (source_height - 1 - y)) * max_resolution + x_offset + x) * 4
            for c in range(4):
                target_pixels[target_index + c] = inverted_pixels[source_index + c]

    target_image.pixels = target_pixels

def adjustUVs(obj, x_offset, y_offset, source_width, source_height, atlas_res):
    mesh = obj.data

    lightmap_layer = mesh.uv_layers.get("UVMap-Lightmap")

    if lightmap_layer is not None:
        # First atlas run. Back up original UVs into UVMap-Lightmap-part (UV2),
        # write atlas coordinates into UVMap-Lightmap (UV1), then rename it to UVMap-Atlas.
        # This keeps the atlas at the correct UV index for game engine export (Godot UV2 = Blender UV1).
        part_layer = mesh.uv_layers.get("UVMap-Lightmap-part")
        if part_layer is None:
            part_layer = mesh.uv_layers.new(name="UVMap-Lightmap-part")

        # Re-fetch after uv_layers.new() — adding a layer may reallocate the underlying C array,
        # invalidating any previously obtained Python references to other layers.
        lightmap_layer = mesh.uv_layers.get("UVMap-Lightmap")

        for loop in mesh.loops:
            orig_u = lightmap_layer.data[loop.index].uv.x
            orig_v = lightmap_layer.data[loop.index].uv.y
            part_layer.data[loop.index].uv.x = orig_u
            part_layer.data[loop.index].uv.y = orig_v
            lightmap_layer.data[loop.index].uv.x = (x_offset + orig_u * source_width) / atlas_res
            lightmap_layer.data[loop.index].uv.y = (y_offset + orig_v * source_height) / atlas_res

        lightmap_layer.name = "UVMap-Atlas"

    else:
        # Re-atlas run. UVMap-Lightmap was already renamed to UVMap-Atlas on the first run.
        # Read original per-object UVs from UVMap-Lightmap-part and write new atlas coordinates
        # into UVMap-Atlas, so the correct UV index is preserved.
        part_layer = mesh.uv_layers.get("UVMap-Lightmap-part")
        atlas_layer = mesh.uv_layers.get("UVMap-Atlas")

        if part_layer is None or atlas_layer is None:
            raise ValueError(
                f"Object '{obj.name}' is missing expected UV layers for re-atlasing. "
                f"Expected 'UVMap-Lightmap' or both 'UVMap-Atlas' and 'UVMap-Lightmap-part'."
            )

        for loop in mesh.loops:
            orig_u = part_layer.data[loop.index].uv.x
            orig_v = part_layer.data[loop.index].uv.y
            atlas_layer.data[loop.index].uv.x = (x_offset + orig_u * source_width) / atlas_res
            atlas_layer.data[loop.index].uv.y = (y_offset + orig_v * source_height) / atlas_res

def setMaterialImage(obj, atlas_image):
    if obj.type != 'MESH':
        return

    for slot in obj.material_slots:
        material = slot.material
        if not material or not material.use_nodes:
            continue
        nodes = material.node_tree.nodes
        tlm_lightmap_node = nodes.get("TLM-Lightmap")
        if tlm_lightmap_node and tlm_lightmap_node.type == 'TEX_IMAGE':
            tlm_lightmap_node.image = atlas_image

        # Renaming a UV layer via Python does not automatically update ShaderNodeUVMap nodes
        # that reference it by name. Point the TLM-UVMap node at the atlas layer directly.
        tlm_uvmap_node = nodes.get("TLM-UVMap")
        if tlm_uvmap_node:
            tlm_uvmap_node.uv_map = "UVMap-Atlas"

def createAtlases(max_resolution):
    atlas_text_display.toggle()
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

    imagesToAtlas = loadImagesToAtlas()
    if not imagesToAtlas:
        print("No images to atlas")
        atlas_text_display.toggle()
        atlas_text_display.remove()
        return []

    atlases = []  # List to store created atlases
    manifest_data = {"ext": "", "lightmaps": {}}  # Updated manifest data

    relative_directory = "//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir
    absolute_directory = bpy.path.abspath(relative_directory)

    # Load images from disk if they are not already in bpy.data.images.
    # This is required when atlasing runs in the main Blender instance after a bake subprocess,
    # because the subprocess saves images to disk but never populates the main instance's bpy.data.images.
    valid_images = []
    for img_info in imagesToAtlas:
        if img_info['name'] not in bpy.data.images:
            file_path = os.path.join(absolute_directory, img_info['name'])
            if os.path.exists(file_path):
                bpy.data.images.load(file_path)
            else:
                print(f"[TLM]:2:Warning: Image file {img_info['name']} not found on disk, skipping.", flush=True)
                continue
        img = bpy.data.images[img_info['name']]
        w, h = img.size[0], img.size[1]
        if w > max_resolution or h > max_resolution:
            print(f"[TLM]:2:Warning: Image {img_info['name']} ({w}x{h}) exceeds atlas max resolution {max_resolution}, skipping.", flush=True)
            continue
        valid_images.append(img_info)

    if not valid_images:
        print("[TLM]:2:No valid images to atlas after filtering.", flush=True)
        return []

    imagesToAtlas = valid_images
    total_rectangles = len(imagesToAtlas)
    processed_rectangles = 0

    source_images = [bpy.data.images[img_info['name']] for img_info in imagesToAtlas]
    rectangles = [(img.size[0], img.size[1], i) for i, img in enumerate(source_images)]
    print("Rectangles for Packing:", rectangles)

    output_format = bpy.context.scene.TLM_SceneProperties.tlm_format

    while processed_rectangles < total_rectangles:
        print(f"Creating new atlas (Bin #{len(atlases) + 1})...")

        # Initialize the packer for each new atlas
        packer = newPacker(mode=PackingMode.Offline, rotation=False, pack_algo=MaxRectsBssf)

        # Add a new bin for the current atlas
        packer.add_bin(max_resolution, max_resolution)

        # Add remaining rectangles to the packer
        for rect in rectangles:
            packer.add_rect(*rect)

        # Perform packing
        packer.pack()

        # Create an empty atlas for this bin
        atlas_index = len(atlases) + 1
        atlas_image = createEmptyAtlas(atlas_index, output_format, max_resolution)
        atlases.append(atlas_image)

        if output_format == "HDR":
            atlas_path = os.path.join(absolute_directory, f"atlas_{atlas_index}.hdr")
            atlas_image.file_format = "HDR"
        else:
            atlas_path = os.path.join(absolute_directory, f"atlas_{atlas_index}.exr")
            atlas_image.file_format = "OPEN_EXR"

        atlas_image.filepath_raw = atlas_path

        # manifest_data["atlases"].append(f"atlas_{atlas_index}.{output_format.lower()}")

        # Process packed rectangles for the current bin
        packed_rects = packer.rect_list()
        print(f"Packed Rectangles for Atlas {atlas_index}: {packed_rects}")

        # Calculate atlas fill percentage
        used_area = sum(w * h for _, _, _, w, h, _ in packed_rects)
        total_area = max_resolution * max_resolution
        fill_percentage = (used_area / total_area) * 100
        print(f"Atlas {atlas_index} Fill Percentage: {fill_percentage:.2f}%")

        # Process packed rectangles
        packed_ids = set()
        for rect in packed_rects:
            bin_id, x, y, w, h, rid = rect
            if rid is None:
                raise ValueError(f"Rectangle {rect} has no associated ID (rid). This should not happen.")

            img_info = imagesToAtlas[rid]
            source_image = bpy.data.images[img_info['name']]
            inverted_pixels = invertPixelsY(source_image)
            transferPixels(inverted_pixels, atlas_image, x, y, w, h, max_resolution)
            obj = bpy.data.objects[img_info['object']]
            adjustUVs(obj, x, y, w, h, max_resolution)

            # Assign the correct atlas image to the object's material
            setMaterialImage(obj, atlas_image)

            # Track processed rectangles
            packed_ids.add(rid)
            processed_rectangles += 1

            # Update the manifest for the object.
            # KTX files are converted from EXR, so the intermediate and atlas files on disk are
            # always EXR. The manifest ext reflects what the game engine will load after conversion.
            manifest_data["lightmaps"][img_info['object']] = f"atlas_{atlas_index}"
            manifest_data["ext"] = "hdr" if output_format == "HDR" else "exr"

            bpy.context.scene["atlas_progress"] = processed_rectangles / total_rectangles
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        # Save after all pixels have been transferred into this atlas.
        atlas_image.save()
        print(f"Atlas {atlas_index} saved to {atlas_path}")

        # Determine unpacked rectangles
        rectangles = [rect for rect in rectangles if rect[2] not in packed_ids]

    # Save the updated manifest to the lightmap directory
    manifest_path = os.path.join(absolute_directory, "manifest.json")
    with open(manifest_path, 'w') as manifest_file:
        json.dump(manifest_data, manifest_file, indent=4)
    print(f"Manifest saved to {manifest_path}")

    # Convert to KTX if required
    if output_format == "KTX":
        print("Converting to KTX")

        #shutil.rmtree(os.path.join(absolute_directory,"KTX"))

        for image in bpy.data.images:
            if image.name.startswith("Atlas"):
                image.save()

        convertToKTX(absolute_directory, manifest_data)

    # Clean non-atlas lightmap files now that atlases are built
    for file in os.listdir(absolute_directory):
        if file.endswith(".hdr") or file.endswith(".exr"):
            if not file.startswith("atlas_"):
                os.remove(os.path.join(absolute_directory, file))

    # Debug report
    print("\nAtlas Creation Summary:")
    print(f"Total Atlases Created: {len(atlases)}")
    print(f"Total Rectangles Packed: {processed_rectangles}/{total_rectangles}")

    atlas_text_display.toggle()
    atlas_text_display.remove()

    return atlases


# ── Texel density helpers ─────────────────────────────────────────────────────

def _compute_world_area(obj):
    """Return total world-space surface area of obj's mesh via triangle-fan decomposition."""
    import mathutils
    mesh = obj.data
    mw = obj.matrix_world
    total = 0.0
    for poly in mesh.polygons:
        verts = [mw @ mesh.vertices[i].co for i in poly.vertices]
        for i in range(1, len(verts) - 1):
            e1 = verts[i] - verts[0]
            e2 = verts[i + 1] - verts[0]
            total += e1.cross(e2).length * 0.5
    return total

_VALID_RESOLUTIONS = [32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]

def _nearest_power_of_2_resolution(r):
    """Round r to the nearest value in _VALID_RESOLUTIONS using linear distance."""
    import math
    r = max(32.0, min(8192.0, r))
    log2r = math.log2(r)
    lo = int(2 ** math.floor(log2r))
    hi = int(2 ** math.ceil(log2r))
    result = lo if abs(r - lo) <= abs(r - hi) else hi
    return max(32, min(8192, result))


class TLM_OT_texel_density_preview(bpy.types.Operator):
    bl_idname = "tlm.texel_density_preview"
    bl_label = "Preview"
    bl_description = "Show what resolution each TLM-enabled object would receive at the target texel density, without changing anything"
    bl_options = {'REGISTER'}

    def execute(self, context):
        import math
        texel_size_cm = context.scene.TLM_SceneProperties.tlm_texel_size_cm
        candidates = [
            obj for obj in context.scene.objects
            if obj.type == 'MESH' and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use
        ]
        if not candidates:
            self.report({'WARNING'}, "No TLM-enabled mesh objects in scene")
            return {'CANCELLED'}

        print(f"\n[TLM] Texel Density Preview (texel size={texel_size_cm:.2f} cm/texel):")
        for obj in candidates:
            area = _compute_world_area(obj)
            if area <= 0.0:
                print(f"  {obj.name}: no geometry, skipped")
                continue
            raw = (math.sqrt(area) * 100) / texel_size_cm
            res = _nearest_power_of_2_resolution(raw)
            current = obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution
            print(f"  {obj.name}: {current} -> {res}  (area={area:.2f} m², raw={raw:.1f})")

        self.report({'INFO'}, f"Texel density preview for {len(candidates)} objects (see console)")
        return {'FINISHED'}


class TLM_OT_texel_density_apply(bpy.types.Operator):
    bl_idname = "tlm.texel_density_apply"
    bl_label = "Apply"
    bl_description = "Auto-assign lightmap resolution to all TLM-enabled objects based on the target texel density and each object's world-space surface area"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import math
        texel_size_cm = context.scene.TLM_SceneProperties.tlm_texel_size_cm
        candidates = [
            obj for obj in context.scene.objects
            if obj.type == 'MESH' and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use
        ]
        if not candidates:
            self.report({'WARNING'}, "No TLM-enabled mesh objects in scene")
            return {'CANCELLED'}

        assigned = 0
        skipped = 0
        for obj in candidates:
            area = _compute_world_area(obj)
            if area <= 0.0:
                skipped += 1
                continue
            raw = (math.sqrt(area) * 100) / texel_size_cm
            res = _nearest_power_of_2_resolution(raw)
            obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = str(res)
            assigned += 1

        self.report({'INFO'}, f"Texel density applied: {assigned} assigned, {skipped} skipped (no geometry)")
        return {'FINISHED'}


class TLM_Atlas(bpy.types.Operator):
    bl_idname = "tlm.atlas"
    bl_label = "Atlas lightmaps"
    bl_description = "Package all your lightmaps into combined textures called atlas textures"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):
        created_atlases = createAtlases(int(bpy.context.scene.TLM_SceneProperties.tlm_atlas_max_resolution))
        print(f"Created {len(created_atlases)} atlases.")
        return {'FINISHED'}
