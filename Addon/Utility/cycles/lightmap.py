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
        if image.is_dirty:
            filepath, filepath_ext = os.path.splitext(image.filepath_raw)
            saveDir = "C:/Users/akg/Desktop/"
            filepath_ext = ".hdr"
            image.filepath_raw = saveDir + filepath + "_bake" + filepath_ext
            image.save()