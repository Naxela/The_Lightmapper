import bpy
from bpy.props import *
from bpy.types import Menu, Panel
from ... addon.properties import scene
from .. import icon
from .. import module

class TLM_PT_Panel(bpy.types.Panel):
    bl_label = "The Lightmapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        row = layout.row(align=True)
        row.operator("tlm.build_lightmaps", icon="NONE", icon_value=icon.id("bake"))
        row = layout.row(align=True)
        row.prop(scene, "tlm_bake_for_selection")
        row = layout.row(align=True)
        row.operator("tlm.clean_lightmaps", icon="NONE", icon_value=icon.id("clean"))
        row = layout.row(align=True)
        row.prop(scene, "tlm_clean_for_selection")
        row = layout.row(align=True)
        row.operator("tlm.explore_lightmaps", icon="NONE", icon_value=icon.id("explore"))

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
        row = layout.row(align=True)
        row.prop(scene, 'tlm_quality')
        row = layout.row(align=True)
        row.prop(scene, 'tlm_lightmap_scale', expand=True)
        row = layout.row(align=True)
        row.prop(scene, 'tlm_lightmap_savedir')
        row = layout.row(align=True)
        row.prop(scene, 'tlm_mode')
        row = layout.row(align=True)
        row.prop(scene, 'tlm_apply_on_unwrap')
        row = layout.row(align=True)
        row.prop(scene, 'tlm_dilation_margin')
        row = layout.row(align=True)
        row.prop(scene, 'tlm_indirect_only')

class TLM_PT_Denoise(bpy.types.Panel):
    bl_label = "Denoise"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw_header(self, context):
        scene = context.scene
        self.layout.prop(scene, "tlm_denoise_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene
        layout.active = scene.tlm_denoise_use

        row = layout.row(align=True)
        row.prop(scene, "tlm_oidn_path")
        row = layout.row(align=True)
        row.prop(scene, "tlm_oidn_verbose")
        row = layout.row(align=True)
        row.prop(scene, "tlm_oidn_threads")
        row = layout.row(align=True)
        row.prop(scene, "tlm_oidn_maxmem")
        row = layout.row(align=True)
        row.prop(scene, "tlm_oidn_affinity")

class TLM_PT_Filtering(bpy.types.Panel):
    bl_label = "Filtering"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw_header(self, context):
        scene = context.scene
        self.layout.prop(scene, "tlm_filtering_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False

        column = layout.column()
        box = column.box()
        if module.checkModules():
            box.label(text="OpenCV Installed", icon="INFO")
        else:
            box.label(text="Please restart Blender after installing")
            box.operator("tlm.install_opencv",icon="PREFERENCES")

        if(scene.tlm_filtering_use):
            if(module.checkModules()):
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

        row = layout.row(align=True)
        row.prop(scene, "tlm_filtering_mode")
        row = layout.row(align=True)
        if scene.hdrlm_filtering_mode == "Gaussian":
            row.prop(scene, "tlm_filtering_gaussian_strength")
            row = layout.row(align=True)
            row.prop(scene, "tlm_filtering_iterations")
        elif scene.hdrlm_filtering_mode == "Box":
            row.prop(scene, "tlm_filtering_box_strength")
            row = layout.row(align=True)
            row.prop(scene, "tlm_filtering_iterations")

        elif scene.hdrlm_filtering_mode == "Bilateral":
            row.prop(scene, "tlm_filtering_bilateral_diameter")
            row = layout.row(align=True)
            row.prop(scene, "tlm_filtering_bilateral_color_deviation")
            row = layout.row(align=True)
            row.prop(scene, "tlm_filtering_bilateral_coordinate_deviation")
            row = layout.row(align=True)
            row.prop(scene, "tlm_filtering_iterations")
        else:
            row.prop(scene, "tlm_filtering_median_kernel", expand=True)
            row = layout.row(align=True)
            row.prop(scene, "tlm_filtering_iterations")

class TLM_PT_Encoding(bpy.types.Panel):
    bl_label = "Encoding"
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
        row = layout.row(align=True)
        row.prop(scene, "tlm_encoding_mode", expand=True)
        if scene.tlm_encoding_mode == "RGBM" or scene.tlm_encoding_mode == "RGBD":
            row = layout.row(align=True)
            row.prop(scene, "tlm_encoding_range")
            row = layout.row(align=True)
            row.prop(scene, "tlm_encoding_armory_setup")
        row = layout.row(align=True)
        row.prop(scene, "tlm_encoding_colorspace")

class TLM_PT_Compression(bpy.types.Panel):
    bl_label = "Compression"
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
        if scene.tlm_encoding_mode == "RGBE":
            layout.label(text="HDR compression not available for RGBE")
        else:
            row = layout.row(align=True)
            row.prop(scene, "tlm_compression")

class TLM_PT_Additional(bpy.types.Panel):
    bl_label = "Additional"
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
        layout.label(text="Enable for selection")
        layout.label(text="Disable for selection")
        layout.label(text="Something...")