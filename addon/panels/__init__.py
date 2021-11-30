import bpy, os
from bpy.utils import register_class, unregister_class
from . import scene, object, light, world, image

classes = [
    scene.TLM_PT_Panel,
    scene.TLM_PT_Groups,
    scene.TLM_PT_Settings,
    scene.TLM_PT_Denoise,
    scene.TLM_PT_Filtering,
    scene.TLM_PT_Encoding,
    scene.TLM_PT_Utility,
    #scene.TLM_PT_Selection,
    scene.TLM_PT_Additional,
    object.TLM_PT_ObjectMenu,
    object.TLM_PT_MaterialMenu,
    light.TLM_PT_LightMenu,
    world.TLM_PT_WorldMenu,
    image.TLM_PT_Imagetools
]

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)