import bpy, os, time, blf
from .. Utility import utility

font_info = {
    "font_id": 0,
    "handler": None,
}

class TLM_BuildLightmaps(bpy.types.Operator):
    """Builds the lightmaps"""
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.baking_process = False
        print("Init bake")

        font_path = bpy.path.abspath('//Zeyada.ttf')
        # Store the font indice - to use later.

    def invoke(self, context, event):
        print("Running Invoke")

        args = (self, context)

        if(context.window_manager.TLM_Baking is False):
            context.window_manager.TLM_Baking = True
                
            self.register_handlers(args, context)

            font_path = bpy.path.abspath('//Zeyada.ttf')
            # Store the font indice - to use later.
            if os.path.exists(font_path):
                font_info["font_id"] = blf.load(font_path)
            else:
                # Default font.
                font_info["font_id"] = 0

            # set the font drawing routine to run every frame
            font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')
            # scene = context.scene
            # cycles = bpy.data.scenes[scene.name].cycles
            # utility.bake_ordered(self, context)

            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        else:
            context.window_manager.TLM_Baking = False
            return {'CANCELLED'}

    def register_handlers(self, args, context):
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (self, context), "WINDOW", "POST_PIXEL")
        self.font_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')
        self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)
        
    def unregister_handlers(self, context):
        context.window_manager.event_timer_remove(self.draw_event)
        
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")
        bpy.types.SpaceView3D.draw_handler_remove(self.font_handle, "WINDOW")
        self.draw_handle = None
        self.draw_event  = None
        self.font_handle = None

    def modal(self, context, event):
        print("Running Modal")

        context.area.tag_redraw()

        if self.baking_process is False:
            self.baking_process = True

            #self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (self, context), "WINDOW", "POST_PIXEL")
            self.font_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')
            self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)
            #bpy.context.ops(object.dp_ot_draw_operator)
            #scene = context.scene
            #cycles = bpy.data.scenes[scene.name].cycles
            #utility.bake_ordered(self, context)

        if context.area:
            context.area.tag_redraw()
                
        if context.area.type == 'VIEW_3D':
            return {'RUNNING_MODAL'}
            # if self.PN_Precon.handle_event(event):
            #     return {'RUNNING_MODAL'}
            # if self.PN_Bake.handle_event(event):
            #     return {'RUNNING_MODAL'} 
            # if self.PN_Postcon.handle_event(event):
            #     return {'RUNNING_MODAL'} 
            # if self.PN_Den.handle_event(event):
            #     return {'RUNNING_MODAL'} 
            # if self.PN_Fil.handle_event(event):
            #     return {'RUNNING_MODAL'} 
        
        if event.type in {"ESC"}:
            context.window_manager.TLM_Baking = False
        
        if not context.window_manager.TLM_Baking:
            self.unregister_handlers(context)
            return {'CANCELLED'}

        return {"PASS_THROUGH"}

    def cancel(self, context):
        print("Running Cancel")
        if context.window_manager.TLM_Baking:
            self.unregister_handlers(context)
        return {'CANCELLED'}        
        
    def finish(self):
        print("Running Finish")
        self.unregister_handlers(context)
        return {"FINISHED"}

    def draw_callback_px(self, context, args):
        print("Running Callback")

        font_id = font_info["font_id"]
        blf.position(font_id, 2, 80, 0)
        blf.size(font_id, 50, 72)
        blf.draw(font_id, "Hello World")



wm = bpy.types.WindowManager
wm.TLM_Baking = bpy.props.BoolProperty(default=False)


    # def modal(self, context, event):

    #     print("Test Baking...")

    #     return {'RUNNING_MODAL'}
    # def execute(self, context):

    #     scene = context.scene
    #     cycles = bpy.data.scenes[scene.name].cycles

    #     utility.bake_ordered(self, context)

    #     return{'FINISHED'}