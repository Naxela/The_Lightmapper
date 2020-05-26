import bpy
from bpy.props import *
from bpy.types import Menu, Panel
from .. utility import icon

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
        sceneProperties = scene.TLM_SceneProperties

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

        #We list LuxCoreRender as available, by default we assume Cycles exists
        row.prop(sceneProperties, "tlm_lightmap_engine")

        if sceneProperties.tlm_lightmap_engine == "Cycles":

            #CYCLES SETTINGS HERE
            engineProperties = scene.TLM_EngineProperties

            row = layout.row(align=True)
            row.label(text="General Settings")
            row = layout.row(align=True)
            row.operator("tlm.build_lightmaps")
            row = layout.row(align=True)
            row.operator("tlm.clean_lightmaps")
            row = layout.row(align=True)
            row.operator("tlm.explore_lightmaps")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_apply_on_unwrap")

            row = layout.row(align=True)
            row.label(text="Cycles Settings")

            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_mode")
            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_quality")
            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_resolution_scale")
            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_bake_mode")
            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_caching_mode")
            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_directional_mode")
            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_lightmap_savedir")
            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_dilation_margin")
            row = layout.row(align=True)
            row.prop(engineProperties, "tlm_exposure_multiplier")

        elif sceneProperties.tlm_lightmap_engine == "LuxCoreRender":

            #LUXCORE SETTINGS HERE
            luxcore_available = False

            #Look for Luxcorerender in the renderengine classes
            for engine in bpy.types.RenderEngine.__subclasses__():
                if engine.bl_idname == "LUXCORE":
                    luxcore_available = True
                    break

            row = layout.row(align=True)
            if not luxcore_available:
                row.label(text="Please install BlendLuxCore.")
            else:
                row.label(text="LuxCoreRender not yet available.")

        elif sceneProperties.tlm_lightmap_engine == "OctaneRender":

            #LUXCORE SETTINGS HERE
            octane_available = False

            row = layout.row(align=True)
            row.label(text="Octane Render not yet available.")

class TLM_PT_Denoise(bpy.types.Panel):
    bl_label = "Denoise"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    def draw_header(self, context):
        scene = context.scene
        sceneProperties = scene.TLM_SceneProperties
        #self.layout.prop(sceneProperties, "tlm_denoise_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties
        #layout.active = sceneProperties.tlm_denoise_use

class TLM_PT_Filtering(bpy.types.Panel):
    bl_label = "Filtering"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"

    _module_installed = False

    def draw_header(self, context):
        scene = context.scene
        sceneProperties = scene.TLM_SceneProperties
        #self.layout.prop(sceneProperties, "tlm_filtering_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties

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
        sceneProperties = scene.TLM_SceneProperties

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
        sceneProperties = scene.TLM_SceneProperties

class TLM_PT_Selection(bpy.types.Panel):
    bl_label = "Selection"
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
        sceneProperties = scene.TLM_SceneProperties