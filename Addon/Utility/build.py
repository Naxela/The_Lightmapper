import bpy
from . cycles import lightmap, prepare

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

    scene = bpy.context.scene
    sceneProperties = scene.TLM_SceneProperties

    if sceneProperties.tlm_lightmap_engine == "Cycles":

        #if cycles
        lightmap.bake()

    pass

    manage_build()

def manage_build():

    #if cycles
    #apply materials
    
    #print(previous_settings["settings"])

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

    # if scene.TLM_SceneProperties.tlm_denoise_use:
    #     if scene.TLM_SceneProperties.tlm_oidn_path == "":
    #         print("NO DENOISE PATH")
    #         return False
    #     else:
    #         return True
    # else:
    #     return True