import bpy, math, time, os

from . import cache
from .. utility import *

_TLM_DEBUG_REPORT_PATH = None
_TLM_DEBUG_LINES = []

def _tlm_debug_base_dir():
    if bpy.data.filepath:
        return os.path.dirname(bpy.data.filepath)
    return bpy.app.tempdir

def _tlm_debug_start():
    global _TLM_DEBUG_REPORT_PATH
    global _TLM_DEBUG_LINES

    base_dir = _tlm_debug_base_dir()
    _TLM_DEBUG_REPORT_PATH = os.path.join(base_dir, "tlm_debug_latest.txt")
    _TLM_DEBUG_LINES = []
    _tlm_debug_log("report=" + _TLM_DEBUG_REPORT_PATH)
    _tlm_debug_log("blend=" + (bpy.data.filepath if bpy.data.filepath else "<unsaved>"))

def _tlm_debug_log(message):
    global _TLM_DEBUG_REPORT_PATH
    global _TLM_DEBUG_LINES

    if _TLM_DEBUG_REPORT_PATH is None:
        base_dir = _tlm_debug_base_dir()
        _TLM_DEBUG_REPORT_PATH = os.path.join(base_dir, "tlm_debug_latest.txt")

    line = "TLM_DEBUG: " + message
    _TLM_DEBUG_LINES.append(line)
    print(line)

    try:
        os.makedirs(os.path.dirname(_TLM_DEBUG_REPORT_PATH), exist_ok=True)
        with open(_TLM_DEBUG_REPORT_PATH, "w", encoding="utf-8") as debug_file:
            debug_file.write("\n".join(_TLM_DEBUG_LINES))
            debug_file.write("\n")
    except Exception as e:
        print("TLM_DEBUG: failed to write debug report: " + str(e))

def assemble():

    configure_world()

    configure_lights()

    configure_meshes()

def init(self, prev_container):

    store_existing(prev_container)

    set_settings()

    configure_world()

    configure_lights()

    configure_meshes(self)
    # try:
    #     configure_meshes(self)
    # except Exception as e:

    #     print("An error occured during mesh configuration. See error below:")

    #     print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")

    #     if not bpy.context.scene.TLM_SceneProperties.tlm_verbose:
    #         print("Turn on verbose mode to get more detail.")

def configure_world():
    pass

def configure_lights():
    pass

def _target_uv_channel(obj):
    if not obj.TLM_ObjectProperties.tlm_use_default_channel:
        return obj.TLM_ObjectProperties.tlm_uv_channel
    return "UVMap_Lightmap"

def _ensure_single_user_lightmap_mesh(obj):
    if obj.type != 'MESH':
        return

    if obj.data.users > 1:
        old_name = obj.data.name
        obj.data = obj.data.copy()
        obj.data.name = obj.name + "_TLM_Mesh"
        print("TLM: Made single-user mesh copy for lightmap object " + obj.name + " (was sharing " + old_name + ")")

def _is_hidden_from_lightmap(obj):
    hidden = False

    if obj.hide_get():
        hidden = True
    if obj.hide_viewport:
        hidden = True
    if obj.hide_render:
        hidden = True

    for collection in obj.users_collection:
        if collection.hide_viewport:
            hidden = True
        if collection.hide_render:
            hidden = True
        try:
            if collection.name in bpy.context.scene.view_layers[0].layer_collection.children:
                if bpy.context.scene.view_layers[0].layer_collection.children[collection.name].hide_viewport:
                    hidden = True
        except:
            print("Error: Could not find collection: " + collection.name)

    return hidden

def _collect_atlas_objects(scene, atlasgroup):
    atlas_items = []
    atlas_names = [group.name for group in scene.TLM_AtlasList]

    for obj in scene.objects:
        if obj.type != 'MESH' or obj.name not in bpy.context.view_layer.objects:
            continue

        props = obj.TLM_ObjectProperties
        if not props.tlm_mesh_lightmap_use:
            continue

        if props.tlm_mesh_lightmap_unwrap_mode != "AtlasGroupA":
            continue

        if props.tlm_atlas_pointer == "":
            warning = "TLM Atlas warning: " + obj.name + " uses Atlas Group (Prepack) but has no atlas group assigned."
            print(warning)
            _tlm_debug_log(warning)
            continue

        if props.tlm_atlas_pointer not in atlas_names:
            warning = "TLM Atlas warning: " + obj.name + " points to missing atlas group '" + props.tlm_atlas_pointer + "'."
            print(warning)
            _tlm_debug_log(warning)
            continue

        if props.tlm_atlas_pointer != atlasgroup.name:
            continue

        if _is_hidden_from_lightmap(obj):
            continue

        atlas_items.append(obj)

    return atlas_items

def _snapshot_non_target_uvs(objects):
    snapshots = {}
    for obj in objects:
        if obj.type != 'MESH':
            continue

        target_uv = _target_uv_channel(obj)
        layer_snapshots = {}
        for layer in obj.data.uv_layers:
            if layer.name == target_uv:
                continue
            layer_snapshots[layer.name] = [(loop.uv.x, loop.uv.y) for loop in layer.data]

        if layer_snapshots:
            snapshots[obj.data.name] = (obj.data, obj.name, layer_snapshots)
    return snapshots

