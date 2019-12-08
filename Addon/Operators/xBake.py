import bpy, os, blf

font_info = {
    "font_id": 0,
    "handler": None,
}

class XBake(bpy.types.Operator):
    bl_idname = "tlm.experiment_bake"
    bl_label = "Experiment Bake"

    _updating = False
    _calcs_done = False
    _timer = None
    _count = 0
    _handle = None

    # def invoke(self, context, event):
    #     print("Invoke...")
    #     import os
    #     # Create a new font object, use external ttf file.
    #     font_path = bpy.path.abspath('//Zeyada.ttf')
    #     # Store the font indice - to use later.
    #     if os.path.exists(font_path):
    #         font_info["font_id"] = blf.load(font_path)
    #     else:
    #         # Default font.
    #         font_info["font_id"] = 0

    #     # set the font drawing routine to run every frame
    #     font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')
    #     return {'RUNNING_MODAL'}

    def do_calcs(self):
        #print("Do Calc")

        #For list of baking objects?
        #for x in range(10):
        #    print("Something: " + str(x))
        #print(self._count)
        self._count = self._count + 1
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        if self._count == 1:
            bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=16)
            self._calcs_done = True

        # would be good if you can break up your calcs
        # so when looping over a list, you could do batches
        # of 10 or so by slicing through it.
        # do your calcs here and when finally done
        #self._calcs_done = True

    def modal(self, context, event):
        #print("Do Modal")
        context.area.tag_redraw()

        if not self._handle:
            args = (context, event)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        if event.type == 'TIMER' and not self._updating:
            self._updating = True
            self.do_calcs()
            self._updating = False

        if self._calcs_done:
            self.cancel(context)

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)

        return {'PASS_THROUGH'}

    def execute(self, context):
        #print("Do Exec")
        import os
        # Create a new font object, use external ttf file.
        font_path = bpy.path.abspath('//Zeyada.ttf')
        # Store the font indice - to use later.
        if os.path.exists(font_path):
            font_info["font_id"] = blf.load(font_path)
        else:
            # Default font.
            font_info["font_id"] = 0

        # set the font drawing routine to run every frame
        #font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        self._updating = False
        self._timer = context.window_manager.event_timer_add(time_step=0.5, window=context.window)
        args = (context, None)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        self._timer = None
        self._handle = None
        return {'CANCELLED'}

    def draw_callback_px(self, context, event):
        """Draw on the viewports"""
        # BLF drawing routine
        font_id = font_info["font_id"]
        blf.position(font_id, 2, 80, 0)
        blf.size(font_id, 50, 72)
        blf.draw(font_id, "Baking")