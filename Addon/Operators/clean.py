import bpy, os, shutil
from .. Utility import utility, matcache

class TLM_CleanLightmaps(bpy.types.Operator):
    """Cleans the lightmaps"""
    bl_idname = "tlm.clean_lightmaps"
    bl_label = "Clean Lightmaps"
    bl_description = "Clean Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = bpy.data.scenes[scene.name].cycles
        selection = []

        for obj in bpy.data.objects:
            if obj.select_get():
                selection.append(obj)

        if scene.TLM_SceneProperties.tlm_clean_option == "Selection":
            filepath = bpy.data.filepath
            dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)
            if os.path.isdir(dirpath):
                list = os.listdir(dirpath)
                for file in list:
                    for obj in selection:
                        if file.startswith(obj.name[:4]):
                            print(file)
                            if file.endswith(".pfm"):
                                os.remove(os.path.join(dirpath,file))
                            if file.endswith(".hdr"):
                                os.remove(os.path.join(dirpath,file))

            for obj in selection:
                for slot in obj.material_slots:
                    matcache.backup_material_restore(slot)

        elif scene.TLM_SceneProperties.tlm_clean_option == "Clean cache":
            filepath = bpy.data.filepath
            dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)
            if os.path.isdir(dirpath):
                list = os.listdir(dirpath)
                for file in list:
                    if file.endswith(".pfm"):
                        os.remove(os.path.join(dirpath,file))
                    if file.endswith("denoised.hdr"):
                        os.remove(os.path.join(dirpath,file))
                    if file.endswith("finalized.hdr"):
                        os.remove(os.path.join(dirpath,file))

            for image in bpy.data.images:
                if image.name.endswith("_baked"):
                    image.save()

        else: #Clean and Restore
            print("Clean and restore...")
            filepath = bpy.data.filepath
            dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)
            if os.path.isdir(dirpath):
                for file in os.listdir(dirpath):
                    os.remove(os.path.join(dirpath + "/" + file))

            for obj in bpy.data.objects:
                if obj.type == "MESH":
                    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                        for slot in obj.material_slots:
                            matcache.backup_material_restore(slot)

        for mat in bpy.data.materials:
            if mat.name.endswith('_Original'):
                bpy.data.materials.remove(mat, do_unlink=True)
            if mat.name.endswith('.temp'):
                bpy.data.materials.remove(mat, do_unlink=True)
            if mat.name.endswith('_temp'):
                bpy.data.materials.remove(mat, do_unlink=True)

        for mat in bpy.data.materials:
            mat.update_tag()

        return{'FINISHED'}