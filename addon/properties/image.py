import bpy
from bpy.props import *

class TLM_ImageProperties(bpy.types.PropertyGroup):
    tlm_image_scale_engine : EnumProperty(
        items = [('OpenCV', 'OpenCV', 'TODO')],
                name = "Scaling engine", 
                description="TODO", 
                default='OpenCV')

        #('Native', 'Native', 'TODO'),

    tlm_image_scale_method : EnumProperty(
        items = [('Nearest', 'Nearest', 'TODO'),
                 ('Area', 'Area', 'TODO'),
                 ('Linear', 'Linear', 'TODO'),
                 ('Cubic', 'Cubic', 'TODO'),
                 ('Lanczos', 'Lanczos', 'TODO')],
                name = "Scaling method", 
                description="TODO", 
                default='Lanczos')

