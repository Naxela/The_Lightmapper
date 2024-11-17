import bpy, math


def prepareLightmapChannel(obj, setActive):
    
    pass

def unwrapObjectOnChannel(obj):

    print("Unwrapping object A: " + obj.name)

    if len(obj.data.vertex_colors) < 1:
        obj.data.vertex_colors.new(name="TLM")

    # if scene.TLM_SceneProperties.tlm_reset_uv:
    #     uv_layers = obj.data.uv_layers
    #     uv_channel = "UVMap_Lightmap"
    #     for uvlayer in uv_layers:
    #         if uvlayer.name == uv_channel:
    #             uv_layers.remove(uvlayer)
        
    if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:

        print("Unwrapping object B: " + obj.name)

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

            print("Unwrapping object C: " + obj.name)

            objWasHidden = False

            #For some reason, a Blender bug might prevent invisible objects from being smart projected
            #We will turn the object temporarily visible
            obj.hide_viewport = False
            obj.hide_set(False)

            #Configure selection
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            obs = bpy.context.view_layer.objects
            active = obs.active
            #Provide material if none exists

            existing_lightmap_uv = False

            mesh = obj.data
            
            if not "UVMap-Lightmap" in mesh.uv_layers:
                
                mesh.uv_layers.new(name="UVMap-Lightmap")

            else:

                existing_lightmap_uv = True

            

            #If a lightmap UV map already exists, we don't want to unwrap it
            if not existing_lightmap_uv:

                mesh.uv_layers.active = mesh.uv_layers["UVMap-Lightmap"]
                mesh.uv_layers["UVMap-Lightmap"].active_render = True

                #If lightmap
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Lightmap":

                    print("Lightmapping UV Map for object: " + obj.name)

                    bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin)
                
                #If smart project
                elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "SmartProject":

                    print("Smart Projecting UV Map for object: " + obj.name)

                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')

                    angle = math.radians(45.0)
                    bpy.ops.uv.smart_project(angle_limit=angle, island_margin=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin, area_weight=1.0, correct_aspect=True, scale_to_bounds=False)

                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    
                else: #if copy existing

                    print("Copied Existing UV Map for object: " + obj.name)

                mesh.uv_layers.active = mesh.uv_layers[0]
                mesh.uv_layers[0].active_render = True

def prepareObjectsForBaking():
    scene = bpy.context.scene
    obj_list = []
        
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                obj_list.append(obj.name)

    total = len(obj_list)
    for index, obj_name in enumerate(obj_list):
        obj = bpy.data.objects[obj_name]
        prepareLightmapChannel(obj, True)
        unwrapObjectOnChannel(obj)

    #if scene.TLM_SceneProperties.tlm_reset_uv:
    #    pass
        #todo

    if scene.TLM_SceneProperties.tlm_material_multi_user == "Unique":
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    for slot in obj.material_slots:
                        
                        mat = slot.material

                        #If the material has more users, make it unique
                        if mat.users > 1:

                            original_material = mat
                            # Duplicate the material
                            new_mat = mat.copy()

                            new_mat["TLM_InheritedMaterial"] = original_material
                            # Rename the new material with the object's name as suffix
                            new_mat.name = f"{mat.name}-{obj.name}"
                            # Assign the new, uniquely named material to the slot
                            slot.material = new_mat

    elif scene.TLM_SceneProperties.tlm_material_multi_user == "Shared":

        pass

    else:

        pass




    #Save the blend file
    bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath)