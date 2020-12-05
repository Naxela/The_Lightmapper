import bpy, math

#from . import cache
from .. utility import *

def init(self, prev_container):

    #store_existing(prev_container)

    #set_settings()

    configure_world()

    configure_lights()

    configure_meshes(self)

def configure_world():
    pass

def configure_lights():
    pass

def configure_meshes(self):

    # for obj in bpy.data.objects:
    #     if obj.type == "MESH":
    #         if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
    #             cache.backup_material_restore(obj)

    # for obj in bpy.data.objects:
    #     if obj.type == "MESH":
    #         if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
    #             cache.backup_material_rename(obj)

    for mat in bpy.data.materials:
        if mat.users < 1:
            bpy.data.materials.remove(mat)

    for mat in bpy.data.materials:
        if mat.name.startswith("."):
            if "_Original" in mat.name:
                bpy.data.materials.remove(mat)

    for image in bpy.data.images:
        if image.name.endswith("_baked"):
            bpy.data.images.remove(image, do_unlink=True)

    iterNum = 0
    currentIterNum = 0

    scene = bpy.context.scene

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                obj.hide_select = False #Remember to toggle this back

                currentIterNum = currentIterNum + 1

                obj.octane.baking_group_id = currentIterNum

                for slot in obj.material_slots:
                    if "." + slot.name + '_Original' in bpy.data.materials:
                        if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                            print("The material: " + slot.name + " shifted to " + "." + slot.name + '_Original')
                        slot.material = bpy.data.materials["." + slot.name + '_Original']

def set_settings():

    scene = bpy.context.scene
    cycles = scene.cycles
    scene.render.engine = "CYCLES"
    sceneProperties = scene.TLM_SceneProperties
    engineProperties = scene.TLM_EngineProperties
    cycles.device = scene.TLM_EngineProperties.tlm_mode

    if cycles.device == "GPU":
        scene.render.tile_x = 256
        scene.render.tile_y = 256
    else:
        scene.render.tile_x = 32
        scene.render.tile_y = 32
    
    if engineProperties.tlm_quality == "0":
        cycles.samples = 32
        cycles.max_bounces = 1
        cycles.diffuse_bounces = 1
        cycles.glossy_bounces = 1
        cycles.transparent_max_bounces = 1
        cycles.transmission_bounces = 1
        cycles.volume_bounces = 1
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "1":
        cycles.samples = 64
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "2":
        cycles.samples = 512
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "3":
        cycles.samples = 1024
        cycles.max_bounces = 256
        cycles.diffuse_bounces = 256
        cycles.glossy_bounces = 256
        cycles.transparent_max_bounces = 256
        cycles.transmission_bounces = 256
        cycles.volume_bounces = 256
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "4":
        cycles.samples = 2048
        cycles.max_bounces = 512
        cycles.diffuse_bounces = 512
        cycles.glossy_bounces = 512
        cycles.transparent_max_bounces = 512
        cycles.transmission_bounces = 512
        cycles.volume_bounces = 512
        cycles.caustics_reflective = True
        cycles.caustics_refractive = True
    else: #Custom
        pass

def store_existing(prev_container):

    scene = bpy.context.scene
    cycles = scene.cycles

    selected = []

    for obj in bpy.data.objects:
        if obj.select_get():
            selected.append(obj.name)

    prev_container["settings"] = [
        cycles.samples,
        cycles.max_bounces,
        cycles.diffuse_bounces,
        cycles.glossy_bounces,
        cycles.transparent_max_bounces,
        cycles.transmission_bounces,
        cycles.volume_bounces,
        cycles.caustics_reflective,
        cycles.caustics_refractive,
        cycles.device,
        scene.render.engine,
        bpy.context.view_layer.objects.active,
        selected,
        [scene.render.resolution_x, scene.render.resolution_y]
    ]