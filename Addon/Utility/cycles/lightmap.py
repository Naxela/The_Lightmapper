import bpy, os

def bake():



    for obj in bpy.data.objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(False)

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        scene = bpy.context.scene

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        obs = bpy.context.view_layer.objects
        active = obs.active
        obj.hide_render = False
        scene.render.bake.use_clear = False

        bpy.ops.object.bake(type='COMBINED')
        bpy.ops.object.select_all(action='DESELECT')

    for image in bpy.data.images:
        if image.name.endswith("_baked"):
            


            saveDir = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)
            bakemap_path = os.path.join(saveDir, image.name)
            filepath_ext = ".hdr"
            image.filepath_raw = bakemap_path + filepath_ext
            image.file_format = "HDR"
            print("Saving to: " + image.filepath_raw)
            image.save()

        # if image.is_dirty:
        #     print("Dirty: " + image.name)
        #     filepath, filepath_ext = os.path.splitext(image.filepath_raw)
        #     saveDir = os.path.abspath(bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)
        #     filepath_ext = ".hdr"
        #     image.filepath_raw = saveDir + "/" + image.name + "_baked" + filepath_ext
        #     image.save()