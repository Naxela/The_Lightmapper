import bpy, os
from . cycles import lightmap, prepare, nodes
from . denoiser import integrated
from os import listdir
from os.path import isfile, join

previous_settings = {}

def prepare_build(self=0):

    scene = bpy.context.scene
    sceneProperties = scene.TLM_SceneProperties

    #Timer start here bound to global

    if check_save():
        self.report({'INFO'}, "Please save your file first")
        return{'FINISHED'}

    if check_denoiser():
        self.report({'INFO'}, "No denoise OIDN path assigned")
        return{'FINISHED'}

    if check_materials():
        self.report({'INFO'}, "Error with material")
        return{'FINISHED'}

    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)

    #Naming check
    naming_check()

    ## RENDER DEPENDENCY FROM HERE

    if sceneProperties.tlm_lightmap_engine == "Cycles":

        prepare.init(previous_settings)

    if sceneProperties.tlm_lightmap_engine == "LuxCoreRender":

        pass

    if sceneProperties.tlm_lightmap_engine == "OctaneRender":

        pass

    #Renderer - Store settings

    #Renderer - Set settings

    #Renderer - Config objects, lights, world

    begin_build()

def begin_build():

    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)

    scene = bpy.context.scene
    sceneProperties = scene.TLM_SceneProperties

    if sceneProperties.tlm_lightmap_engine == "Cycles":

        #if cycles
        lightmap.bake()

    #Denoiser

    if sceneProperties.tlm_denoise_use:

        if sceneProperties.tlm_denoise_engine == "Integrated":

            baked_image_array = []

            dirfiles = [f for f in listdir(dirpath) if isfile(join(dirpath, f))]

            for file in dirfiles:
                if file.endswith("_baked.hdr"):
                    baked_image_array.append(file)

            print(baked_image_array)

            denoiser = integrated.TLM_Integrated_Denoise()

            denoiser.load(baked_image_array)

            denoiser.setOutputDir(dirpath)

            denoiser.cull_undefined()

            denoiser.setup()

            #denoiser.setOutputDir()

        elif sceneProperties.tlm_denoise_engine == "OIDN":
            pass
        else:
            pass

    #Filtering

    manage_build()

def manage_build():

    scene = bpy.context.scene
    sceneProperties = scene.TLM_SceneProperties

    if sceneProperties.tlm_lightmap_engine == "Cycles":

        nodes.apply_materials()

    if sceneProperties.tlm_lightmap_engine == "LuxCoreRender":

        pass

    if sceneProperties.tlm_lightmap_engine == "OctaneRender":

        pass

def naming_check():

    for obj in bpy.data.objects:

        if obj.type == "MESH":

            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                if "_" in obj.name:
                    obj.name = obj.name.replace("_",".")
                if " " in obj.name:
                    obj.name = obj.name.replace(" ",".")
                if "[" in obj.name:
                    obj.name = obj.name.replace("[",".")
                if "]" in obj.name:
                    obj.name = obj.name.replace("]",".")
                if "ø" in obj.name:
                    obj.name = obj.name.replace("ø","oe")
                if "æ" in obj.name:
                    obj.name = obj.name.replace("æ","ae")
                if "å" in obj.name:
                    obj.name = obj.name.replace("å","aa")

                for slot in obj.material_slots:
                    if "_" in slot.material.name:
                        slot.material.name = slot.material.name.replace("_",".")
                    if " " in slot.material.name:
                        slot.material.name = slot.material.name.replace(" ",".")
                    if "[" in slot.material.name:
                        slot.material.name = slot.material.name.replace("[",".")
                    if "[" in slot.material.name:
                        slot.material.name = slot.material.name.replace("]",".")
                    if "ø" in slot.material.name:
                        slot.material.name = slot.material.name.replace("ø","oe")
                    if "æ" in slot.material.name:
                        slot.material.name = slot.material.name.replace("æ","ae")
                    if "å" in slot.material.name:
                        slot.material.name = slot.material.name.replace("å","aa")

def check_save():
    if not bpy.data.is_saved:

        return 1

    else:

        return 0

def check_denoiser():

    scene = bpy.context.scene

    return 0

    #TODO FINISH DENOISE CHECK

    # if scene.TLM_SceneProperties.tlm_denoise_use:
    #     if scene.TLM_SceneProperties.tlm_oidn_path == "":
    #         print("NO DENOISE PATH")
    #         return False
    #     else:
    #         return True
    # else:
    #     return True

def check_materials():
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                for slot in obj.material_slots:
                    mat = slot.material

                    nodes = mat.node_tree.nodes

                    #TODO FINISH MATERIAL CHECK