import bpy
from bpy.utils import register_class, unregister_class
from . import scene, object, light
from bpy.props import *

# classes = [
#     scene.TLMSceneProperties,
#     object.TLMObjectProperties,
#     light.TLMLightProperties
# ]


def register():
    #for cls in classes:
    #    register_class(cls)
    scene.register()
    object.register()

def unregister():
    for cls in classes:
        unregister_class(cls)