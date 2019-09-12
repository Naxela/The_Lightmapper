import bpy
from bpy.utils import register_class, unregister_class
#from . import build, clean, explore, encode, installopencv
from . import scene

classes = [
    scene.TLM_SceneProperties
]

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.TLM_Properties = bpy.props.PointerProperty(type=scene.TLM_SceneProperties)
        
def unregister():
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.TLM_Properties