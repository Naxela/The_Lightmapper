import bpy, math
from bpy.props import *
from bpy.types import Menu, Panel

class TLM_PT_ObjectMenu(bpy.types.Panel):
    bl_label = "The Lightmapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = bpy.context.object
        layout.use_property_split = True
        layout.use_property_decorate = False

        if obj.type == "MESH":
            row = layout.row(align=True)
            row.prop(obj.TLM_ObjectProperties, "tlm_mesh_lightmap_use")

            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                row = layout.row(align=True)
                row.prop(obj.TLM_ObjectProperties, "tlm_mesh_lightmap_resolution")

                # Live texel density readout
                res = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution)
                area = 0.0
                mw = obj.matrix_world
                for poly in obj.data.polygons:
                    verts = [mw @ obj.data.vertices[i].co for i in poly.vertices]
                    for i in range(1, len(verts) - 1):
                        e1 = verts[i] - verts[0]
                        e2 = verts[i + 1] - verts[0]
                        area += e1.cross(e2).length * 0.5
                if area > 0.0:
                    cm_per_texel = (math.sqrt(area) * 100) / res
                    row = layout.row(align=True)
                    row.enabled = False
                    row.label(text=f"Texel size: {cm_per_texel:.2f} cm/texel")

                row = layout.row(align=True)
                row.prop(obj.TLM_ObjectProperties, "tlm_uv_channel")
                row = layout.row(align=True)
                row.prop(obj.TLM_ObjectProperties, "tlm_mesh_lightmap_unwrap_mode")

                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == 'Lightmap':
                    row = layout.row(align=True)
                    row.prop(obj.TLM_ObjectProperties, "tlm_use_per_object_lightmap_pack")

                    if obj.TLM_ObjectProperties.tlm_use_per_object_lightmap_pack:
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_lightmap_pack_selection")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_lightmap_pack_share_space")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_lightmap_pack_new_uv")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_lightmap_pack_quality")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_lightmap_pack_margin")

                elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == 'SmartProject':
                    row = layout.row(align=True)
                    row.prop(obj.TLM_ObjectProperties, "tlm_use_per_object_unwrap")

                    if obj.TLM_ObjectProperties.tlm_use_per_object_unwrap:
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_smart_project_angle_limit")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_smart_project_margin_method")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_smart_project_rotation_method")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_smart_project_island_margin")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_smart_project_area_weight")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_smart_project_correct_aspect")
                        row = layout.row(align=True)
                        row.prop(obj.TLM_ObjectProperties, "tlm_smart_project_scale_to_bounds")