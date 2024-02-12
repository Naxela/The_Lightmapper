import bpy, blf, gpu, os
from gpu_extras.batch import batch_for_shader

# Progress
class NX_Progress_Bar:
    
    def __init__(self, x, y, width, height, progress, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.progress = progress
        self.color = color
        
        self.inset = 2
        self.font_id = self.load_font()
    
    def load_font(self):
        return 0
        #font_path = bpy.path.abspath('//Zeyada.ttf')
        #if os.path.exists(font_path):
        #    return blf.load(font_path)
        #else:
            # Return default font ID if custom font is not found
        #    return 0
    
    def draw(self):
        progress_width = self.width * self.progress
        if(progress_width < 0.01):
            progress_status = "Starting"
        elif(progress_width > 99.9):
            progress_status = "Please wait..."
        else:
            progress_status = str(round(progress_width)) + "%"
            
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        
        vertices_outline = [(self.x - self.inset, self.y - self.inset), 
                    (self.x + self.width + self.inset / 2, self.y - self.inset), 
                    (self.x + self.width + self.inset / 2, self.y + self.height + self.inset/2), 
                    (self.x - self.inset, self.y + self.height + self.inset/2)]
        
        indices_outline = [(0, 1), (1, 2), (2, 3), (3, 0)]
        batch_outline = batch_for_shader(shader, 'LINES', {"pos": vertices_outline}, indices=indices_outline)
        
        vertices_bar = [(self.x, self.y), 
                    (self.x + progress_width, self.y), 
                    (self.x + progress_width, self.y + self.height), 
                    (self.x, self.y + self.height)]
        indices_bar = [(0, 1, 2), (0, 2, 3)]
        
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch_bar = batch_for_shader(shader, 'TRIS', {"pos": vertices_bar}, indices=indices_bar)
        
        shader.bind()
        shader.uniform_float("color", self.color)
        batch_outline.draw(shader)
        batch_bar.draw(shader)
        
        # Setting up and drawing the text
        blf.position(self.font_id, self.x + self.width + 5, self.y + self.height / 2 - 3, 0)
        blf.size(self.font_id, 10)
        blf.color(self.font_id, 0.0, 0.0, 0.0, 1.0)
        blf.draw(self.font_id, f"Building Lightmaps: {progress_status}")