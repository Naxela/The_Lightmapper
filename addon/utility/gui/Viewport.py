import bpy, blf, os, gpu
from gpu_extras.batch import batch_for_shader

class ViewportDraw:

    def __init__(self, context, text):

        bakefile = "TLM_Overlay.png"
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        bakefile_path = os.path.abspath(os.path.join(scriptDir, '..', '..', 'assets', bakefile))

        image_name = "TLM_Overlay.png"

        bpy.ops.image.open(filepath=bakefile_path)

        print("Self path: " + bakefile_path)

        image = None
        for img in bpy.data.images:
            if img.filepath.endswith(image_name):
                image = img
                break

        if not image:
            image = bpy.data.images[image_name]

        x = 15
        y = 15
        w = 400
        h = 200

        # Changed from '2D_IMAGE' to 'IMAGE' in Blender 4.0+
        self.shader = gpu.shader.from_builtin('IMAGE')
        self.batch = batch_for_shader(
            self.shader, 'TRI_FAN',
            {
                "pos": ((x, y), (x+w, y), (x+w, y+h), (x, y+h)),
                "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
            },
        )

        self.text = text
        self.image = image
        # Create GPU texture from image
        self.gpu_texture = gpu.texture.from_image(self.image)
        
        self.handle2 = bpy.types.SpaceView3D.draw_handler_add(self.draw_image_callback, (context,), 'WINDOW', 'POST_PIXEL')

    def draw_text_callback(self, context):

        font_id = 0
        blf.position(font_id, 15, 15, 0)
        blf.size(font_id, 20)  # Note: dpi parameter removed in Blender 4.0
        blf.draw(font_id, "%s" % (self.text))

    def draw_image_callback(self, context):
        
        if self.image:
            # Use gpu.state for blend mode
            gpu.state.blend_set('ALPHA')
            
            try:
                # Recreate texture if needed (in case image was reloaded)
                if self.gpu_texture is None:
                    self.gpu_texture = gpu.texture.from_image(self.image)
                
                self.shader.bind()
                self.shader.uniform_sampler("image", self.gpu_texture)
                self.batch.draw(self.shader)
            except Exception as e:
                print(f"Draw error: {e}")
                bpy.types.SpaceView3D.draw_handler_remove(self.handle2, 'WINDOW')
            finally:
                # Restore blend mode
                gpu.state.blend_set('NONE')

    def update_text(self, text):

        self.text = text

    def remove_handle(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.handle2, 'WINDOW')
        # Clean up texture reference
        self.gpu_texture = None