def _restore_uv_snapshots(snapshots):
    for mesh, obj_name, layer_snapshots in snapshots.values():
        for layer_name, coords in layer_snapshots.items():
            layer = mesh.uv_layers.get(layer_name)
            if layer is None:
                continue
            if len(layer.data) != len(coords):
                print("TLM: Skipping UV restore for " + obj_name + " / " + layer_name + " because topology changed.")
                continue
            for loop, coord in zip(layer.data, coords):
                loop.uv.x = coord[0]
                loop.uv.y = coord[1]
        mesh.update()

def _normalize_uv_layer_order(obj):
    target_uv = _target_uv_channel(obj)
    uv_layers = obj.data.uv_layers

    if target_uv not in uv_layers:
        return

    snapshots = {
        layer.name: [(loop.uv.x, loop.uv.y) for loop in layer.data]
        for layer in uv_layers
    }

    ordered_names = []
    if "UVMap" in snapshots and target_uv != "UVMap":
        ordered_names.append("UVMap")
    ordered_names.append(target_uv)
    for layer in uv_layers:
        if layer.name not in ordered_names:
            ordered_names.append(layer.name)

    if [layer.name for layer in uv_layers] == ordered_names:
        tlm_set_active_uv_layer_by_name(obj.data, target_uv)
        return

    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("TLM: Normalizing UV layer order for " + obj.name + " -> " + ", ".join(ordered_names))

    while len(uv_layers) > 0:
        uv_layers.remove(uv_layers[0])

    for layer_name in ordered_names:
        layer = uv_layers.new(name=layer_name)
        coords = snapshots.get(layer_name)
        if coords and len(coords) == len(layer.data):
            for loop, coord in zip(layer.data, coords):
                loop.uv.x = coord[0]
                loop.uv.y = coord[1]

    tlm_set_active_uv_layer_by_name(obj.data, target_uv)
    obj.data.update()

def _snapshot_target_uvs(objects):
    snapshots = {}
    for obj in objects:
        layer = obj.data.uv_layers.get(_target_uv_channel(obj))
        if layer is None:
            continue
        snapshots[obj.name] = [(loop.uv.x, loop.uv.y) for loop in layer.data]
    return snapshots

def _uv_bounds(obj):
    layer = obj.data.uv_layers.get(_target_uv_channel(obj))
    if layer is None or len(layer.data) == 0:
        return None
    xs = [loop.uv.x for loop in layer.data]
    ys = [loop.uv.y for loop in layer.data]
    return (min(xs), min(ys), max(xs), max(ys))

def _print_atlas_uv_diagnostics(atlas_name, objects, before_snapshots):
    print("TLM Atlas '" + atlas_name + "' UV diagnostics:")
    for obj in objects:
        layer = obj.data.uv_layers.get(_target_uv_channel(obj))
        if layer is None:
            print("  " + obj.name + ": missing target UV layer")
            continue

        before = before_snapshots.get(obj.name)
        after = [(loop.uv.x, loop.uv.y) for loop in layer.data]
        changed = before is None or before != after
        bounds = _uv_bounds(obj)
        if bounds:
            print("  " + obj.name + ": changed=" + str(changed) + ", bounds=(" + ", ".join([str(round(value, 4)) for value in bounds]) + ")")
        else:
            print("  " + obj.name + ": changed=" + str(changed) + ", bounds=none")

def _pack_selected_uv_islands(margin):
    bpy.ops.uv.select_all(action='SELECT')
    try:
        bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    except Exception as e:
        print("TLM: Atlas UV island packing failed: " + str(e))

def _layout_atlas_objects_grid(objects, margin):
    if not objects:
        return

    columns = math.ceil(math.sqrt(len(objects)))
    rows = math.ceil(len(objects) / columns)
    padding = min(max(margin, 0.0), 0.25)
    cell_width = 1.0 / columns
    cell_height = 1.0 / rows

    for index, obj in enumerate(objects):
        layer = obj.data.uv_layers.get(_target_uv_channel(obj))
        if layer is None or len(layer.data) == 0:
            continue

        xs = [loop.uv.x for loop in layer.data]
        ys = [loop.uv.y for loop in layer.data]
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)
        width = max_x - min_x
        height = max_y - min_y

        if width <= 0.0 or height <= 0.0:
            continue

        column = index % columns
        row = index // columns
        cell_min_x = column * cell_width
        cell_min_y = 1.0 - ((row + 1) * cell_height)
        usable_width = max(cell_width - (padding * 2.0), cell_width * 0.5)
        usable_height = max(cell_height - (padding * 2.0), cell_height * 0.5)
        scale = min(usable_width / width, usable_height / height)
        offset_x = cell_min_x + ((cell_width - (width * scale)) * 0.5)
        offset_y = cell_min_y + ((cell_height - (height * scale)) * 0.5)

        for loop in layer.data:
            loop.uv.x = ((loop.uv.x - min_x) * scale) + offset_x
            loop.uv.y = ((loop.uv.y - min_y) * scale) + offset_y

        obj.data.update()

