import bpy
from bpy.props import *

class TLM_AtlasListItem(bpy.types.PropertyGroup):
    obj: PointerProperty(type=bpy.types.Object, description="The object to bake")
    tlm_atlas_lightmap_resolution : EnumProperty(
        items = [('32', '32', 'TODO'),
                 ('64', '64', 'TODO'),
                 ('128', '128', 'TODO'),
                 ('256', '256', 'TODO'),
                 ('512', '512', 'TODO'),
                 ('1024', '1024', 'TODO'),
                 ('2048', '2048', 'TODO'),
                 ('4096', '4096', 'TODO'),
                 ('8192', '8192', 'TODO')],
                name = "Atlas Lightmap Resolution", 
                description="TODO",
                default='256')

    tlm_atlas_unwrap_margin : FloatProperty(
        name="Unwrap Margin", 
        default=0.1, 
        min=0.0, 
        max=1.0, 
        subtype='FACTOR')

    tlm_atlas_lightmap_unwrap_mode : EnumProperty(
        items = [('Lightmap', 'Lightmap', 'TODO'),
                 ('SmartProject', 'Smart Project', 'TODO')],
                name = "Unwrap Mode", 
                description="TODO", 
                default='SmartProject')

class TLM_UL_AtlasList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            amount = 0

            for obj in bpy.data.objects:
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup":
                        if obj.TLM_ObjectProperties.tlm_atlas_pointer == item.name:
                            amount = amount + 1

            row = layout.row()
            row.prop(item, "name", text="", emboss=False, icon=custom_icon)
            col = row.column()
            col.label(text=item.tlm_atlas_lightmap_resolution)
            col = row.column()
            col.alignment = 'RIGHT'
            col.label(text=str(amount))

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)