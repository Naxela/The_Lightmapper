import bpy
from bpy.utils import register_class, unregister_class
#from . import build, clean, explore, encode, installopencv
from . import scene, object

classes = [
    scene.TLM_SceneProperties,
    object.TLM_ObjectProperties
]

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.TLM_SceneProperties = bpy.props.PointerProperty(type=scene.TLM_SceneProperties)
    bpy.types.Object.TLM_ObjectProperties = bpy.props.PointerProperty(type=object.TLM_ObjectProperties)
        
def unregister():
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.TLM_SceneProperties
    del bpy.types.Object.TLM_ObjectProperties