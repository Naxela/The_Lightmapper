import bpy, importlib, math
from bpy.props import *
from bpy.types import Menu, Panel

class TLM_PT_Panel(bpy.types.Panel):
    bl_label = "The Lightmapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        row = layout.row(align=True)
        row.operator("tlm.build_lightmaps")
        row = layout.row(align=True)
        row.operator("tlm.apply_lightmaps")
        row = layout.row(align=True)
        row.operator("tlm.link_lightmaps")
        row = layout.row(align=True)
        row.operator("tlm.explore_lightmaps")
        row = layout.row(align=True)
        row.operator("tlm.clean_and_reassign_materials")

class TLM_PT_Settings(bpy.types.Panel):
    bl_label = "Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties

        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_setting_renderer", expand=True)
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_quality")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_bake_mode")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_directional")
        if sceneProperties.tlm_directional:
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_directional_mode")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_setting_scale", expand=True)
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_supersampling")
        if sceneProperties.tlm_supersampling != '0':
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_supersampling_filter")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_setting_savedir")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_reset_lightmap_uv")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_play_sound")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_material_multi_user")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_material_missing")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_dilation_margin")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_denoise_engine", expand=True)
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_format", expand=True)

        if sceneProperties.tlm_format == "KTX":

            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_tex_format")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_tex_compression")

            if sceneProperties.tlm_tex_compression:

                row = layout.row(align=True)
                row.prop(sceneProperties, "tlm_tex_compression_level")

        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_create_atlas")

        if sceneProperties.tlm_create_atlas:
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_atlas_max_resolution")

            # ── Atlas estimate info ──
            scale_div = int(sceneProperties.tlm_setting_scale)
            atlas_res = int(sceneProperties.tlm_atlas_max_resolution)
            atlas_area = atlas_res * atlas_res

            lm_objects = [obj for obj in scene.objects
                          if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use]
            lm_count = len(lm_objects)

            total_area = sum(
                (int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) // scale_div) ** 2
                for obj in lm_objects
            )

            if lm_count > 0 and atlas_area > 0:
                est_atlases = max(1, math.ceil(total_area / atlas_area))
                utilization = total_area / (est_atlases * atlas_area) * 100.0
            else:
                est_atlases = 0
                utilization = 0.0

            box = layout.box()
            col = box.column(align=True)
            col.scale_y = 0.75
            col.label(text=f"Lightmaps: {lm_count}   Est. atlases: {est_atlases}", icon='TEXTURE')
            col.label(text=f"Est. utilization: {utilization:.1f}%", icon='FULLSCREEN_ENTER')


class TLM_PT_Utilities(bpy.types.Panel):
    bl_label = "Utilities"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        props = scene.TLM_SceneProperties

        # ── Texel Density ──────────────────────────────────────────────────────
        col = layout.column(align=True)
        col.prop(props, "tlm_texel_size_cm")
        row = col.row(align=True)
        row.operator("tlm.texel_density_preview", icon='HIDE_OFF')
        row.operator("tlm.texel_density_apply",   icon='CHECKMARK')

        # Live summary: resolution range that would be assigned at current texel size
        enabled_objs = [
            obj for obj in scene.objects
            if obj.type == 'MESH' and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use
        ]
        if enabled_objs:
            texel_size_cm = props.tlm_texel_size_cm
            resolutions = []
            for obj in enabled_objs:
                area = 0.0
                mw = obj.matrix_world
                for poly in obj.data.polygons:
                    verts = [mw @ obj.data.vertices[i].co for i in poly.vertices]
                    for i in range(1, len(verts) - 1):
                        e1 = verts[i] - verts[0]
                        e2 = verts[i + 1] - verts[0]
                        area += e1.cross(e2).length * 0.5
                if area > 0.0:
                    raw = max(32.0, min(8192.0, (math.sqrt(area) * 100) / texel_size_cm))
                    lo = int(2 ** math.floor(math.log2(raw)))
                    hi = int(2 ** math.ceil(math.log2(raw)))
                    res = lo if abs(raw - lo) <= abs(raw - hi) else hi
                    resolutions.append(max(32, min(8192, res)))

            if resolutions:
                box = layout.box()
                col2 = box.column(align=True)
                col2.scale_y = 0.75
                col2.label(
                    text=f"Objects: {len(enabled_objs)}   Res range: {min(resolutions)}–{max(resolutions)}",
                    icon='TEXTURE'
                )