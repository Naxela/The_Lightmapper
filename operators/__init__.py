import bpy
from bpy.utils import register_class, unregister_class
from . import tlm

# Define a function to add the Lightmapping menu to the Object menu
def menu_func(self, context):
    layout = self.layout
    layout.separator()  # Optional separator for better visual separation
    layout.menu("OBJECT_MT_lightmapping_menu")

# Create a custom menu with Lightmapping options
class OBJECT_MT_lightmapping_menu(bpy.types.Menu):
    bl_label = "Lightmapping"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("object.lightmap_enable", text="Enable lightmapping")
        layout.operator("object.lightmap_disable", text="Disable lightmapping")
        layout.operator("tlm.disable_spec", text="Disable Specular")
        layout.operator("tlm.disable_metallic", text="Disable Metallic")

classes = [
    tlm.TLM_BuildLightmaps,
    tlm.TLM_ApplyLightmaps,
    tlm.TLM_LinkLightmaps,
    tlm.TLM_ExploreLightmaps,
    tlm.TLM_CleanAndReassignMaterials,
    tlm.TLM_OBJECT_OT_lightmap_enable,
    tlm.TLM_OBJECT_OT_lightmap_disable,
    tlm.TLM_OBJECT_OT_selected_lightmapped,
    OBJECT_MT_lightmapping_menu,
    tlm.TLM_MatProperties,
    tlm.TLM_OBJECT_OT_lightmap_oneup,
    tlm.TLM_OBJECT_OT_lightmap_onedown,
    tlm.TLM_OBJECT_OT_lightmap_removeuv,
    tlm.TLM_DisableSpec,
    tlm.TLM_DisableMetallic,
    tlm.TLM_removeMatLink,
    tlm.TLM_Atlas
]

def menu_func_select_object(self, context):
    layout = self.layout
    layout.operator("object.selected_lightmapped", text="Select Lightmapped")

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_select_object.append(menu_func_select_object)

def unregister():
    for cls in classes:
        unregister_class(cls)

    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.types.VIEW3D_MT_select_object.remove(menu_func_select_object)