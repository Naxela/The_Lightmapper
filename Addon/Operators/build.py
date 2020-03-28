import bpy, os, time, blf
#from .. Utility import utility
from .. Utility import bake_run

font_info = {
    "font_id": 0,
    "handler": None,
}

class TLM_BuildLightmaps(bpy.types.Operator):
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _time = ""
    _handle = None
    _warm_up = 0

    def modal(self, context, event):
        #print("Modal...")
        context.area.tag_redraw()

        scene = context.scene
        cycles = scene.cycles

        if event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if self._warm_up < 1:
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                self._warm_up = self._warm_up + 1
                #print("Heating up - time: " + str(self._warm_up))
            else:

                if scene.TLM_SceneProperties.tlm_bake_for_selection:

                    previousToggle = []

                    for obj in bpy.data.objects:
                        if(obj.TLM_ObjectProperties.tlm_mesh_lightmap_use):
                            previousToggle.append(obj.name)
                        obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = False

                    for obj in bpy.context.selected_objects:
                        obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = True

                cycles = bpy.data.scenes[scene.name].cycles

                #utility.bake_ordered(self, context, None)
                bake_run.bake_ordered(self, context, None)

                if scene.TLM_SceneProperties.tlm_bake_for_selection:
                    for obj in bpy.data.objects:
                        obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = False
                        if obj.name in previousToggle:
                            obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = True

                self._handle = bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                #print("Finished...")
                return {'FINISHED'}
            
            #bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            #self._time = str(time.strftime('%X %x %Z'))

        return {'PASS_THROUGH'}

    def invoke(self, context, event):

        #self._time = str(time.strftime('%X %x %Z'))
        
        #Clean lightmaps first?
        bpy.ops.tlm.clean_lightmaps()

        font_path = bpy.path.abspath('//Zeyada.ttf')
        # Store the font indice - to use later.
        if os.path.exists(font_path):
            font_info["font_id"] = blf.load(font_path)
        else:
            # Default font.
            font_info["font_id"] = 0

        args = (context, event)

        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        #print("Invoked..")

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        self._handle = bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        #print("Cancel..")

    def draw_callback_px(self, context, event):
        """Draw on the viewports"""
        # BLF drawing routine
        font_id = font_info["font_id"]
        blf.position(font_id, 10, 10, 0)
        blf.size(font_id, 20, 42)
        blf.draw(font_id, "Building lightmaps")
