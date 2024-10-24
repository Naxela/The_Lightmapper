import bpy

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

        return {'CANCELLED'}
    
# Operator to apply lightmaps, toggling them on the objects
class TLM_ApplyLightmaps(bpy.types.Operator):
    bl_idname = "tlm.apply_lightmaps"
    bl_label = "Toggle Lightmaps"
    bl_description = "Toggle Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):
        util.applyLightmap("//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir, False)
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