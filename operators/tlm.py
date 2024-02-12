import bpy
#from ..ui import progress_bar.NX_Progress_Bar as NX_Progress_Bar
from ..ui.progress_bar import NX_Progress_Bar
import subprocess
import threading
from queue import Queue, Empty
from ..utility import util

main_progress = NX_Progress_Bar(10, 10, 100, 10, 0.0, (0.0, 0.0, 0.0, 1.0))

def draw_callback_2d():
    main_progress.progress = bpy.context.scene.get("baking_progress", 0.0)
    #main_progress.color = (1.0, 0.0, 0.0, 1.0)
    main_progress.draw()
    
def callbackOperations(argument):
    
    # [TLM]:0:0.0
    # [INDICATOR] : KEYTYPE : VALUE
    
    global baking_progress
    
    if argument.startswith("[TLM]"):
        
        call = argument.split(':') #Remove indicator and split by semicolon :
        
        if call[1] == "0":
            progress_value = float(call[2].strip())
            bpy.context.scene["baking_progress"] = progress_value
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        
        if call[1] == "1":
            print(call[2].strip())

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

    def read_output(self, pipe, queue):
        try:
            for line in iter(pipe.readline, ''):
                queue.put(line)
        finally:
            pipe.close()

    def start_process(self, cmd):
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, bufsize=1, universal_newlines=True, encoding='utf-8')
        self.stdout_thread = threading.Thread(target=self.read_output, args=(self.process.stdout, self.output_queue))
        self.stderr_thread = threading.Thread(target=self.read_output, args=(self.process.stderr, self.error_queue))
        self.stdout_thread.start()
        self.stderr_thread.start()
        
    def execute(self, context):
        args=()
        # Setup command and start the process
        util.copyBuildScript()
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
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            
            try:
                while True:  # Non-blocking read from the queue
                    line = self.output_queue.get_nowait()
                    callbackOperations(line)
                    print(line.strip())
                    # Process line here if necessary
            except Empty:
                pass  # No more lines to read for now

            if self.process.poll() is not None:  # Process has finished
                try:
                    while True:  # Ensure we read all remaining lines
                        line = self.error_queue.get_nowait()
                        print("[stderr] " + line.strip())
                except Empty:
                    pass
                return self.cancel(context)
        return {'PASS_THROUGH'}

    def cancel(self, context):
        print("Cancel Call")
        if self.process and self.process.poll() is None:
            self.process.terminate()  # Or .kill() if terminate doesn't work
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
        return {'CANCELLED'}
    
class TLM_ApplyLightmaps(bpy.types.Operator):
    bl_idname = "tlm.apply_lightmaps"
    bl_label = "Apply Lightmaps"
    bl_description = "Apply Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):
        util.applyLightmap("//Lightmaps", False)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        return {'PASS_THROUGH'}

    def cancel(self, context):
        return {'CANCELLED'}

class TLM_LinkLightmaps(bpy.types.Operator):
    bl_idname = "tlm.link_lightmaps"
    bl_label = "Link Lightmaps"
    bl_description = "Link Lightmaps to NX Engine"
    bl_options = {'REGISTER', 'UNDO'}
        
    def execute(self, context):
        util.linkLightmap("//Lightmaps")
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        return {'PASS_THROUGH'}

    def cancel(self, context):
        return {'CANCELLED'}