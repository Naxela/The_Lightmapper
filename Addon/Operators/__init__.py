import bpy
from bpy.utils import register_class, unregister_class
from . import build, clean, explore, encode, installopencv, gui, xBake, selection, additional, lighttools

classes = [
    build.TLM_BuildLightmaps,
    clean.TLM_CleanLightmaps,
    encode.TLM_EncodeLightmaps,
    explore.TLM_ExploreLightmaps,
    installopencv.TLM_Install_OpenCV,
    selection.TLM_EnableSelection,
    selection.TLM_DisableSelection,
    selection.TLM_RemoveLightmapUV,
    additional.TLM_AtlasListNewItem,
    additional.TLM_AtlastListDeleteItem,
    additional.TLM_AtlasListMoveItem,
    lighttools.TLM_Downsize,
    lighttools.TLM_Upsize
    #xBake.XBake
]

gui.register()

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.IMAGE_PT_image_properties.append(lighttools.draw)
    bpy.types.Scene.tlm_image_interpolation = bpy.props.EnumProperty(
        items = [('INTER_LINEAR', 'INTER_LINEAR', 'TODO'),
                ('INTER_NEAREST', 'INTER_NEAREST', 'TODO'),
                ('INTER_AREA', 'INTER_AREA', 'TODO'),
                ('INTER_CUBIC', 'INTER_CUBIC', 'TODO'),
                ('INTER_LANCZOS4', 'INTER_LANCZOS4', 'TODO')],
                name = "", 
                description="TODO",
                default='INTER_NEAREST')
        
def unregister():
    for cls in classes:
        unregister_class(cls)

    bpy.types.IMAGE_PT_image_properties.remove(lighttools.draw)