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
        row.prop(sceneProperties, "tlm_setting_scale", expand=True)
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_setting_savedir")
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