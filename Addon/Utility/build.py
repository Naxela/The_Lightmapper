import bpy, os, importlib, subprocess, sys
from . cycles import lightmap, prepare, nodes
from . denoiser import integrated, oidn
from . filtering import opencv
from os import listdir
from os.path import isfile, join
from time import time

previous_settings = {}

def prepare_build(self=0, background_mode=False):

    if bpy.context.scene.TLM_EngineProperties.tlm_bake_mode == "Foreground" or background_mode==True:

        global start_time
        start_time = time()

        scene = bpy.context.scene
        sceneProperties = scene.TLM_SceneProperties

        #We dynamically load the renderer and denoiser, instead of loading something we don't use

        if sceneProperties.tlm_lightmap_engine == "Cycles":

            pass

        if sceneProperties.tlm_lightmap_engine == "LuxCoreRender":

            pass

        if sceneProperties.tlm_lightmap_engine == "OctaneRender":

            pass

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

    else:

        print("BG_CALL")

        filepath = bpy.data.filepath

        process = subprocess.call([sys.executable,
                                    "-b",
                                    filepath,
                                    "--python-expr",
                                    'import bpy; import thelightmapper; thelightmapper.addon.utility.build.prepare_build(0, True);'],
                                    shell=False)

        #bpy.ops.wm.revert_mainfile()

        #begin_build()

def begin_build():

    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.TLM_EngineProperties.tlm_lightmap_savedir)

    scene = bpy.context.scene
    sceneProperties = scene.TLM_SceneProperties

    if sceneProperties.tlm_lightmap_engine == "Cycles":

        lightmap.bake()

    if sceneProperties.tlm_lightmap_engine == "LuxCoreRender":
        pass

    if sceneProperties.tlm_lightmap_engine == "OctaneRender":
        pass

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

            denoiser.denoise()

        elif sceneProperties.tlm_denoise_engine == "OIDN":

            baked_image_array = []

            dirfiles = [f for f in listdir(dirpath) if isfile(join(dirpath, f))]

            for file in dirfiles:
                if file.endswith("_baked.hdr"):
                    baked_image_array.append(file)

            oidnProperties = scene.TLM_OIDNEngineProperties

            denoiser = oidn.TLM_OIDN_Denoise(oidnProperties, baked_image_array, dirpath)

            denoiser.denoise()

            

        else:
            pass

    #Filtering
    if sceneProperties.tlm_filtering_use:

        if sceneProperties.tlm_denoise_use:
            useDenoise = True
        else:
            useDenoise = False

        filter = opencv.TLM_CV_Filtering

        filter.init(dirpath, useDenoise)

    if sceneProperties.tlm_encoding_use:
        pass

    manage_build()

def manage_build():

    scene = bpy.context.scene
    sceneProperties = scene.TLM_SceneProperties

    if sceneProperties.tlm_lightmap_engine == "Cycles":

        nodes.apply_materials()

        end = "_baked"

        if sceneProperties.tlm_denoise_use:

            end = "_denoised"

        if sceneProperties.tlm_filtering_use:

            end = "_filtered"
        
        nodes.exchangeLightmapsToPostfix("_baked",end)

    if sceneProperties.tlm_lightmap_engine == "LuxCoreRender":

        pass

    if sceneProperties.tlm_lightmap_engine == "OctaneRender":

        pass

    #bpy.ops.wm.save_as_mainfile()

    for image in bpy.data.images:
        if image.users < 1:
            bpy.data.images.remove(image)

    total_time = sec_to_hours((time() - start_time))
    print(total_time)

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

                    if mat is None:
                        print("MatNone")
                        mat = bpy.data.materials.new(name="Material")
                        mat.use_nodes = True
                        slot.material = mat

                    nodes = mat.node_tree.nodes

                    #TODO FINISH MATERIAL CHECK -> Nodes check
                    #Afterwards, redo build/utility

def sec_to_hours(seconds):
    a=str(seconds//3600)
    b=str((seconds%3600)//60)
    c=str((seconds%3600)%60)
    d=["{} hours {} mins {} seconds".format(a, b, c)]
    return d