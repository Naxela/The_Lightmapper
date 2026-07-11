import bpy

PREVIEW_MAT_SUFFIX = '_LMPreview'

def iter_lightmap_objects(context=None):
    context = context or bpy.context
    for obj in context.scene.objects:
        if obj.type == 'MESH' and obj.name in context.view_layer.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                yield obj

def _original_backup_key(material_name):
    return "." + material_name + "_Original"

def preview_material_name(orig_name, obj_name):
    return orig_name + '_' + obj_name + PREVIEW_MAT_SUFFIX

def is_preview_material(mat):
    return mat and mat.name.endswith(PREVIEW_MAT_SUFFIX)

def backup_material_copy(slot):
    material = slot.material
    key = _original_backup_key(material.name)
    if key in bpy.data.materials:
        return
    dup = material.copy()
    dup.name = key
    dup.use_fake_user = True

def _find_material_source(orig_name):
    key = _original_backup_key(orig_name)
    mat = bpy.data.materials.get(key)
    if mat:
        return mat
    for candidate in bpy.data.materials:
        if candidate.name.startswith(key + "."):
            return candidate
    return bpy.data.materials.get(orig_name)

def backup_material_cache(slot, path):
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)

def backup_material_cache_restore(slot, path):
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("Restore cache")

def restore_original_slots(obj):
    if "TLM_PrevMatArray" not in obj:
        return False

    prevMatArray = obj["TLM_PrevMatArray"]
    if len(prevMatArray) < 1:
        return False

    restored = False
    for idx, slot in enumerate(obj.material_slots):
        try:
            originalMaterial = prevMatArray[idx]
        except IndexError:
            continue

        if not originalMaterial or slot.material is None:
            continue

        backup_key = _original_backup_key(originalMaterial)
        if originalMaterial in bpy.data.materials:
            slot.material = bpy.data.materials[originalMaterial]
            restored = True
        elif backup_key in bpy.data.materials:
            slot.material = bpy.data.materials[backup_key]
            slot.material.use_fake_user = False
            restored = True

    return restored

def backup_material_restore(obj):
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("Restoring material for: " + obj.name)
    return restore_original_slots(obj)

def use_preview_slots(obj):
    if "TLM_PrevMatArray" not in obj:
        return False

    preview_names = []
    for idx, slot in enumerate(obj.material_slots):
        try:
            orig_name = obj["TLM_PrevMatArray"][idx]
        except IndexError:
            preview_names.append("")
            continue

        if not orig_name:
            preview_names.append("")
            continue

        source = _find_material_source(orig_name)
        if not source:
            preview_names.append("")
            continue

        preview_mat = source.copy()
        preview_mat.name = preview_material_name(orig_name, obj.name)
        preview_names.append(preview_mat.name)
        slot.material = preview_mat

    obj["TLM_PreviewMatArray"] = preview_names
    return any(preview_names)

def assign_preview_slots(obj):
    if "TLM_PreviewMatArray" not in obj:
        return False

    assigned = False
    for idx, slot in enumerate(obj.material_slots):
        try:
            preview_name = obj["TLM_PreviewMatArray"][idx]
        except IndexError:
            continue

        if preview_name and preview_name in bpy.data.materials:
            slot.material = bpy.data.materials[preview_name]
            assigned = True

    return assigned

def backup_material_rename(obj):
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("Renaming material for: " + obj.name)

    if "TLM_PrevMatArray" not in obj:
        print("No Previous material array for: " + obj.name)
        return

    for slot in obj.material_slots:
        if slot.material is not None and slot.material.name.endswith("_Original"):
            slot.material.name = slot.material.name[1:-9]

    del obj["TLM_PrevMatArray"]
