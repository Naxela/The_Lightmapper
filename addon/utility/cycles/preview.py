import bpy
from . import cache, nodes


def refresh_preview(scene=None, background_pass=False):
    scene = scene or bpy.context.scene
    nodes.apply_preview_materials()
    if not background_pass:
        end, formatEnc = nodes.get_lightmap_output_suffix(scene)
        nodes.exchangeLightmapsToPostfix("_baked", end, formatEnc)
    nodes.set_active_lightmap_uv_layers()


def restore_original_view(context=None):
    for obj in cache.iter_lightmap_objects(context):
        cache.restore_original_slots(obj)
    nodes.set_active_texture_uv_layers(context)


def finish_bake(background_pass=False):
    scene = bpy.context.scene
    prepared = 0

    for obj in cache.iter_lightmap_objects():
        if cache.use_preview_slots(obj):
            prepared += 1
        elif bpy.context.scene.TLM_SceneProperties.tlm_verbose:
            print(f"TLM: preview skipped for '{obj.name}'")

    if not prepared:
        print("TLM: finish_bake aborted — no preview materials created")
        return

    refresh_preview(scene, background_pass)

    restore_original_view()

    scene.TLM_SceneProperties.tlm_lightmap_preview = False


def toggle(context=None):
    context = context or bpy.context
    scene = context.scene
    props = scene.TLM_SceneProperties
    enable = not props.tlm_lightmap_preview

    if enable:
        any_assigned = False
        for obj in cache.iter_lightmap_objects(context):
            if cache.assign_preview_slots(obj):
                any_assigned = True

        if not any_assigned:
            missing = [obj.name for obj in cache.iter_lightmap_objects(context) if "TLM_PreviewMatArray" not in obj]
            if missing:
                return False, f"No preview for: {', '.join(missing)}. Run Build Lightmaps first."
            return False, "No lightmapped objects with preview. Enable lightmaps and build first."

        refresh_preview(scene)
    else:
        restore_original_view(context)

    props.tlm_lightmap_preview = enable
    return True, None