def configure_meshes(self):

    _tlm_debug_start()

    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("Configuring meshes: Start")

    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("Configuring meshes: Material restore")
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                cache.backup_material_restore(obj)

    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("Configuring meshes: Material rename check")
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                cache.backup_material_rename(obj)

    for mat in bpy.data.materials:
        if mat.users < 1:
            bpy.data.materials.remove(mat)

    for mat in bpy.data.materials:
        if mat.name.startswith("."):
            if "_Original" in mat.name:
                bpy.data.materials.remove(mat)

    #for image in bpy.data.images:
    #    if image.name.endswith("_baked"):
    #        bpy.data.images.remove(image, do_unlink=True)

    iterNum = 0
    currentIterNum = 0

    scene = bpy.context.scene

    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print("Object: Setting UV, converting modifiers and prepare channels")

    #OBJECT: Set UV, CONVERT AND PREPARE
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:

            hidden = False

            #We check if the object is hidden
            if obj.hide_get():
                hidden = True
            if obj.hide_viewport:
                hidden = True
            if obj.hide_render:
                hidden = True

            #We check if the object's collection is hidden
            collections = obj.users_collection

            for collection in collections:

                if collection.hide_viewport:
                    hidden = True
                if collection.hide_render:
                    hidden = True
                    
                try:
                    if collection.name in bpy.context.scene.view_layers[0].layer_collection.children:
                        if bpy.context.scene.view_layers[0].layer_collection.children[collection.name].hide_viewport:
                            hidden = True
                except:
                    print("Error: Could not find collection: " + collection.name)


            #Additional check for zero poly meshes
            mesh = obj.data
            if (len(mesh.polygons)) < 1:
                print("Found an object with zero polygons. Skipping object: " + obj.name)
                obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = False

            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use and not hidden:
                
                print("Preparing: UV initiation for object: " + obj.name)

                _ensure_single_user_lightmap_mesh(obj)

                if len(obj.data.vertex_colors) < 1:
                    obj.data.vertex_colors.new(name="TLM")

                if scene.TLM_SceneProperties.tlm_reset_uv:

                    uv_layers = obj.data.uv_layers
                    uv_channel = "UVMap_Lightmap"
                    for uvlayer in uv_layers:
                        if uvlayer.name == uv_channel:
                            uv_layers.remove(uvlayer)

                if scene.TLM_SceneProperties.tlm_apply_on_unwrap:
                    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                        print("Applying transform to: " + obj.name)
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

                if scene.TLM_SceneProperties.tlm_apply_modifiers:
                    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                        print("Applying modifiers to: " + obj.name)
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                    bpy.ops.object.convert(target='MESH')

                for slot in obj.material_slots:
                    material = slot.material
                    skipIncompatibleMaterials(material)

                obj.hide_select = False #Remember to toggle this back
                for slot in obj.material_slots:
                    if "." + slot.name + '_Original' in bpy.data.materials:
                        if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                            print("The material: " + slot.name + " shifted to " + "." + slot.name + '_Original')
                        slot.material = bpy.data.materials["." + slot.name + '_Original']

    protected_scene_uvs = _snapshot_non_target_uvs([
        obj for obj in bpy.context.scene.objects
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use
    ])

    #ATLAS UV PROJECTING
    print("PREPARE: ATLAS")
    _tlm_debug_log("atlas_group_count=" + str(len(scene.TLM_AtlasList)))
    for atlasgroup in scene.TLM_AtlasList:

        print("Adding UV Projection for Atlas group: " + atlasgroup.name)

        atlas = atlasgroup.name
        atlas_items = _collect_atlas_objects(scene, atlasgroup)
        _tlm_debug_log("atlas=" + atlas + ", unwrap=" + atlasgroup.tlm_atlas_lightmap_unwrap_mode + ", resolution=" + atlasgroup.tlm_atlas_lightmap_resolution + ", members=" + str(len(atlas_items)) + ", member_names=[" + ", ".join([obj.name for obj in atlas_items]) + "]")

        bpy.ops.object.select_all(action='DESELECT')

        #Atlas: Set UV and prepare every explicit atlas member.
        for obj in atlas_items:
            uv_layers = obj.data.uv_layers
            uv_channel = _target_uv_channel(obj)

            if not uv_channel in uv_layers:
                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                    print("UV map created for object: " + obj.name)
                uv_layers.new(name=uv_channel)
                uv_layers.active_index = len(uv_layers) - 1
                tlm_set_active_uv_layer_by_name(obj.data, uv_channel)
            else:
                print("Existing UV map found for object: " + obj.name)
                tlm_set_active_uv_layer_by_name(obj.data, uv_channel)

            _normalize_uv_layer_order(obj)

        if not atlas_items:
            print("No objects found for Atlas group: " + atlas)
            _tlm_debug_log("atlas=" + atlas + " skipped: no objects found")
            continue

        bpy.ops.object.select_all(action='DESELECT')
        for obj in atlas_items:
            obj.select_set(True)

        print("TLM Atlas '" + atlas + "' contains " + str(len(atlas_items)) + " object(s).")

        atlas_uv_ready = True
        for atlas_obj in atlas_items:
            if not atlas_obj.TLM_ObjectProperties.tlm_use_default_channel:
                ch = atlas_obj.TLM_ObjectProperties.tlm_uv_channel
            else:
                ch = "UVMap_Lightmap"
            _normalize_uv_layer_order(atlas_obj)
            if not tlm_set_active_uv_layer_by_name(atlas_obj.data, ch):
                print("TLM Atlas: UV layer '" + ch + "' missing on " + atlas_obj.name)
                atlas_uv_ready = False
            elif tlm_active_uv_layer_name(atlas_obj.data) != ch:
                print("TLM Atlas: active UV sync failed on " + atlas_obj.name + " (expected '" + ch + "', active '" + str(tlm_active_uv_layer_name(atlas_obj.data)) + "')")
                atlas_uv_ready = False

        if not atlas_uv_ready:
            print("TLM Atlas skipped: target UV layer was not active for all atlas objects.")
            _tlm_debug_log("atlas=" + atlas + " skipped: target UV layer was not active for all atlas objects")
            continue

        bpy.context.view_layer.objects.active = atlas_items[0]
        protected_uvs = _snapshot_non_target_uvs(atlas_items)
        target_uvs_before = _snapshot_target_uvs(atlas_items)

        if atlasgroup.tlm_atlas_lightmap_unwrap_mode == "SmartProject":
            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                print("Atlasgroup Smart Project for: " + str(atlas_items))

            for obj in atlas_items:
                print("Applying Smart Project to: ")
                print(obj.name + ": Active UV: " + obj.data.uv_layers[obj.data.uv_layers.active_index].name)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            #API changes in 2.91 causes errors:
            if (2, 91, 0) > bpy.app.version:
                bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=atlasgroup.tlm_atlas_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=True)
            else:
                angle = math.radians(45.0)
                bpy.ops.uv.smart_project(angle_limit=angle, island_margin=atlasgroup.tlm_atlas_unwrap_margin, area_weight=1.0, correct_aspect=True, scale_to_bounds=True)
            _pack_selected_uv_islands(atlasgroup.tlm_atlas_unwrap_margin)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            print("Smart project done.")
        elif atlasgroup.tlm_atlas_lightmap_unwrap_mode == "Lightmap":

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=atlasgroup.tlm_atlas_unwrap_margin)
            _pack_selected_uv_islands(atlasgroup.tlm_atlas_unwrap_margin)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

        elif atlasgroup.tlm_atlas_lightmap_unwrap_mode in ["Xatlas", "XatlasPython"]:

            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                print("Using " + atlasgroup.tlm_atlas_lightmap_unwrap_mode + " on Atlas Group: " + atlas)

            bpy.ops.object.mode_set(mode='EDIT')

            xatlas_result = Unwrap_Lightmap_Group_Xatlas_2_headless_call(
                atlas_items[0],
                atlasgroup.tlm_atlas_lightmap_unwrap_mode == "XatlasPython",
                atlas_items
            )
            _tlm_debug_log("atlas=" + atlas + " xatlas result=" + str(xatlas_result))

            bpy.ops.object.mode_set(mode='OBJECT')

        else:
            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                print("Copied Existing UV Map for Atlas Group: " + atlas)

        if atlasgroup.tlm_atlas_lightmap_unwrap_mode != "Xatlas":
            _layout_atlas_objects_grid(atlas_items, atlasgroup.tlm_atlas_unwrap_margin)
        _print_atlas_uv_diagnostics(atlas, atlas_items, target_uvs_before)
        _restore_uv_snapshots(protected_uvs)

        if atlasgroup.tlm_use_uv_packer:
            bpy.ops.object.select_all(action='DESELECT')
            protected_uvs = _snapshot_non_target_uvs(atlas_items)
            for obj in atlas_items:
                obj.select_set(True)
                if not obj.TLM_ObjectProperties.tlm_use_default_channel:
                    ch = obj.TLM_ObjectProperties.tlm_uv_channel
                else:
                    ch = "UVMap_Lightmap"
                _normalize_uv_layer_order(obj)
                tlm_set_active_uv_layer_by_name(obj.data, ch)

            bpy.context.view_layer.objects.active = atlas_items[0]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')

            bpy.context.scene.UVPackerProps.uvp_padding = atlasgroup.tlm_uv_packer_padding
            bpy.context.scene.UVPackerProps.uvp_engine = atlasgroup.tlm_uv_packer_packing_engine

            pack_label = atlas_items[0].name if atlas_items else "atlas"
            print("!!!!!!!!!!!!!!!!!!!!! Using UV Packer on: " + pack_label)

            bpy.ops.uvpackeroperator.packbtn()

            # if bpy.context.scene.UVPackerProps.uvp_engine == "OP0":
            #     time.sleep(1)
            # else:
            #     time.sleep(2)
            time.sleep(2)

            #FIX THIS! MAKE A SEPARATE CALL. THIS IS A THREADED ASYNC

            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            _restore_uv_snapshots(protected_uvs)

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                iterNum = iterNum + 1

    #OBJECT UV PROJECTING
    print("PREPARE: OBJECTS")
    for obj in bpy.context.scene.objects:
        if obj.name in bpy.context.view_layer.objects: #Possible fix for view layer error
            if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:

                hidden = False

                #We check if the object is hidden
                if obj.hide_get():
                    hidden = True
                if obj.hide_viewport:
                    hidden = True
                if obj.hide_render:
                    hidden = True

                #We check if the object's collection is hidden
                collections = obj.users_collection

                for collection in collections:

                    if collection.hide_viewport:
                        hidden = True
                    if collection.hide_render:
                        hidden = True
                        
                    try:
                        if collection.name in bpy.context.scene.view_layers[0].layer_collection.children:
                            if bpy.context.scene.view_layers[0].layer_collection.children[collection.name].hide_viewport:
                                hidden = True
                    except:
                        print("Error: Could not find collection: " + collection.name)

                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use and not hidden:

                    objWasHidden = False

                    #For some reason, a Blender bug might prevent invisible objects from being smart projected
                    #We will turn the object temporarily visible
                    obj.hide_viewport = False
                    obj.hide_set(False)

                    currentIterNum = currentIterNum + 1

                    #Configure selection
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)

                    obs = bpy.context.view_layer.objects
                    active = obs.active

                    #Provide material if none exists
                    print("Preprocessing material for: " + obj.name)
                    preprocess_material(obj, scene)

                    #UV Layer management here
                    if not obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA":

                        print("Managing layer for Obj: " + obj.name)

                        uv_layers = obj.data.uv_layers

                        if not obj.TLM_ObjectProperties.tlm_use_default_channel:
                            uv_channel = obj.TLM_ObjectProperties.tlm_uv_channel
                        else:
                            uv_channel = "UVMap_Lightmap"

                        if not uv_channel in uv_layers:
                            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                print("UV map created for obj: " + obj.name)
                            uvmap = uv_layers.new(name=uv_channel)
                            uv_layers.active_index = len(uv_layers) - 1
                            tlm_set_active_uv_layer_by_name(obj.data, uv_channel)
                            _normalize_uv_layer_order(obj)
                            protected_uvs = _snapshot_non_target_uvs([obj])

                            #If lightmap
                            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Lightmap":
                                if tlm_active_uv_layer_name(obj.data) == uv_channel:
                                    bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin)
                                else:
                                    print("TLM: Lightmap Pack skipped on " + obj.name + " (expected active UV '" + uv_channel + "', got '" + str(tlm_active_uv_layer_name(obj.data)) + "')")
                            
                            #If smart project
                            elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "SmartProject":

                                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                    print("Smart Project B")
                                bpy.ops.object.select_all(action='DESELECT')
                                obj.select_set(True)
                                bpy.ops.object.mode_set(mode='EDIT')
                                bpy.ops.mesh.select_all(action='SELECT')
                                if not tlm_set_active_uv_layer_by_name(obj.data, uv_channel):
                                    print("TLM: Smart Project skipped on " + obj.name + ": UV layer '" + uv_channel + "' not found")
                                elif tlm_active_uv_layer_name(obj.data) != uv_channel:
                                    print("TLM: Smart Project skipped on " + obj.name + ": active UV is '" + str(tlm_active_uv_layer_name(obj.data)) + "', expected '" + uv_channel + "'")
                                else:
                                    #API changes in 2.91 causes errors:
                                    if (2, 91, 0) > bpy.app.version:
                                        bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=True)
                                    else:
                                        angle = math.radians(45.0)
                                        bpy.ops.uv.smart_project(angle_limit=angle, island_margin=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin, area_weight=1.0, correct_aspect=True, scale_to_bounds=True)

                                bpy.ops.mesh.select_all(action='DESELECT')
                                bpy.ops.object.mode_set(mode='OBJECT')
                            
                            elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode in ["Xatlas", "XatlasPython"]:
                                
                                Unwrap_Lightmap_Group_Xatlas_2_headless_call(
                                    obj,
                                    obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "XatlasPython"
                                )

                            elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA":

                                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                    print("ATLAS GROUP: " + obj.TLM_ObjectProperties.tlm_atlas_pointer)
                                
                            else: #if copy existing

                                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                    print("Copied Existing UV Map for object: " + obj.name)
                            _restore_uv_snapshots(protected_uvs)

                        if obj.TLM_ObjectProperties.tlm_use_uv_packer:
                            bpy.ops.object.select_all(action='DESELECT')
                            protected_uvs = _snapshot_non_target_uvs([obj])
                            obj.select_set(True)
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='SELECT')

                            bpy.context.scene.UVPackerProps.uvp_padding = obj.TLM_ObjectProperties.tlm_uv_packer_padding
                            bpy.context.scene.UVPackerProps.uvp_engine = obj.TLM_ObjectProperties.tlm_uv_packer_packing_engine

                            #print(x)

                            print("!!!!!!!!!!!!!!!!!!!!! Using UV Packer on: " + obj.name)

                            if not tlm_set_active_uv_layer_by_name(obj.data, uv_channel):
                                print("TLM UV Packer skipped: layer '" + uv_channel + "' not on " + obj.name)
                            elif tlm_active_uv_layer_name(obj.data) != uv_channel:
                                print("TLM UV Packer skipped on " + obj.name + ": active UV is '" + str(tlm_active_uv_layer_name(obj.data)) + "', expected '" + uv_channel + "'")
                            else:
                                bpy.ops.uvpackeroperator.packbtn()

                            if bpy.context.scene.UVPackerProps.uvp_engine == "OP0":
                                time.sleep(1)
                            else:
                                time.sleep(2)

                            #FIX THIS! MAKE A SEPARATE CALL. THIS IS A THREADED ASYNC

                            bpy.ops.mesh.select_all(action='DESELECT')
                            bpy.ops.object.mode_set(mode='OBJECT')
                            _restore_uv_snapshots(protected_uvs)

                            #print(x)

                        else:
                            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                print("Existing UV map found for obj: " + obj.name)
                            for i in range(0, len(uv_layers)):
                                if uv_layers[i].name == uv_channel:
                                    uv_layers.active_index = i
                                    break
                            _normalize_uv_layer_order(obj)

                    #print(x)

                    #Sort out nodes
                    for slot in obj.material_slots:

                        nodetree = slot.material.node_tree

                        outputNode = nodetree.nodes[0] #Presumed to be material output node

                        if(outputNode.type != "OUTPUT_MATERIAL"):
                            for node in nodetree.nodes:
                                if node.type == "OUTPUT_MATERIAL":
                                    outputNode = node
                                    break

                        mainNode = outputNode.inputs[0].links[0].from_node

                        if mainNode.type not in ['BSDF_PRINCIPLED','BSDF_DIFFUSE','GROUP']:

                            #TODO! FIND THE PRINCIPLED PBR
                            #self.report({'INFO'}, "The primary material node is not supported. Seeking first principled.")
                            print("The primary material node is not supported. Seeking first principled.")

                            if len(find_node_by_type(nodetree.nodes, Node_Types.pbr_node)) > 0: 
                                mainNode = find_node_by_type(nodetree.nodes, Node_Types.pbr_node)[0]
                            else:
                                #self.report({'INFO'}, "No principled found. Seeking diffuse")
                                print("No principled found. Seeking diffuse.")
                                if len(find_node_by_type(nodetree.nodes, Node_Types.diffuse)) > 0: 
                                    mainNode = find_node_by_type(nodetree.nodes, Node_Types.diffuse)[0]
                                else:
                                    print("No supported nodes. Continuing anyway")
                                    print("Unsupported node was: " + node.type)
                                    #self.report({'INFO'}, "No supported nodes. Continuing anyway.")

                        if mainNode.type == 'GROUP':
                            if mainNode.node_tree != "Armory PBR":
                                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                    print("The material group is not supported!")

                        if (mainNode.type == "ShaderNodeMixRGB"):
                            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                print("Mix shader found")

                            #Skip for now
                            slot.material.TLM_ignore = True

                        if (mainNode.type == "BSDF_PRINCIPLED"):
                            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                print("BSDF_Principled")
                            if scene.TLM_EngineProperties.tlm_directional_mode == "None":
                                if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                    print("Directional mode")
                                if not len(mainNode.inputs[22].links) == 0:
                                    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                        print("NOT LEN 0")
                                    ninput = mainNode.inputs[22].links[0]
                                    noutput = mainNode.inputs[22].links[0].from_node
                                    nodetree.links.remove(noutput.outputs[0].links[0])

                            #Clamp metallic
                            if bpy.context.scene.TLM_SceneProperties.tlm_metallic_clamp == "limit":

                                MainMetNodeSocket = mainNode.inputs.get("Metallic")
                                if not len(MainMetNodeSocket.links) == 0:

                                    print("Creating new clamp node")

                                    nodes = nodetree.nodes
                                    MetClampNode = nodes.new('ShaderNodeClamp')
                                    MetClampNode.location = (-200,150)
                                    MetClampNode.inputs[2].default_value = 0.9
                                    minput = mainNode.inputs.get("Metallic").links[0] #Metal input socket
                                    moutput = mainNode.inputs.get("Metallic").links[0].from_socket #Output socket
                                    
                                    nodetree.links.remove(minput)

                                    nodetree.links.new(moutput, MetClampNode.inputs[0]) #minput node to clamp node
                                    nodetree.links.new(MetClampNode.outputs[0], MainMetNodeSocket) #clamp node to metinput

                                elif mainNode.type == "PRINCIPLED_BSDF" and MainMetNodeSocket.links[0].from_node.type == "CLAMP":

                                    pass

                                else:

                                    print("New clamp node NOT made")

                                    if mainNode.inputs[4].default_value > 0.9:
                                        mainNode.inputs[4].default_value = 0.9

                            elif bpy.context.scene.TLM_SceneProperties.tlm_metallic_clamp == "zero":

                                MainMetNodeSocket = mainNode.inputs[4]
                                if not len(MainMetNodeSocket.links) == 0:
                                    nodes = nodetree.nodes
                                    MetClampNode = nodes.new('ShaderNodeClamp')
                                    MetClampNode.location = (-200,150)
                                    MetClampNode.inputs[2].default_value = 0.0
                                    minput = mainNode.inputs[4].links[0] #Metal input socket
                                    moutput = mainNode.inputs[4].links[0].from_socket #Output socket

                                    nodetree.links.remove(minput)

                                    nodetree.links.new(moutput, MetClampNode.inputs[0]) #minput node to clamp node
                                    nodetree.links.new(MetClampNode.outputs[0], MainMetNodeSocket) #clamp node to metinput
                                else:
                                    mainNode.inputs[4].default_value = 0.0

                            else: #Skip
                                pass

                        if (mainNode.type == "BSDF_DIFFUSE"):
                            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                                print("BSDF_Diffuse")

                        # if (mainNode.type == "BSDF_DIFFUSE"):
                        #     if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                        #         print("BSDF_Diffuse")

                    #TODO FIX THIS PART!
                    #THIS IS USED IN CASES WHERE FOR SOME REASON THE USER FORGETS TO CONNECT SOMETHING INTO THE OUTPUT MATERIAL
                    for slot in obj.material_slots:

                        nodetree = bpy.data.materials[slot.name].node_tree
                        nodes = nodetree.nodes

                        #First search to get the first output material type
                        for node in nodetree.nodes:
                            if node.type == "OUTPUT_MATERIAL":
                                mainNode = node
                                break

                        #Fallback to get search
                        if not mainNode.type == "OUTPUT_MATERIAL":
                            mainNode = nodetree.nodes.get("Material Output")

                        #Last resort to first node in list
                        if not mainNode.type == "OUTPUT_MATERIAL":
                            mainNode = nodetree.nodes[0].inputs[0].links[0].from_node

                    #     for node in nodes:
                    #         if "LM" in node.name:
                    #             nodetree.links.new(node.outputs[0], mainNode.inputs[0])

                    #     for node in nodes:
                    #         if "Lightmap" in node.name:
                    #                 nodes.remove(node)

    _restore_uv_snapshots(protected_scene_uvs)

def preprocess_material(obj, scene):
    if len(obj.material_slots) == 0:
        single = False
        number = 0
        while single == False:
            matname = obj.name + ".00" + str(number)
            if matname in bpy.data.materials:
                single = False
                number = number + 1
            else:
                mat = bpy.data.materials.new(name=matname)
                mat.use_nodes = True
                obj.data.materials.append(mat)
                single = True

    #We copy the existing material slots to an ordered array, which corresponds to the slot index
    matArray = []
    for slot in obj.material_slots:
        matArray.append(slot.name)
    
    obj["TLM_PrevMatArray"] = matArray

    #We check and safeguard against NoneType
    for slot in obj.material_slots:
        if slot.material is None:
            matName = obj.name + ".00" + str(0)
            bpy.data.materials.new(name=matName)
            slot.material = bpy.data.materials[matName]
            slot.material.use_nodes = True

    for slot in obj.material_slots:

        cache.backup_material_copy(slot)

        mat = slot.material
        if mat.users > 1:
                copymat = mat.copy()
                slot.material = copymat

    #SOME ATLAS EXCLUSION HERE?
    ob = obj
    for slot in ob.material_slots:
        #If temporary material already exists
        if slot.material.name.endswith('_temp'):
            continue
        n = slot.material.name + '_' + ob.name + '_temp'
        if not n in bpy.data.materials:
            slot.material = slot.material.copy()
        slot.material.name = n

    #Add images for baking
    img_name = obj.name + '_baked'
    #Resolution is object lightmap resolution divided by global scaler

    if scene.TLM_EngineProperties.tlm_setting_supersample == "2x":
        supersampling_scale = 2
    elif scene.TLM_EngineProperties.tlm_setting_supersample == "4x":
        supersampling_scale = 4
    else:
        supersampling_scale = 1


    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA" and obj.TLM_ObjectProperties.tlm_atlas_pointer == "":
        print("TLM Atlas warning: " + obj.name + " is Atlas Group (Prepack) but has no atlas group assigned; material preprocessing skipped.")
        return

    if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA" and obj.TLM_ObjectProperties.tlm_atlas_pointer not in scene.TLM_AtlasList:
        print("TLM Atlas warning: " + obj.name + " points to missing atlas group '" + obj.TLM_ObjectProperties.tlm_atlas_pointer + "'; material preprocessing skipped.")
        return

    if (obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA" and obj.TLM_ObjectProperties.tlm_atlas_pointer != ""):

        atlas_image_name = obj.TLM_ObjectProperties.tlm_atlas_pointer + "_baked"

        res = int(scene.TLM_AtlasList[obj.TLM_ObjectProperties.tlm_atlas_pointer].tlm_atlas_lightmap_resolution) / int(scene.TLM_EngineProperties.tlm_resolution_scale) * int(supersampling_scale)

        #If image not in bpy.data.images or if size changed, make a new image
        if atlas_image_name not in bpy.data.images or bpy.data.images[atlas_image_name].size[0] != res or bpy.data.images[atlas_image_name].size[1] != res:
            if atlas_image_name in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[atlas_image_name], do_unlink=True)
            img = bpy.data.images.new(atlas_image_name, int(res), int(res), alpha=True, float_buffer=True)

            num_pixels = len(img.pixels)
            result_pixel = list(img.pixels)

            for i in range(0,num_pixels,4):

                if scene.TLM_SceneProperties.tlm_override_bg_color:
                    print("Override Background Color")
                    result_pixel[i+0] = scene.TLM_SceneProperties.tlm_override_color[0]
                    result_pixel[i+1] = scene.TLM_SceneProperties.tlm_override_color[1]
                    result_pixel[i+2] = scene.TLM_SceneProperties.tlm_override_color[2]
                else:
                    result_pixel[i+0] = 0.0
                    result_pixel[i+1] = 0.0
                    result_pixel[i+2] = 0.0
                    result_pixel[i+3] = 1.0

            img.pixels = result_pixel

        else:
            img = bpy.data.images[atlas_image_name]

        for slot in obj.material_slots:
            mat = slot.material
            mat.use_nodes = True
            nodes = mat.node_tree.nodes

            if "Baked Image" in nodes:
                img_node = nodes["Baked Image"]
                img_node.image = img
            else:
                img_node = nodes.new('ShaderNodeTexImage')
                img_node.name = 'Baked Image'
                img_node.location = (100, 100)
                img_node.image = img
            img_node.select = True
            nodes.active = img_node

        #We need to save this file first in Blender 3.3 due to new filmic option?
        image = img
        #image.colorspace_settings.name = 'Raw'
        saveDir = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)
        bakemap_path = os.path.join(saveDir, image.name)
        filepath_ext = ".hdr"
        image.filepath_raw = bakemap_path + filepath_ext
        image.file_format = "HDR"
        if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
            print("Saving to: " + image.filepath_raw)
        image.save()

    else:

        res = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) / int(scene.TLM_EngineProperties.tlm_resolution_scale) * int(supersampling_scale)

        #If image not in bpy.data.images or if size changed, make a new image
        if img_name not in bpy.data.images or bpy.data.images[img_name].size[0] != res or bpy.data.images[img_name].size[1] != res:
            if img_name in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[img_name], do_unlink=True)
            img = bpy.data.images.new(img_name, int(res), int(res), alpha=True, float_buffer=True)

            num_pixels = len(img.pixels)
            result_pixel = list(img.pixels)

            if scene.TLM_SceneProperties.tlm_override_bg_color:
                print("Override Background Color")

            for i in range(0,num_pixels,4):
                if scene.TLM_SceneProperties.tlm_override_bg_color:
                    result_pixel[i+0] = scene.TLM_SceneProperties.tlm_override_color[0]
                    result_pixel[i+1] = scene.TLM_SceneProperties.tlm_override_color[1]
                    result_pixel[i+2] = scene.TLM_SceneProperties.tlm_override_color[2]
                    result_pixel[i+3] = 1.0
                else:
                    result_pixel[i+0] = 0.0
                    result_pixel[i+1] = 0.0
                    result_pixel[i+2] = 0.0
                    result_pixel[i+3] = 1.0

            img.pixels = result_pixel

        else:
            img = bpy.data.images[img_name]

        for slot in obj.material_slots:
            mat = slot.material
            mat.use_nodes = True
            nodes = mat.node_tree.nodes

            if "Baked Image" in nodes:
                img_node = nodes["Baked Image"]
                img_node.image = img
            else:
                img_node = nodes.new('ShaderNodeTexImage')
                img_node.name = 'Baked Image'
                img_node.location = (100, 100)
                img_node.image = img
            img_node.select = True
            nodes.active = img_node

        #We need to save this file first in Blender 3.3 due to new filmic option?
        image = img
        #image.colorspace_settings.name = 'Raw'
        saveDir = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)
        bakemap_path = os.path.join(saveDir, image.name)
        filepath_ext = ".hdr"
        image.filepath_raw = bakemap_path + filepath_ext
        image.file_format = "HDR"
        if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
            print("Saving to: " + image.filepath_raw)
        image.save()

