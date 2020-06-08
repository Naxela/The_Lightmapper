import bpy
from bpy.utils import register_class, unregister_class
from . import scene, object
from . renderer import cycles
from . denoiser import oidn, optix

classes = [
    scene.TLM_SceneProperties,
    object.TLM_ObjectProperties,
    cycles.TLM_CyclesSceneProperties,
    oidn.TLM_OIDNEngineProperties

    #scene.TLM_UL_AtlasList,
    #scene.TLM_AtlasListItem
]

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.TLM_SceneProperties = bpy.props.PointerProperty(type=scene.TLM_SceneProperties)
    bpy.types.Object.TLM_ObjectProperties = bpy.props.PointerProperty(type=object.TLM_ObjectProperties)
    
    #If...
    bpy.types.Scene.TLM_EngineProperties = bpy.props.PointerProperty(type=cycles.TLM_CyclesSceneProperties)
    bpy.types.Scene.TLM_OIDNEngineProperties = bpy.props.PointerProperty(type=cycles.TLM_CyclesSceneProperties)
    #bpy.types.Scene.TLM_AtlasList = bpy.props.CollectionProperty(type=scene.TLM_AtlasListItem)
    #bpy.types.Scene.TLM_AtlasList_index = bpy.props.IntProperty(name="Index for my_list", default=0)

def unregister():
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.TLM_SceneProperties
    del bpy.types.Object.TLM_ObjectProperties
    del bpy.types.Scene.TLM_EngineProperties
    del bpy.types.Scene.TLM_OIDNEngineProperties