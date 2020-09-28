import bpy, cv2, os, sys, math, mathutils
import numpy as np
import matplotlib.pyplot as plt
from . rectpack import newPacker, PackingMode, PackingBin

def postpack():

    lightmap_directory = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)

    packedAtlas = {}

    #TODO - TEST WITH ONLY 1 ATLAS AT FIRST (1 Atlas for each, but only 1 bin (no overflow))
    #PackedAtlas = Packer
    #Each atlas has bins
    #Each bins has rects
    #Each rect corresponds to a pack_object

    packer = {}

    for atlas in bpy.context.scene.TLM_PostAtlasList: #For each atlas

        packer[atlas.name] = newPacker(PackingMode.Offline, PackingBin.BFF, rotation=False)

        scene = bpy.context.scene

        if scene.TLM_EngineProperties.tlm_setting_supersample == "2x":
            supersampling_scale = 2
        elif scene.TLM_EngineProperties.tlm_setting_supersample == "4x":
            supersampling_scale = 4
        else:
            supersampling_scale = 1

        atlas_resolution = int(int(atlas.tlm_atlas_lightmap_resolution) / int(scene.TLM_EngineProperties.tlm_resolution_scale) * int(supersampling_scale))

        packer[atlas.name].add_bin(atlas_resolution, atlas_resolution, 1)

        #AtlasList same name prevention?
        rect = []

        #For each object that targets the atlas
        for obj in bpy.data.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupB":
                    if obj.TLM_ObjectProperties.tlm_postatlas_pointer == atlas.name:

                        res = int(int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) / int(scene.TLM_EngineProperties.tlm_resolution_scale) * int(supersampling_scale))

                        rect.append((res, res, obj.name))

        for r in rect:
            packer[atlas.name].add_rect(*r)

        #Continue here...
        packedAtlas[atlas.name] = np.zeros((atlas_resolution,atlas_resolution, 3), dtype="float32")

        packer[atlas.name].pack()

        for idy, rect in enumerate(packer[atlas.name].rect_list()):

            aob = rect[5]

            src = cv2.imread(os.path.join(lightmap_directory, aob + "_baked.hdr"), cv2.IMREAD_ANYDEPTH)

            print("Obj name is: " + aob)

            x,y,w,h = rect[1],rect[2],rect[3],rect[4]

            packedAtlas[atlas.name][y:h+y, x:w+x] = src
            
            obj = bpy.data.objects[aob]

            for idx, layer in enumerate(obj.data.uv_layers):
                if layer.name == "UVMap_Lightmap":
                    obj.data.uv_layers.active_index = idx

                    print("UVLayer set to: " + str(obj.data.uv_layers.active_index))

            #S = mathutils.Vector.Diagonal((1, -1)) # scale matrix

            for uv_verts in obj.data.uv_layers.active.data:

                #SET UV LAYER TO 

                atlasRes = atlas_resolution
                texRes = rect[3]
                x,y,w,z = x,y,texRes,texRes
                
                ratio = atlasRes/texRes
                
                if x == 0:
                    x_offset = 0
                else:
                    x_offset = 1/(atlasRes/x)

                if y == 0:
                    y_offset = 0
                else:
                    y_offset = 1/(atlasRes/y)
                
                vertex_x = (uv_verts.uv[0] * 1/(ratio)) + x_offset
                vertex_y = (1 - ((uv_verts.uv[1] * 1/(ratio)) + y_offset))
                
                uv_verts.uv[0] = vertex_x
                uv_verts.uv[1] = vertex_y

            #Change the material for each material, slot
            for slot in obj.material_slots:
                nodetree = slot.material.node_tree

                for node in nodetree.nodes:

                    if node.name == "TLM_Lightmap":

                        node.image.filepath_raw = os.path.join(lightmap_directory, atlas.name + "_baked.hdr")

            #print(xxs)

        cv2.imwrite(os.path.join(lightmap_directory, atlas.name + "_baked.hdr"), packedAtlas[atlas.name])
