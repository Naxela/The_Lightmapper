import bpy, math, os, platform, subprocess, sys, re, shutil, webbrowser, glob, bpy_extras, site, aud, datetime
from . import denoise, objectconfig, lightbake, cfilter, encoding, ambientbake, utility
import numpy as np
from time import time

module_pip = False
module_opencv = False

try:
    import pip
    module_pip = True
except ImportError:
    module_pip = False

try:
    import cv2
    module_opencv = True
except ImportError:
    pip 
    module_opencv = False

def sec_to_hours(seconds):
    a=str(seconds//3600)
    b=str((seconds%3600)//60)
    c=str((seconds%3600)%60)
    d=["{} hours {} mins {} seconds".format(a, b, c)]
    return d

def bake_background(self, context, process):
    scene = context.scene
    cycles = scene.cycles

    filepath = bpy.data.filepath

    process = subprocess.Popen([sys.executable,
        "--background",
        filepath,
        "--python-expr",
        'import bpy;p=bpy.ops.tlm.build_lightmaps();'],
        shell=False)

def bake_ordered(self, context, process):
    scene = context.scene
    cycles = scene.cycles

    stats = []

    #//////////// PRECONFIGURATION
    print("BAKING:!")
    #scene.TLM_SceneProperties.shiftMaterials = []

    if not bpy.data.is_saved:
        self.report({'INFO'}, "Please save your file first")
        return{'FINISHED'}

    total_time = time()

    if not denoise.check_denoiser_path(self, scene):
        self.report({'INFO'}, "No denoise OIDN path assigned")
        return{'FINISHED'}

    utility.check_compatible_naming(self)

    prevSettings = utility.store_existing(cycles, scene, context)
    utility.set_settings(cycles, scene)

    #configure_World()
    objectconfig.configure_lights()

    print("////////////////////////////// CONFIGURING OBJECTS")
    objectconfig.configure_objects(self, scene)

    preconfig_time = sec_to_hours((time() - total_time))

    #Baking
    print("////////////////////////////// BAKING LIGHTMAPS")
    lightbake.bake_objects(scene)

    bake_time = sec_to_hours((time() - total_time))

    #Post configuration
    print("////////////////////////////// MANAGING LIGHTMAPS")
    utility.postmanage_materials(scene)

    postconfig_time = sec_to_hours((time() - total_time))

    #Denoise lightmaps
    print("////////////////////////////// DENOISING LIGHTMAPS")
    denoise.denoise_lightmaps(scene)

    denoise_time = sec_to_hours((time() - total_time))

    #Filter lightmaps
    print("////////////////////////////// FILTERING LIGHTMAPS")
    cfilter.filter_lightmaps(self, scene, module_opencv)

    filter_time = sec_to_hours((time() - total_time))

    #Encode lightmaps
    print("////////////////////////////// ENCODING LIGHTMAPS")
    encoding.encode_lightmaps(scene)

    encode_time = sec_to_hours((time() - total_time))

    #Apply lightmaps
    print("////////////////////////////// Apply LIGHTMAPS")
    utility.apply_materials(self, scene)

    utility_time = sec_to_hours((time() - total_time))
    
    #//////////// POSTCONFIGURATION
    utility.restore_settings(cycles, scene, prevSettings)

    #TODO! STORE SELECTION AND ACTIVE OBJECT
    #TODO! RESTORE SELECTION AND ACTIVE OBJECT

    print("////////////////////////////// LIGHTMAPS BUILT")

    #BEGIN AO Baking here...
    ambientbake.TLM_Build_AO()

    ao_time = sec_to_hours((time() - total_time))

    #SAVE AO!

    #TODO: EXPOSE AO STRENGTH AND THRESHOLD
    ttime = sec_to_hours((time() - total_time))

    stats.extend([preconfig_time, bake_time, postconfig_time, denoise_time, filter_time, encode_time, utility_time, ao_time, ttime])

    scene.TLM_SceneProperties["stats"] = stats


    print("Baking finished in: {}".format(ttime))

    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)

    if scene.TLM_SceneProperties.tlm_compile_statistics:
        f = open(dirpath + "/stats.txt", "w")
        f.write("Preconfig time after: " + str(preconfig_time) + "\n")
        f.write("Bake time after: " + str(bake_time) + "\n")
        f.write("Postconfig time after: " + str(postconfig_time) + "\n")
        f.write("Denoise time after: " + str(denoise_time) + "\n")
        f.write("Filter time after: " + str(filter_time) + "\n")
        f.write("Encode time after: " + str(encode_time) + "\n")
        f.write("Utility time after: " + str(utility_time) + "\n")
        f.write("AO time after: " + str(ao_time) + "\n")
        f.write("Total time: " + str(ttime) + "\n")
        f.close()

    # print("Preconfig time after: " + str(preconfig_time))
    # print("Bake time after: " + str(bake_time))
    # print("Postconfig time after: " + str(postconfig_time))
    # print("Denoise time after: " + str(denoise_time))
    # print("Filter time after: " + str(filter_time))
    # print("Encode time after: " + str(encode_time))
    # print("Utility time after: " + str(utility_time))
    # print("AO time after: " + str(ao_time))
    # print("Total time: " + str(ttime))

    if scene.TLM_SceneProperties.tlm_play_sound:

        scriptDir = os.path.dirname(os.path.realpath(__file__))
        sound_path = os.path.abspath(os.path.join(scriptDir, '..', 'Assets/sound.ogg'))

        device = aud.Device()
        sound = aud.Sound.file(sound_path)
        device.play(sound)

    process = False