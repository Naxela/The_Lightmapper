import bpy
import gpu
import blf
import os
import bgl
import sys

from gpu_extras.batch import batch_for_shader
from bpy.types import Operator
from bpy.props import *

font_info = {
    "font_0": 0,
    "handler": None,
}

baking_progress = [
    0.0, #PRECON
    0.0, #BAKING
    0.0, #POSTCON
    0.0, #DEN
    0.0  #FIL
]

class Progress_Bar:
    
    def __init__(self, x, y, width, height, progress):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.progress = progress
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.is_drag = False
        self.color = (0.2, 0.9, 0.9, 0.1)
        self.update(self.x, self.y, self.width, self.height, self.progress)
        
        font_path = bpy.path.abspath('//Zeyada.ttf')
        if os.path.exists(font_path):
            font_info["font_0"] = blf.load(font_path)
#            font_info1["font_id"] = blf.load(font_path)
#            font_info2["font_id"] = blf.load(font_path)
#            font_info3["font_id"] = blf.load(font_path)
#            font_info4["font_id"] = blf.load(font_path)
        else:
            # Default font.
            font_info["font_0"] = 0
#            font_info1["font_id"] = 1
#            font_info2["font_id"] = 2
#            font_info3["font_id"] = 3
#            font_info4["font_id"] = 4
        
    def set_color(self, color):
        self.color = color
    
    def draw(self):
        self.shader.bind()
        self.shader.uniform_float("color", self.color)
        
        bgl.glEnable(bgl.GL_BLEND)
        self.batch_panel.draw(self.shader)
        self.batch_panel2.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)
    
    def update(self, x, y, width, height, progress):
        
        indices = ((0, 1, 2), (0, 2, 3))
        
        self.x = x - self.drag_offset_x
        self.y = y - self.drag_offset_y
        self.width = width
        self.height = height
        self.progress = progress
        
        if self.progress > 1.0:
            self.progress = 1.0
        
        if self.progress < 0.0:
            self.progress = 0.0
        
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        
        self.inset = 2
        
        # bottom left, top left, top right, bottom right
        verticesBorder = (
                    (self.x, self.y), 
                    (self.x, self.y + self.height), 
                    (self.x + self.width * self.progress, self.y + self.height),
                    (self.x + self.width * self.progress, self.y))
                    
        self.batch_panel = batch_for_shader(self.shader, 'LINE_LOOP', {"pos" : verticesBorder})
        #self.batch_panel = batch_for_shader(self.shader, 'TRIS', {"pos" : vertices}, indices=indices)
        
        verticesInner = (
                    (self.x + self.inset, self.y + self.inset), 
                    (self.x + self.inset, self.y + self.height - self.inset + 1), 
                    (self.x - self.inset + 1 + self.width * self.progress, self.y - self.inset + 1 + self.height),
                    (self.x - self.inset + 1 + self.width * self.progress, self.y + self.inset))
        
        self.batch_panel2 = batch_for_shader(self.shader, 'TRIS', {"pos" : verticesInner}, indices=indices)
    
    def handle_event(self, event):
        if(event.type == 'LEFTMOUSE'):
            if(event.value == 'PRESS'):
                return self.mouse_down(event.mouse_region_x, event.mouse_region_y)
            else:
                self.mouse_up(event.mouse_region_x, event.mouse_region_y)
                
        
        elif(event.type == 'MOUSEMOVE'):
            self.mouse_move(event.mouse_region_x, event.mouse_region_y)
            return True
                        
        return False                 


    def is_in_rect(self, x, y):
        
        if (
            (self.x <= x <= (self.x + self.width)) and 
            (self.y <= y <= (self.y + self.height))
            ):
            return True
           
        return False      

    def mouse_down(self, x, y):
        
        if self.is_in_rect(x,y):
            self.is_drag = True
            self.drag_offset_x = x - self.x
            self.drag_offset_y = y - self.y
            return True
        
        return False

    def mouse_move(self, x, y):
        if self.is_drag:
            self.update(x, y)

    def mouse_up(self, x, y):
        self.is_drag = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
class DP_OT_draw_operator(Operator):
    bl_idname = "object.dp_ot_draw_operator"
    bl_label = "Progress_Bar"
    bl_description = "Progress_Bar" 
    bl_options = {'REGISTER'}
        
    @classmethod
    def poll(cls, context):
        return True
    
    def __init__(self):
        #print("Running Init")
        self.draw_handle = None
        self.draw_event  = None
        
        self.num = 0
        
        transparency = 0.3
        
        self.PN_Precon = Progress_Bar(10, 70, 100, 12, 0)
        self.PN_Precon.set_color((1.0, 0.0, 0.0, transparency))
        self.PN_Bake = Progress_Bar(10, 55, 100, 12, baking_progress[1])
        self.PN_Bake.set_color((0.0, 0.0, 1.0, transparency))
        self.PN_Postcon = Progress_Bar(10, 40, 100, 12, baking_progress[2])
        self.PN_Postcon.set_color((0.0, 1.0, 0.0, transparency))
        self.PN_Den = Progress_Bar(10, 25, 100, 12, baking_progress[3])
        self.PN_Den.set_color((1.0, 1.0, 0.0, transparency))
        self.PN_Fil = Progress_Bar(10, 10, 100, 12, baking_progress[4])
        self.PN_Fil.set_color((0.5, 0.5, 0.5, transparency))
        
