import bpy
from bpy.utils import register_class, unregister_class
#from . import build, clean, explore, encode, installopencv
from . import scene, object

classes = [
    scene.TLM_SceneProperties,
    object.TLM_ObjectProperties,
    scene.TLM_UL_AtlasList,
    scene.TLM_AtlasListItem
]

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.TLM_SceneProperties = bpy.props.PointerProperty(type=scene.TLM_SceneProperties)
    bpy.types.Object.TLM_ObjectProperties = bpy.props.PointerProperty(type=object.TLM_ObjectProperties)
    bpy.types.Scene.TLM_AtlasList = bpy.props.CollectionProperty(type=scene.TLM_AtlasListItem)
    bpy.types.Scene.TLM_AtlasList_index = bpy.props.IntProperty(name="Index for my_list", default=0)

def unregister():
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.TLM_SceneProperties
    del bpy.types.Object.TLM_ObjectProperties