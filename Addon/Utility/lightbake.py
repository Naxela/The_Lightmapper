import bpy

def bake_objects(scene):

    bakeMode = 0

    if bakeMode == 0:

        iterNum = 0
        currentIterNum = 0

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    iterNum = iterNum + 1

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                    obs = bpy.context.view_layer.objects
                    active = obs.active
                    obj.hide_render = False

                    if scene.TLM_SceneProperties.tlm_indirect_only:
                        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"INDIRECT"}, margin=scene.TLM_SceneProperties.tlm_dilation_margin)
                    else:
                        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=scene.TLM_SceneProperties.tlm_dilation_margin)

    else:

        for obj in bpy.data.objects:
            obj.select_set(False)

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    obj.select_set(True)
    
        bpy.ops.object.bake("INVOKE_SCREEN", type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=scene.TLM_SceneProperties.tlm_dilation_margin)

        #Todo remove
        x = 1

        while x < 5000:
            print("Waiting for baking...:" + str(x))
            x = x + 1