import bpy

def backup_material_copy(slot):
    material = slot.material
    dup = material.copy()
    dup.name = "." + material.name + "_Original"
    dup.use_fake_user = True

def backup_material_cache(slot, path):
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)

def backup_material_cache_restore(slot, path):
    print("Restore cache")

def backup_material_restore(slot):
    material = slot.material
    if "." + material.name + "_Original" in bpy.data.materials:
        original = bpy.data.materials["." + material.name + "_Original"]
        slot.material = original
        material.name = material.name
        original.name = original.name[1:-9]
        original.use_fake_user = False
        material.user_clear()
        bpy.data.materials.remove(material)
        #Reset number
    else:
        pass
        #Check if material has nodes with lightmap prefix