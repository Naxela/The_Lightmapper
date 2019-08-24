import bpy
from bpy.props import *

class TLM_CleanLightmaps(bpy.types.Operator):
    """Cleans the lightmaps"""
    bl_idname = "tlm.clean_lightmaps"
    bl_label = "Clean Lightmaps"
    bl_description = "Clean Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def backup_material_restore(self, slot):
        material = slot.material
        original = bpy.data.materials[material.name + "_Original"]
        slot.material = original
        material.name = material.name + "_temp"
        original.name = original.name[:-9]
        original.use_fake_user = False
        material.user_clear()
        bpy.data.materials.remove(material)

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.tlm_mesh_lightmap_use:
                    for slot in obj.material_slots:
                        self.backup_material_restore(slot)

        return {'FINISHED'}