def set_settings():

    scene = bpy.context.scene
    cycles = scene.cycles
    scene.render.engine = "CYCLES"
    sceneProperties = scene.TLM_SceneProperties
    engineProperties = scene.TLM_EngineProperties
    cycles.device = scene.TLM_EngineProperties.tlm_mode
    
    print(bpy.app.version)

    if bpy.app.version[0] == 3 or bpy.app.version[0] == 4 or bpy.app.version[0] == 5:
        if cycles.device == "GPU":
            scene.cycles.tile_size = 256
        else:
            scene.cycles.tile_size = 32
    else:    
        if cycles.device == "GPU":
            scene.render.tile_x = 256
            scene.render.tile_y = 256
        else:
            scene.render.tile_x = 32
            scene.render.tile_y = 32
    
    if engineProperties.tlm_quality == "0":
        cycles.samples = 32
        cycles.max_bounces = 1
        cycles.diffuse_bounces = 1
        cycles.glossy_bounces = 1
        cycles.transparent_max_bounces = 1
        cycles.transmission_bounces = 1
        cycles.volume_bounces = 1
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "1":
        cycles.samples = 64
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "2":
        cycles.samples = 512
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "3":
        cycles.samples = 1024
        cycles.max_bounces = 256
        cycles.diffuse_bounces = 256
        cycles.glossy_bounces = 256
        cycles.transparent_max_bounces = 256
        cycles.transmission_bounces = 256
        cycles.volume_bounces = 256
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "4":
        cycles.samples = 2048
        cycles.max_bounces = 512
        cycles.diffuse_bounces = 512
        cycles.glossy_bounces = 512
        cycles.transparent_max_bounces = 512
        cycles.transmission_bounces = 512
        cycles.volume_bounces = 512
        cycles.caustics_reflective = True
        cycles.caustics_refractive = True
    else: #Custom
        pass

