import bpy, os, json

from ..ui.progress_bar import NX_Progress_Bar
import subprocess
import threading
from queue import Queue, Empty
from ..utility import util
from ..utility import unwrap

main_progress = NX_Progress_Bar(10, 10, 100, 10, 0.0, (0.0, 0.0, 0.0, 1.0))

# Draws the 2D progress bar in the Blender interface
def draw_callback_2d():
    main_progress.progress = bpy.context.scene.get("baking_progress", 0.0)
    main_progress.draw()
    
# Handles operations based on output from the subprocess, updating progress or printing messages
def callback_operations(argument):
    if argument.startswith("[TLM]"):
        call = argument.split(":")
        if len(call) < 3:
            return
        key_type = call[1].strip()
        value = call[2].strip()

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

# Operator for building lightmaps, manages the subprocess and updates progress in Blender
class TLM_BuildLightmaps(bpy.types.Operator):
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _draw_handler = None
    
    def __init__(self):
        self.output_queue = Queue()
        self.error_queue = Queue()

    # Reads output from the subprocess and adds it to a queue
    def read_output(self, pipe, queue):
        try:
            for line in iter(pipe.readline, ''):
                queue.put(line)
        finally:
            pipe.close()

    # Starts the subprocess to build lightmaps
    def start_process(self, cmd):
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, bufsize=1, universal_newlines=True, encoding='utf-8')
        self.stdout_thread = threading.Thread(target=self.read_output, args=(self.process.stdout, self.output_queue), daemon=True)
        self.stderr_thread = threading.Thread(target=self.read_output, args=(self.process.stderr, self.error_queue), daemon=True)
        self.stdout_thread.start()
        self.stderr_thread.start()
        
    # Executes the lightmap building process, setting up timers and handlers
    def execute(self, context):
        args = ()

        util.removeLightmapFolder()
        util.configureEngine()
        util.copyBuildScript()
        unwrap.prepareObjectsForBaking()

        script_path = bpy.path.abspath("//_build_script.py")
        blender_exe_path = bpy.app.binary_path
        blend_file_path = bpy.data.filepath
        cmd = f'"{blender_exe_path}" "{blend_file_path}" --background --python "{script_path}"'
        self.start_process(cmd)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        self._draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d, args, 'WINDOW', 'POST_PIXEL')
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    # Handles modal events, reading subprocess output and updating progress
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

    # Cancels the operation, cleaning up subprocess and handlers
    def cancel(self, context):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        if self.stdout_thread.is_alive():
            self.stdout_thread.join()
        if self.stderr_thread.is_alive():
            self.stderr_thread.join()
        
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        
        if self._draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handler, 'WINDOW')
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        util.removeBuildScript()
        util.postprocessBuild()


        self.report({'INFO'}, "Lightmapping Finished")

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
    bl_description = "Clean and reassign materials"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):

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

        # Clean the lightmap folder

        scene = context.scene

        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_setting_savedir)

        # if os.path.isdir(dirpath):
        #     for file in os.listdir(dirpath):
        #         os.remove(os.path.join(dirpath + "/" + file))

        #import bpy

        # Iterate over all materials in the file
        for material in bpy.data.materials:

            # Check if the material has 0 users
            if material.users == 0:

                # Unlink and remove the material
                matname = str(material.name)
                bpy.data.materials.remove(material)
                print(f"Removed material: {matname}")

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
        min=128,
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

            if obj.type == "MESH":

                uv_layers = obj.data.uv_layers
                uv_channel = "UVMap-Lightmap"

                for uvlayer in uv_layers:
                    if uvlayer.name == uv_channel:
                        uv_layers.remove(uvlayer)

        self.report({'INFO'}, "Lightmapping resolution doubled")
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