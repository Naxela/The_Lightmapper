import bpy, os, shutil
from .. Utility import utility

class TLM_EnableSelection(bpy.types.Operator):
    """Enable for selection"""
    bl_idname = "tlm.enable_selection"
    bl_label = "Enable for selection"
    bl_description = "Enable for selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        for obj in bpy.context.selected_objects:
            obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = True

            if scene.TLM_SceneProperties.tlm_override_object_settings:
                obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = scene.TLM_SceneProperties.tlm_mesh_lightmap_resolution
                obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode = scene.TLM_SceneProperties.tlm_mesh_lightmap_unwrap_mode
                obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_margin = scene.TLM_SceneProperties.tlm_mesh_unwrap_margin
                obj.TLM_ObjectProperties.tlm_mesh_bake_ao = scene.TLM_SceneProperties.tlm_mesh_bake_ao

        return{'FINISHED'}

class TLM_DisableSelection(bpy.types.Operator):
    """Disable for selection"""
    bl_idname = "tlm.disable_selection"
    bl_label = "Disable for selection"
    bl_description = "Disable for selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        for obj in bpy.context.selected_objects:
            obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = False

        return{'FINISHED'}

class TLM_RemoveLightmapUV(bpy.types.Operator):
    """Remove Lightmap UV for selection"""
    bl_idname = "tlm.remove_uv_selection"
    bl_label = "Remove Lightmap UV"
    bl_description = "Remove Lightmap UV for selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                uv_layers = obj.data.uv_layers

                for uvlayer in uv_layers:
                    if uvlayer.name == "UVMap_Lightmap":
                        uv_layers.remove(uvlayer)

        return{'FINISHED'}