#        self.panel = Drag_Panel(10, 10, 100, 20)
#        self.panel.set_color((1.0, 0.2, 0.2, 1.0))

    def invoke(self, context, event):
        #print("Running Invoke")
        args = (self, context)
        
        if(context.window_manager.DP_started is False):
            context.window_manager.DP_started = True
                
            # Register draw callback
            self.register_handlers(args, context)
                       
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        else:
            context.window_manager.DP_started = False
            #print("Cancelled")
            return {'CANCELLED'}
    
    def register_handlers(self, args, context):
        #print("Register handlers")
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (self, context), "WINDOW", "POST_PIXEL")
        self.font_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')
        self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)
        
    def unregister_handlers(self, context):
        #print("Unregister handlers")
        context.window_manager.event_timer_remove(self.draw_event)
        
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")
        bpy.types.SpaceView3D.draw_handler_remove(self.font_handle, "WINDOW")
        
        self.draw_handle = None
        self.draw_event  = None
        self.font_handle = None
     
           
    def modal(self, context, event):
        #print("Running Modal")
        if context.area:
            context.area.tag_redraw()
                
        if context.area.type == 'VIEW_3D':
            if self.PN_Precon.handle_event(event):
                return {'RUNNING_MODAL'}
            if self.PN_Bake.handle_event(event):
                return {'RUNNING_MODAL'} 
            if self.PN_Postcon.handle_event(event):
                return {'RUNNING_MODAL'} 
            if self.PN_Den.handle_event(event):
                return {'RUNNING_MODAL'} 
            if self.PN_Fil.handle_event(event):
                return {'RUNNING_MODAL'} 
        
        if event.type in {"ESC"}:
            context.window_manager.DP_started = False
        
        if not context.window_manager.DP_started:
            self.unregister_handlers(context)
            return {'CANCELLED'}
        
        
        #print(self.num, flush=True)
        #sys.stdout.write("\r%d%%" % self.num)
        #sys.stdout.write("\r%d%%" % baking_progress[0])
        #sys.stdout.flush()
        
        self.num = self.num + 1
        baking_progress[0] = self.num / 100
        baking_progress[1] = (self.num-100) / 100
        baking_progress[2] = (self.num-200) / 100
        baking_progress[3] = (self.num-300) / 100
        baking_progress[4] = (self.num-400) / 100
        
        self.PN_Precon.update(self.PN_Precon.x, self.PN_Precon.y, self.PN_Precon.width, self.PN_Precon.height, baking_progress[0])
        self.PN_Bake.update(self.PN_Bake.x, self.PN_Bake.y, self.PN_Bake.width, self.PN_Bake.height, baking_progress[1])
        self.PN_Postcon.update(self.PN_Postcon.x, self.PN_Postcon.y, self.PN_Postcon.width, self.PN_Postcon.height, baking_progress[2])
        self.PN_Den.update(self.PN_Den.x, self.PN_Den.y, self.PN_Den.width, self.PN_Den.height, baking_progress[3])
        self.PN_Fil.update(self.PN_Fil.x, self.PN_Fil.y, self.PN_Fil.width, self.PN_Fil.height, baking_progress[4])
        
        if baking_progress[0] > 0.99:
            if baking_progress[1] > 0.99:
                if baking_progress[2] > 0.99:
                    if baking_progress[3] > 0.99:
                        if baking_progress[4] > 0.99:
                            context.window_manager.DP_started = False
             
               
        return {"PASS_THROUGH"}
                            
        
    def cancel(self, context):
        #print("Running Cancel")
        if context.window_manager.DP_started:
            self.unregister_handlers(context)
        return {'CANCELLED'}        
        
    def finish(self):
        #print("Running Finish")
        self.unregister_handlers(context)
        return {"FINISHED"}
        
        # Draw handler to paint onto the screen
    def draw_callback_px(self, context, args):

        self.PN_Precon.draw()
        self.PN_Bake.draw()
        self.PN_Postcon.draw()
        self.PN_Den.draw()
        self.PN_Fil.draw()
        
        font_id = font_info["font_0"]
        blf.position(font_id, 115, 13, 0)
        blf.size(font_id, 10, 72)
        blf.draw(font_id, "Filtering")
        blf.color(font_id, 1, 1, 1, 1)
        blf.position(font_id, 115, 13, 0)
        blf.size(font_id, 10, 72)
        blf.draw(font_id, "Filtering")
        blf.color(font_id, 1, 1, 1, 1)
        
        blf.position(font_id, 115, 28, 0)
        blf.size(font_id, 10, 72)
        blf.draw(font_id, "Denoising")
        blf.color(font_id, 1, 1, 1, 1)

        blf.position(font_id, 115, 43, 0)
        blf.size(font_id, 10, 72)
        blf.draw(font_id, "Postconfiguration")
        blf.color(font_id, 1, 1, 1, 1)
        
        blf.position(font_id, 115, 58, 0)
        blf.size(font_id, 10, 72)
        blf.draw(font_id, "Baking")
        blf.color(font_id, 1, 1, 1, 1)
        
        blf.position(font_id, 115, 73, 0)
        blf.size(font_id, 10, 72)
        blf.draw(font_id, "Preconfiguration")
        blf.color(font_id, 1, 1, 1, 1)
        

wm = bpy.types.WindowManager
wm.DP_started = bpy.props.BoolProperty(default=False)

addon_keymaps = []

def register():
    
    bpy.utils.register_class(DP_OT_draw_operator)
    kcfg = bpy.context.window_manager.keyconfigs.addon
    if kcfg:
        km = kcfg.keymaps.new(name='3D View', space_type='VIEW_3D')
   
        kmi = km.keymap_items.new("object.dp_ot_draw_operator", 'F', 'PRESS', shift=True, ctrl=True)
        
        addon_keymaps.append((km, kmi))
   
def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
   
    bpy.utils.unregister_class(DP_OT_draw_operator)
    
if __name__ == "__main__":
    register()