import bpy
from bpy.props import *
from bpy.types import Menu, Panel
from .. Utility import icon

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
        row = layout.row(align=True)
        row.operator("tlm.build_lightmaps", icon="NONE", icon_value=icon.id("bake"))
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_bake_for_selection")
        row = layout.row(align=True)
        row.operator("tlm.clean_lightmaps", icon="NONE", icon_value=icon.id("clean"))
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_clean_option")
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
        sceneProperties = scene.TLM_SceneProperties
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_mode")
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_quality')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_bake_mode')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_caching_mode')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_baketime_material')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_directional_mode')

        if not sceneProperties.tlm_directional_mode == "None":
            row = layout.row(align=True)
            row.prop(sceneProperties, 'tlm_bake_normal_denoising')

        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_lightmap_scale', expand=True)
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_lightmap_savedir')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_dilation_margin')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_exposure_multiplier')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_default_color')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_apply_on_unwrap')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_indirect_only')
        row = layout.row(align=True)
        if sceneProperties.tlm_indirect_only:
            row.prop(sceneProperties, 'tlm_indirect_mode')
            row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_keep_cache_files')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_clamp_metallic')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_play_sound')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_headless')
        row = layout.row(align=True)
        row.prop(sceneProperties, 'tlm_compile_statistics')

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
        self.layout.prop(sceneProperties, "tlm_denoise_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties
        layout.active = sceneProperties.tlm_denoise_use
        row = layout.row(align=True)

        row.prop(sceneProperties, "tlm_denoiser", expand=True)
        row = layout.row(align=True)

        if sceneProperties.tlm_denoiser == "OIDN":
            row.prop(sceneProperties, "tlm_oidn_path")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_oidn_verbose")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_oidn_threads")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_oidn_maxmem")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_oidn_affinity")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_denoise_ao")
        else:
            row.prop(sceneProperties, "tlm_optix_path")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_optix_verbose")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_optix_maxmem")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_denoise_ao")

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
        self.layout.prop(sceneProperties, "tlm_filtering_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        sceneProperties = scene.TLM_SceneProperties

        column = layout.column()
        box = column.box()

        try:
            import cv2
            module_opencv = True
        except ImportError:
            #pip 
            module_opencv = False

        if module_opencv:
            box.label(text="OpenCV Installed", icon="INFO")
        else:
            if self._module_installed:
                box.label(text="Please restart Blender after installing")
            else:
                box.label(text="Please install as administrator")
                box.operator("tlm.install_opencv_lightmaps", icon="PREFERENCES")

        if(sceneProperties.tlm_filtering_use):
            if(module_opencv):
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

        row = layout.row(align=True)
        row.prop(scene.TLM_SceneProperties, "tlm_filtering_mode")
        row = layout.row(align=True)
        if scene.TLM_SceneProperties.tlm_filtering_mode == "Gaussian":
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_gaussian_strength")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_iterations")
        elif scene.TLM_SceneProperties.tlm_filtering_mode == "Box":
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_box_strength")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_iterations")

        elif scene.TLM_SceneProperties.tlm_filtering_mode == "Bilateral":
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_bilateral_diameter")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_bilateral_color_deviation")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_bilateral_coordinate_deviation")
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_iterations")
        else:
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_median_kernel", expand=True)
            row = layout.row(align=True)
            row.prop(scene.TLM_SceneProperties, "tlm_filtering_iterations")

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
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_encoding_mode", expand=True)
        if sceneProperties.tlm_encoding_mode == "RGBM" or sceneProperties.tlm_encoding_mode == "RGBD":
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_encoding_range")
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_encoding_armory_setup")
        if sceneProperties.tlm_encoding_mode == "LogLuv":
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_encoding_armory_setup")
        if sceneProperties.tlm_encoding_mode == "RGBE":
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_format")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_encoding_colorspace")

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
        if sceneProperties.tlm_encoding_mode == "RGBE":

            if sceneProperties.tlm_format == "HDR":
                layout.label(text="HDR compression not available for RGBE encoding")
            else:
                row = layout.row(align=True)
                row.prop(sceneProperties, "tlm_exr_codec")
                #layout.label(text="EXR Compression not yet available.")
        else:
            row = layout.row(align=True)
            row.prop(sceneProperties, "tlm_compression")

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

        row = layout.row(align=True)
        row.operator("tlm.enable_selection")
        row = layout.row(align=True)
        row.operator("tlm.disable_selection")
        row = layout.row(align=True)
        row.prop(sceneProperties, "tlm_override_object_settings")

        if sceneProperties.tlm_override_object_settings:

            row = layout.row(align=True)
            #row = layout.row()
            #row.prop(obj, "tlm_mesh_apply_after")
            #row = layout.row()
            #row.prop(obj, "tlm_mesh_emissive")
            #row = layout.row()
            #row.prop(obj, "tlm_mesh_emissive_shadow")
            row = layout.row()
            row.prop(sceneProperties, "tlm_mesh_lightmap_unwrap_mode")
            row = layout.row()

            if sceneProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup":

                if scene.TLM_AtlasList_index >= 0 and len(scene.TLM_AtlasList) > 0:
                    row = layout.row()
                    item = scene.TLM_AtlasList[scene.TLM_AtlasList_index]
                    row.prop_search(sceneProperties, "tlm_atlas_pointer", scene, "TLM_AtlasList", text='Atlas Group')
                else:
                    row = layout.label(text="Add Atlas Groups from the scene lightmapping settings.")

            else:

                row.prop(sceneProperties, "tlm_mesh_lightmap_resolution")
                row = layout.row()
                        #ADD ERROR CHECKING HERE! (ELSE)

                row = layout.row()
                row.prop(sceneProperties, "tlm_mesh_unwrap_margin")
                row = layout.row()
                row.prop(sceneProperties, "tlm_mesh_bake_ao")






            # row.prop(sceneProperties, "tlm_mesh_lightmap_resolution")
            # row = layout.row()
            # row.prop(sceneProperties, "tlm_mesh_lightmap_unwrap_mode")
            # row = layout.row()
            # row.prop(sceneProperties, "tlm_mesh_unwrap_margin")
            # row = layout.row()
            # row.prop(sceneProperties, "tlm_mesh_bake_ao")

        row = layout.row(align=True)
        row.operator("tlm.remove_uv_selection")
        row = layout.row(align=True)

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
        layout.label(text="Atlas Groups")

        rows = 2
        if len(scene.TLM_AtlasList) > 1:
            rows = 4
        row = layout.row()
        row.template_list("TLM_UL_AtlasList", "The_List", scene, "TLM_AtlasList", scene, "TLM_AtlasList_index", rows=rows)
        col = row.column(align=True)
        col.operator("tlm_atlaslist.new_item", icon='ADD', text="")
        col.operator("tlm_atlaslist.delete_item", icon='REMOVE', text="")
        #col.menu("ARM_MT_BakeListSpecials", icon='DOWNARROW_HLT', text="")

        # if len(scene.TLM_AtlasList) > 1:
        #     col.separator()
        #     op = col.operator("arm_bakelist.move_item", icon='TRIA_UP', text="")
        #     op.direction = 'UP'
        #     op = col.operator("arm_bakelist.move_item", icon='TRIA_DOWN', text="")
        #     op.direction = 'DOWN'

        if scene.TLM_AtlasList_index >= 0 and len(scene.TLM_AtlasList) > 0:
            item = scene.TLM_AtlasList[scene.TLM_AtlasList_index]
            #layout.prop_search(item, "obj", bpy.data, "objects", text="Object")
            #layout.prop(item, "res_x")
            layout.prop(item, "tlm_atlas_lightmap_unwrap_mode")
            layout.prop(item, "tlm_atlas_lightmap_resolution")
            layout.prop(item, "tlm_atlas_unwrap_margin")

            amount = 0

            for obj in bpy.data.objects:
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup":
                        if obj.TLM_ObjectProperties.tlm_atlas_pointer == item.name:
                            amount = amount + 1

            layout.label(text="Objects: " + str(amount))
        
        # layout.use_property_split = True
        # layout.use_property_decorate = False
        # layout.label(text="Enable for selection")
        # layout.label(text="Disable for selection")
        # layout.label(text="Something...")