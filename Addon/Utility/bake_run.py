import bpy, math, os, platform, subprocess, sys, re, shutil, webbrowser, glob, bpy_extras, site, aud
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

def bake_ordered(self, context, process):
    scene = context.scene
    cycles = scene.cycles

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

    #Baking
    print("////////////////////////////// BAKING LIGHTMAPS")
    lightbake.bake_objects(scene)

    #Post configuration
    print("////////////////////////////// MANAGING LIGHTMAPS")
    utility.postmanage_materials(scene)

    #Denoise lightmaps
    print("////////////////////////////// DENOISING LIGHTMAPS")
    denoise.denoise_lightmaps(scene)

    #Filter lightmaps
    print("////////////////////////////// FILTERING LIGHTMAPS")
    cfilter.filter_lightmaps(self, scene, module_opencv)

    #Encode lightmaps
    print("////////////////////////////// ENCODING LIGHTMAPS")
    encoding.encode_lightmaps(scene)

    #Apply lightmaps
    print("////////////////////////////// Apply LIGHTMAPS")
    utility.apply_materials(self, scene)
    
    #//////////// POSTCONFIGURATION
    utility.restore_settings(cycles, scene, prevSettings)

    #TODO! STORE SELECTION AND ACTIVE OBJECT
    #TODO! RESTORE SELECTION AND ACTIVE OBJECT

    print("////////////////////////////// LIGHTMAPS BUILT")

    #BEGIN AO Baking here...
    ambientbake.TLM_Build_AO()

    #SAVE AO!

    #TODO: EXPOSE AO STRENGTH AND THRESHOLD

    print("Baking finished in: %.3f s" % (time() - total_time))

    if scene.TLM_SceneProperties.tlm_play_sound:

        scriptDir = os.path.dirname(os.path.realpath(__file__))
        sound_path = os.path.abspath(os.path.join(scriptDir, '..', 'Assets/sound.ogg'))

        device = aud.Device()
        sound = aud.Sound.file(sound_path)
        device.play(sound)

    process = False