import bpy, blf, gpu, os
from gpu_extras.batch import batch_for_shader

# Text display class
class NX_Text_Display:
    
    def __init__(self, x, y, message, font_size=12, color=(0.0, 0.0, 0.0, 1.0)):
        self.x = x
        self.y = y
        self.message = message
        self.font_size = font_size
        self.color = color
        self.visible = False  # Toggle on/off state
        self.font_id = 0  # Default font
        self._handle = None  # Store the handler reference

    def draw(self):
        print(f"Drawing text: {self.message}, visible: {self.visible}")
        if not self.visible:
            return  # Don't draw if not visible

        # Set font size and position
        blf.position(self.font_id, self.x, self.y, 0)
        blf.size(self.font_id, self.font_size)
        
        # Set color
        blf.color(self.font_id, *self.color)
        
        # Draw text
        blf.draw(self.font_id, self.message)
    
    # Function to toggle visibility
    def toggle(self):
        # Only register the handler if it's not already registered
        if self._handle is None:
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (), 'WINDOW', 'POST_PIXEL')
        
        # Toggle visibility
        self.visible = not self.visible

        # Force a UI redraw to update the viewport
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    
    def draw_callback(self):
        self.draw()

    def remove(self):
        if self._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self._handle = None
