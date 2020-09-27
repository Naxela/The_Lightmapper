import bpy, cv2, os, sys, math
import numpy as np
import matplotlib.pyplot as plt
from rectpack import newPacker, PackingMode, PackingBin

def postpack():

    lightmap_directory = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)

    bins = []

    for atlas in bpy.context.scene.TLM_PostAtlasList:

        bin_size = atlas.tlm_postatlas_lightmap_resolution

        atlas_area = atlas.tlm_postatlas_lightmap_resolution ** 2

        atlas_used_area = 0

        pack_objects = []

        for obj in bpy.data.objects:
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupB":
                    if obj.TLM_ObjectProperties.tlm_atlas_pointer == atlas:

                        pack_objects.append((obj.name,obj.tlm_mesh_lightmap_resolution))

        for obj in pack_objects:

            area = obj[1] ** 2

            atlas_used_area = atlas_used_area + area

        atlasAmounts = math.ceil(usedArea / (atlasArea**2))

# for i in range(atlasAmounts):
    
#     Atlas.append((atlasResolution, atlasResolution, 1)) #For packer (Bin), along with rectangle
    
#     VS.append(np.zeros((1024,1024, 3), dtype="float32")) #For VS/Img, writes based on bins
#     VS[i][0:1024, 0:1024] = (255,0,0)
    
# packer = newPacker(PackingMode.Offline, PackingBin.BNF)

# # Add the rectangles to packing queue
# for object in atlasObjects:
#     #r = (object[1],object[1])
#     packer.add_rect(object[1],object[1],object[0])

# # Add the bins where the rectangles will be placed
# for b in Atlas:
#     packer.add_bin(*b)

# # Start packing
# packer.pack()


# #TODO? CHECK IF FILE EXISTS IN CASE OF COPY?

# for idx, bin in enumerate(packer):
#     print("Bin #" + str(idx) + " with size 1024") # Bin id if it has one
    
#     for idy, rect in enumerate(packer.rect_list()):
        
#         print(rect)
        
#         if rect[0] == idx: #If bin fits the rect
            
#             #res = [val[0] for idx, val in enumerate(atlasObjects) if atlasObjects[0] == rect[5]]
#             #for idx, val in enumerate(atlasObjects):
#             #    if val[0] == rect[5]:
#             #        res = idx
            
#             print(rect[5])
            
            
#             #AOB is AtlasObjects where idy is rid?
#             for obj in atlasObjects:
#                 if obj[0] == rect[5]:
#                     #print(obj[0])
#                     aob = obj[0]
            
#             #print(aob)
            
#             src = cv2.imread(os.path.join(lmdir, aob + "_baked.hdr"), cv2.IMREAD_ANYDEPTH)
            
#             x = rect[1]
#             y = rect[2]
#             w = rect[3]
#             h = rect[4]
            
#             VS[idx][y:h+y, x:w+x] = src
            
#             print(" ")
            
#             #print(atlasObjects[idy])
#             #src = os.path.join(lmdir, atlasObjects[idy][0] + "_baked.hdr")
#             #print(src)
            
            
#     cv2.imshow('Image', VS[idx])