def store_existing(prev_container):

    scene = bpy.context.scene
    cycles = scene.cycles

    selected = []

    for obj in bpy.context.scene.objects:
        if obj.select_get():
            selected.append(obj.name)

    prev_container["settings"] = [
        cycles.samples,
        cycles.max_bounces,
        cycles.diffuse_bounces,
        cycles.glossy_bounces,
        cycles.transparent_max_bounces,
        cycles.transmission_bounces,
        cycles.volume_bounces,
        cycles.caustics_reflective,
        cycles.caustics_refractive,
        cycles.device,
        scene.render.engine,
        bpy.context.view_layer.objects.active,
        selected,
        [scene.render.resolution_x, scene.render.resolution_y]
    ]

def skipIncompatibleMaterials(material):
    node_tree = material.node_tree
    nodes = material.node_tree.nodes

    #ADD OR MIX SHADER? CUSTOM/GROUP?
    #IF Principled has emissive or transparency?

    SkipMatList = ["EMISSION",
                    "BSDF_TRANSPARENT",
                    "BACKGROUND", 
                    "BSDF_HAIR",
                    "BSDF_HAIR_PRINCIPLED",
                    "HOLDOUT",
                    "PRINCIPLED_VOLUME",
                    "BSDF_REFRACTION",
                    "EEVEE_SPECULAR",
                    "BSDF_TRANSLUCENT",
                    "VOLUME_ABSORPTION",
                    "VOLUME_SCATTER"]

    #Find output node
    outputNode = nodes[0]
    if(outputNode.type != "OUTPUT_MATERIAL"):
        for node in node_tree.nodes:
            if node.type == "OUTPUT_MATERIAL":
                outputNode = node
                break

    #Find mainnode
    mainNode = outputNode.inputs[0].links[0].from_node

    if mainNode.type in SkipMatList:
        material.TLM_ignore = True
        print("Ignored material: " + material.name)

def packUVPack():



    pass
