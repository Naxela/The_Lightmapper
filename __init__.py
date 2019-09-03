bl_info = {
    "name": "HDR Lightmapper",
    "category": "Render",
    "location": "Properties -> Render -> HDR Lightmapper",
    "description": "HDR Lightmapping solution for Blender",
    "author": "Alexander Kleemann",
    "version": (0, 0, 1),
    "blender": (2, 80, 0)
}

import bpy, math, os, platform, subprocess, sys, re, shutil, webbrowser, glob
from bpy.app.handlers import persistent
from bpy.props import *
from bpy.types import Menu, Panel, UIList
import numpy as np
from time import time

module_pip = False
module_opencv = False
module_armory = False


#bpy.context.object.update_tag({‘OBJECT’, ‘DATA’, ‘TIME’})

#import pip OR install pip os.system('python path-to-get-pip')
#Check if python is set in environment variables
#Check if pip is installed
#system: pip install opencv-python
#system: pip install matplotlib

#install pip
#install opencv-python
#uninstall numpy
#install numpy

#TODO:
#CHECK IF TWO OBJECTS SHARE MATERIAL IF SO SPLIT [Privatize Materials]?? Add shared material support later on...
#Weighted lightmap [Fixed;Dimension] for [Selection/Volume/Collection]
#ADD MARGIN FOR UVUNWRAP

try:
    import pip
    module_pip = True
except ImportError:
    module_pip = False
    print("Pip not found")

try:
    import cv2
    module_opencv = True
except ImportError:
    #pip 
    module_opencv = False

try:
    import arm
    module_armory = True
except ImportError:
    module_armory = False

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class HDRLM_PT_Panel(bpy.types.Panel):
    bl_label = "HDR Lightmapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.operator("hdrlm.build_lighting")
        row = layout.row()
        row.operator("hdrlm.build_lighting_selected")
        row = layout.row()
        row.operator("hdrlm.build_ao")
        row = layout.row()
        row.operator("hdrlm.enable_lighting")
        row = layout.row()
        row.operator("hdrlm.disable_lighting")
        row = layout.row()
        row.operator("hdrlm.clean_lighting")
        row = layout.row()
        row.operator("hdrlm.open_lightmap_folder")

class HDRLM_PT_MeshMenu(bpy.types.Panel):
    bl_label = "HDR Lightmapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = bpy.context.object
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene

        if obj.type == "MESH":
            row = layout.row(align=True)
            row.prop(obj, "hdrlm_mesh_lightmap_use")
            if obj.hdrlm_mesh_lightmap_use:
                #row = layout.row()
                #row.prop(obj, "hdrlm_mesh_apply_after")
                #row = layout.row()
                #row.prop(obj, "hdrlm_mesh_emissive")
                #row = layout.row()
                #row.prop(obj, "hdrlm_mesh_emissive_shadow")
                row = layout.row()
                row.prop(obj, "hdrlm_mesh_lightmap_resolution")
                row = layout.row()
                row.prop(obj, "hdrlm_mesh_lightmap_unwrap_mode")
                row = layout.row()
                row.prop(obj, "hdrlm_mesh_unwrap_margin")
                row = layout.row()
                row.prop(obj, "hdrlm_mesh_bake_ao")

class HDRLM_PT_LightMenu(bpy.types.Panel):
    bl_label = "HDR Lightmapper"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene

        obj = bpy.context.object
        if obj == None:
            return

        if obj.type == "LIGHT":
            row = layout.row(align=True)
            row.prop(obj, "hdrlm_light_lightmap_use")

            if obj.hdrlm_light_lightmap_use:
                row = layout.row(align=True)
                row.prop(obj, "hdrlm_light_type", expand=True)
                row = layout.row(align=True)
                row.prop(obj, "hdrlm_light_intensity_scale")
                row = layout.row(align=True)
                row.prop(obj, "hdrlm_light_casts_shadows")

class HDRLM_PT_Unwrap(bpy.types.Panel):
    bl_label = "Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "HDRLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        row = layout.row()
        row.prop(scene, 'hdrlm_mode')
        row = layout.row(align=True)
        row.prop(scene, 'hdrlm_quality')
        row = layout.row(align=True)
        row.prop(scene, 'hdrlm_lightmap_scale', expand=True)
        row = layout.row(align=True)
        row.prop(scene, 'hdrlm_lightmap_savedir')
        row = layout.row(align=True)
        row.prop(scene, "hdrlm_caching_mode")
        row = layout.row(align=True)
        row.prop(scene, 'hdrlm_dilation_margin')
        row = layout.row(align=True)
        row.prop(scene, 'hdrlm_apply_on_unwrap')
        row = layout.row(align=True)
        row.prop(scene, 'hdrlm_indirect_only')
        row = layout.row(align=True)
        row.prop(scene, 'hdrlm_keep_cache_files')
        #row = layout.row(align=True)
        #row.prop(scene, 'bpy.types.Scene.hdrlm_delete_cache')

class HDRLM_PT_Denoise(bpy.types.Panel):
    bl_label = "Denoise"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "HDRLM_PT_Panel"

    def draw_header(self, context):
        scene = context.scene
        self.layout.prop(scene, "hdrlm_denoise_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene
        layout.active = scene.hdrlm_denoise_use

        row = layout.row(align=True)
        row.prop(scene, "hdrlm_denoiser", expand=True)
        if scene.hdrlm_denoiser == "OIDN":
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_oidn_path")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_oidn_verbose")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_oidn_threads")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_oidn_maxmem")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_oidn_affinity")
        if scene.hdrlm_denoiser == "Optix":
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_optix_path")
        #row = layout.row(align=True)
        #row.prop(scene, "hdrlm_oidn_use_albedo")
        #row = layout.row(align=True)
        #row.prop(scene, "hdrlm_oidn_use_normal")

class HDRLM_PT_Filtering(bpy.types.Panel):
    bl_label = "Filtering"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "HDRLM_PT_Panel"

    def draw_header(self, context):
        scene = context.scene
        self.layout.prop(scene, "hdrlm_filtering_use", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        #layout.active = scene.hdrlm_filtering_use

        column = layout.column()
        box = column.box()
        if module_opencv:
            box.label(text="OpenCV Installed", icon="INFO")
        else:
            box.label(text="Please restart Blender after installing")
            box.operator("hdrlm.install_opencv",icon="PREFERENCES")

        if(scene.hdrlm_filtering_use):
            if(module_opencv):
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False
        
        #row = layout.row(align=True)
        #row.prop(scene, "hdrlm_filtering_gimp_path")

        #split = box.split()

        row = layout.row(align=True)
        row.prop(scene, "hdrlm_filtering_mode")
        row = layout.row(align=True)
        if scene.hdrlm_filtering_mode == "Gaussian":
            row.prop(scene, "hdrlm_filtering_gaussian_strength")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_filtering_iterations")
        elif scene.hdrlm_filtering_mode == "Box":
            row.prop(scene, "hdrlm_filtering_box_strength")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_filtering_iterations")

        elif scene.hdrlm_filtering_mode == "Bilateral":
            row.prop(scene, "hdrlm_filtering_bilateral_diameter")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_filtering_bilateral_color_deviation")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_filtering_bilateral_coordinate_deviation")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_filtering_iterations")
        else:
            row.prop(scene, "hdrlm_filtering_median_kernel", expand=True)
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_filtering_iterations")

class HDRLM_PT_Encoding(bpy.types.Panel):
    bl_label = "Encoding"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "HDRLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        row = layout.row(align=True)
        row.prop(scene, "hdrlm_encoding_mode", expand=True)
        if scene.hdrlm_encoding_mode == "RGBM" or scene.hdrlm_encoding_mode == "RGBD":
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_encoding_range")
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_encoding_armory_setup")
        row = layout.row(align=True)
        row.prop(scene, "hdrlm_encoding_colorspace")

class HDRLM_PT_Compression(bpy.types.Panel):
    bl_label = "Compression"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "HDRLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        if scene.hdrlm_encoding_mode == "RGBE":
            layout.label(text="HDR compression not available for RGBE")
        else:
            row = layout.row(align=True)
            row.prop(scene, "hdrlm_compression")

class HDRLM_PT_Additional(bpy.types.Panel):
    bl_label = "Additional Armory Features"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "HDRLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False

        try:
            import arm
            module_armory = True
        except ImportError:
            module_armory = False

        if module_armory:
            row = layout.row(align=True)
            layout.label(text="Armory found! Hooray!")
            row.operator("hdrlm.create_world_volume")
        else:
             layout.label(text="Armory not detected.")

class HDRLM_PT_LightmapList(bpy.types.Panel):
    bl_label = "Lightmaps"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "HDRLM_PT_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False
        row = layout.row(align=True)
        row.operator("image.rgbm_encode")

#class HDRLM_PT_LightmapStatus:
#    def __init__(self):

class HDRLM_CreateWorldVolume(bpy.types.Operator):
    """Create World Volume"""
    bl_idname = "hdrlm.create_world_volume"
    bl_label = "Create World Volume"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        try:
            import arm
            module_armory = True
        except ImportError:
            module_armory = False

        createWorldVolume(self, context, arm)

        return {'FINISHED'}

class HDRLM_BuildAO(bpy.types.Operator):
    """Builds the lighting"""
    bl_idname = "hdrlm.build_ao"
    bl_label = "Build Ambient Occlusion"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        HDRLM_Build_AO(self, context)
        ##HDRLM_Build(self, context)
        return {'FINISHED'}

class HDRLM_BuildLighting(bpy.types.Operator):
    """Builds the lighting"""
    bl_idname = "hdrlm.build_lighting"
    bl_label = "Build Light"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        HDRLM_Build(self, context)
        return {'FINISHED'}

class HDRLM_BuildLightingSelected(bpy.types.Operator):
    """Builds the lighting for a selected"""
    bl_idname = "hdrlm.build_lighting_selected"
    bl_label = "Build Light for selected"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        #TODO! SOME WAY TO TOGGLE ON AND OFF THE EXISTING OBJ WITH LIGHTMAPPING VALUES
        #Array prev toggle = all with lightmap true
        previousToggle = []

        for obj in bpy.data.objects:
            if(obj.hdrlm_mesh_lightmap_use):
                previousToggle.append(obj.name)
            obj.hdrlm_mesh_lightmap_use = False

        for obj in bpy.context.selected_objects:
            obj.hdrlm_mesh_lightmap_use = True

        HDRLM_Build(self, context)

        for obj in bpy.data.objects:
            obj.hdrlm_mesh_lightmap_use = False
            if obj.name in previousToggle:
                obj.hdrlm_mesh_lightmap_use = True
            
        return {'FINISHED'}

class HDRLM_ToggleEnableforSelection(bpy.types.Operator):
    """Toggle lightmapping for selection"""
    bl_idname = "hdrlm.enable_lighting"
    bl_label = "Enable for selection"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            obj.hdrlm_mesh_lightmap_use = True
        return {'FINISHED'}

class HDRLM_ToggleDisableforSelection(bpy.types.Operator):
    """Disable lightmapping for selection"""
    bl_idname = "hdrlm.disable_lighting"
    bl_label = "Disable for selection"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            obj.hdrlm_mesh_lightmap_use = False
        return {'FINISHED'}

class HDRLM_MakeUniqueMaterials(bpy.types.Operator):
    """Disable lightmapping for selection"""
    bl_idname = "hdrlm.make_unique_materials"
    bl_label = "Make Unique Materials"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #for obj in bpy.context.selected_objects:
        #    obj.hdrlm_mesh_lightmap_use = False
        return {'FINISHED'}

class HDRLM_CleanLighting(bpy.types.Operator):
    """Clean lightmap cache"""
    bl_idname = "hdrlm.clean_lighting"
    bl_label = "Clean Lightmap cache"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.hdrlm_mesh_lightmap_use:
                    for slot in obj.material_slots:
                        backup_material_restore(slot)

        # for m in bpy.data.materials: #TODO - CHANGE INTO SPECIFIC MATERIAL
        #     nodetree = m.node_tree
        #     nodes = nodetree.nodes
        #     mainNode = nodetree.nodes[0].inputs[0].links[0].from_node
            
        #     for n in nodes:
        #         if "LM" in n.name:
        #             nodetree.links.new(n.outputs[0], mainNode.inputs[0])
            
        #     for n in nodes:
        #         if "Lightmap" in n.name:
        #             nodes.remove(n)

        # for obj in bpy.data.objects:
        #     for slot in obj.material_slots:
        #         #Soft refresh
        #         #tempMat = bpy.data.materials.new(name='hdrlm_temporary_shift')
        #         #tempMat.use_nodes = True
        #         #mat = bpy.data.materials[slot.material.name]
        #         #slot.material = bpy.data.materials["AAA"]
        #         #slot.material = mat
        #         pass
        #         #mat = bpy.
        #         #mat = bpy.data.materials[slot.material.name]
        #         #slot.material = bpy.data.materials["hdrlm_temporary_shift"]
        #         #slot.material = mat

        # for mat in bpy.data.materials:
        #     if mat.name.endswith('_baked') or mat.name.endswith('_temp'):
        #         bpy.data.materials.remove(mat, do_unlink=True)


        scene = context.scene
        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.hdrlm_lightmap_savedir)
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath)

        # for obj in bpy.data.objects:

        #     ###### MESH / BAKING
        #     if obj.type == "MESH":
        #         if obj.hdrlm_mesh_lightmap_use:

        #             if obj.type == "MESH":
        #                 if "UVMap_baked" in obj.data.uv_layers:
        #                     obj.data.uv_layers.remove(obj.data.uv_layers["UVMap_Lightmaps"])

        #             for slot in obj.material_slots:
        #                 mat = slot.material
        #                 # Remove temp material
        #                 if mat.name.endswith('_temp'):
        #                     old = slot.material
        #                     slot.material = bpy.data.materials[old.name.split('_' + obj.name)[0]]
        #                     bpy.data.materials.remove(old, do_unlink=True)
            
        #             for m in obj.material_slots:
                        
        #                 nodetree = bpy.data.materials[m.name].node_tree

        #                 #Get the material output node
        #                 OutputNode = nodetree.nodes[0]

        #                 #Get the connected node (usually either principled bsdf or armory)
        #                 mainNode = OutputNode.inputs[0].links[0].from_node

        #                 hasPreviousBasecolor = False

        #                 for n in nodetree.nodes:

        #                     prefix = "Lightmap_"
        #                     if n.name == prefix + "Image":
        #                         nodetree.nodes.remove(nodetree.nodes[n.name])

        #                     if n.name == prefix + "Multiplication":
        #                         nodetree.nodes.remove(nodetree.nodes[n.name])

        #                     if n.name == prefix + "UV":
        #                         nodetree.nodes.remove(nodetree.nodes[n.name])

        #                     if n.name == prefix + "RGBM_Decode":
        #                         nodetree.nodes.remove(nodetree.nodes[n.name])

        #                     if n.name == prefix + "BasecolorNode":
        #                         hasPreviousBasecolor = True

        #                 if hasPreviousBasecolor:
        #                     nodetree.links.new(mainNode.inputs[0], nodetree.nodes[prefix+"BasecolorNode"].outputs[0])

        # for mat in bpy.data.materials:
        #     if mat.name.endswith('_baked') or mat.name.endswith('_temp'):
        #         bpy.data.materials.remove(mat, do_unlink=True)

        # for img in bpy.data.images:
        #     if not img.users:
        #         bpy.data.images.remove(img)

        for mat in bpy.data.materials:
            mat.update_tag()

        return{'FINISHED'}


class HDRLM_LightmapFolder(bpy.types.Operator):
    """Open Lightmap Folder"""
    bl_idname = "hdrlm.open_lightmap_folder"
    bl_label = "Explore lightmaps"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        if not bpy.data.is_saved:
            self.report({'INFO'}, "Please save your file first")
            return {"CANCELLED"}

        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.hdrlm_lightmap_savedir)

        if os.path.isdir(dirpath):
            webbrowser.open('file://' + dirpath)
        else:
            os.mkdir(dirpath)
            webbrowser.open('file://' + dirpath)

        return{'FINISHED'}

class HDRLM_InstallOpenCV(bpy.types.Operator):
    """Install OpenCV"""
    bl_idname = "hdrlm.install_opencv"
    bl_label = "Install OpenCV"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        pythonbinpath = bpy.app.binary_path_python

        if platform.system() == "Windows":
            pythonlibpath = os.path.join(os.path.dirname(os.path.dirname(pythonbinpath)), "lib")
        else:
            pythonlibpath = os.path.join(os.path.dirname(os.path.dirname(pythonbinpath)), "lib", os.path.basename(pythonbinpath)[:-1])

        ensurepippath = os.path.join(pythonlibpath, "ensurepip")

        cmda = [pythonbinpath, ensurepippath, "--upgrade", "--user"]
        pip = subprocess.run(cmda, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if pip.returncode == 0:
            print("Sucessfully installed pip!\n")
        else:
            print("Failed to install pip!\n")
            return{'FINISHED'}

        cmdb = [pythonbinpath, "-m", "pip", "install", "opencv-python"]
        
        opencv = subprocess.run(cmdb, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if opencv.returncode == 0:
            print("Sucessfully installed OpenCV!\n")
        else:
            print("Failed to install OpenCV!\n")
            return{'FINISHED'}

        module_opencv = True
        ShowMessageBox("Please restart blender to enable OpenCV filtering", "Restart", 'PREFERENCES')

        return{'FINISHED'}

# function to clamp float
def saturate(num, floats=True):
    if num < 0:
        num = 0
    elif num > (1 if floats else 255):
        num = (1 if floats else 255)
    return num 

class HDRLM_EncodeToRGBM(bpy.types.Operator):
    """Encodes the currently viewed HDR image to RGBM format"""
    bl_idname = "image.rgbm_encode"
    bl_label = "Encode HDR to RGBM"
    bl_description = "Encode HDR/float image to RGBM format. Create new image with '_RGBM.png' prefix"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.type == 'IMAGE_EDITOR' and sima.image and sima.image.is_float

    def execute(self, context):
        sima = context.space_data
        # Image
        ima = sima.image
        ima_name = ima.name

        if ima.colorspace_settings.name != 'Linear':
            ima.colorspace_settings.name = 'Linear'

        # Removing .exr or .hdr prefix
        if ima_name[-4:] == '.exr' or ima_name[-4:] == '.hdr':
            ima_name = ima_name[:-4]

        target_ima = bpy.data.images.get(ima_name + '_RGBM.png')
        if not target_ima:
            target_ima = bpy.data.images.new(
                    name = ima_name + '_RGBM.png',
                    width = ima.size[0],
                    height = ima.size[1],
                    alpha = True,
                    float_buffer = False
                    )
        
        num_pixels = len(ima.pixels)
        result_pixel = list(ima.pixels)
        
        # Encode to RGBM
        for i in range(0,num_pixels,4):
            for j in range(3):
                result_pixel[i+j] *= 1.0 / 8.0
            result_pixel[i+3] = saturate(max(result_pixel[i], result_pixel[i+1], result_pixel[i+2], 1e-6))
            result_pixel[i+3] = math.ceil(result_pixel[i+3] * 255.0) / 255.0;
            for j in range(3):
                result_pixel[i+j] /= result_pixel[i+3]
        
        target_ima.pixels = result_pixel
        
        sima.image = target_ima

        return {'FINISHED'}

def encodeImageRGBM(self, image, maxRange, outDir, quality):
    input_image = bpy.data.images[image.name]
    image_name = input_image.name

    if input_image.colorspace_settings.name != 'Linear':
        input_image.colorspace_settings.name = 'Linear'

    # Removing .exr or .hdr prefix
    if image_name[-4:] == '.exr' or image_name[-4:] == '.hdr':
        image_name = image_name[:-4]

    target_image = bpy.data.images.get(image_name + '_encoded')
    print(image_name + '_encoded')
    if not target_image:
        target_image = bpy.data.images.new(
                name = image_name + '_encoded',
                width = input_image.size[0],
                height = input_image.size[1],
                alpha = True,
                float_buffer = False
                )
    
    num_pixels = len(input_image.pixels)
    result_pixel = list(input_image.pixels)

    for i in range(0,num_pixels,4):
        for j in range(3):
            result_pixel[i+j] *= 1.0 / maxRange;
        result_pixel[i+3] = saturate(max(result_pixel[i], result_pixel[i+1], result_pixel[i+2], 1e-6))
        result_pixel[i+3] = math.ceil(result_pixel[i+3] * 255.0) / 255.0
        for j in range(3):
            result_pixel[i+j] /= result_pixel[i+3]
    
    target_image.pixels = result_pixel
    input_image = target_image
    
    #Save RGBM
    input_image.filepath_raw = outDir + "_encoded.png"
    input_image.file_format = "PNG"
    bpy.context.scene.render.image_settings.quality = quality
    input_image.save_render(filepath = input_image.filepath_raw, scene = bpy.context.scene)
    #input_image.
    #input_image.save()

def encodeImageRGBD(self, image, maxRange, outDir):
    input_image = bpy.data.images[image.name]
    image_name = input_image.name

    if input_image.colorspace_settings.name != 'Linear':
        input_image.colorspace_settings.name = 'Linear'

    # Removing .exr or .hdr prefix
    if image_name[-4:] == '.exr' or image_name[-4:] == '.hdr':
        image_name = image_name[:-4]

    target_image = bpy.data.images.get(image_name + '_encoded')
    if not target_image:
        target_image = bpy.data.images.new(
                name = image_name + '_encoded',
                width = input_image.size[0],
                height = input_image.size[1],
                alpha = True,
                float_buffer = False
                )
    
    num_pixels = len(input_image.pixels)
    result_pixel = list(input_image.pixels)

    for i in range(0,num_pixels,4):

        m = saturate(max(result_pixel[i], result_pixel[i+1], result_pixel[i+2], 1e-6))
        d = max(maxRange / m, 1)
        d = saturate( math.floor(d) / 255 )

        result_pixel[i] = result_pixel[i] * d * 255 / maxRange
        result_pixel[i+1] = result_pixel[i+1] * d * 255 / maxRange
        result_pixel[i+2] = result_pixel[i+2] * d * 255 / maxRange
        result_pixel[i+3] = d
    
    target_image.pixels = result_pixel
    
    input_image = target_image

    #Save RGBD
    input_image.filepath_raw = outDir + "_encoded.png"
    input_image.file_format = "PNG"
    input_image.save()

def lerpNodePoints(self, a, b, c):
    return (a + c * (b - a))

def draw(self, context):
    row = self.layout.row()
    row.label(text="Convert:")
    row = self.layout.row()
    row.operator("image.rgbm_encode")

def load_pfm(file, as_flat_list=False):
    """
    Load a PFM file into a Numpy array. Note that it will have
    a shape of H x W, not W x H. Returns a tuple containing the
    loaded image and the scale factor from the file.
    Usage:
    with open(r"path/to/file.pfm", "rb") as f:
        data, scale = load_pfm(f)
    """
    #start = time()

    header = file.readline().decode("utf-8").rstrip()
    if header == "PF":
        color = True
    elif header == "Pf":
        color = False
    else:
        raise Exception("Not a PFM file.")

    dim_match = re.match(r"^(\d+)\s(\d+)\s$", file.readline().decode("utf-8"))
    if dim_match:
        width, height = map(int, dim_match.groups())
    else:
        raise Exception("Malformed PFM header.")

    scale = float(file.readline().decode("utf-8").rstrip())
    if scale < 0:  # little-endian
        endian = "<"
        scale = -scale
    else:
        endian = ">"  # big-endian

    data = np.fromfile(file, endian + "f")
    shape = (height, width, 3) if color else (height, width)
    if as_flat_list:
        result = data
    else:
        result = np.reshape(data, shape)
    #print("PFM import took %.3f s" % (time() - start))
    return result, scale

def save_pfm(file, image, scale=1):
    """
    Save a Numpy array to a PFM file.
    Usage:
    with open(r"/path/to/out.pfm", "wb") as f:
        save_pfm(f, data)
    """
    #start = time()

    if image.dtype.name != "float32":
        raise Exception("Image dtype must be float32 (got %s)" % image.dtype.name)

    if len(image.shape) == 3 and image.shape[2] == 3:  # color image
        color = True
    elif len(image.shape) == 2 or len(image.shape) == 3 and image.shape[2] == 1:  # greyscale
        color = False
    else:
        raise Exception("Image must have H x W x 3, H x W x 1 or H x W dimensions.")

    file.write(b"PF\n" if color else b"Pf\n")
    file.write(b"%d %d\n" % (image.shape[1], image.shape[0]))

    endian = image.dtype.byteorder

    if endian == "<" or endian == "=" and sys.byteorder == "little":
        scale = -scale

    file.write(b"%f\n" % scale)

    image.tofile(file)

    #print("PFM export took %.3f s" % (time() - start))

def backup_material_copy(slot):
    material = slot.material
    dup = material.copy()
    dup.name = material.name + "_Original"
    dup.use_fake_user = True

def backup_material_restore(slot):
    material = slot.material
    if material.name + "_Original" in bpy.data.materials:
        original = bpy.data.materials[material.name + "_Original"]
        slot.material = original
        material.name = material.name + "_temp"
        original.name = original.name[:-9]
        original.use_fake_user = False
        material.user_clear()
        bpy.data.materials.remove(material)
    else:
        pass
        #Check if material has nodes with lightmap prefix

def backup_material_cache():
    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.hdrlm_lightmap_savedir)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)

    cachefilepath = os.path.join(dirpath, "HDRLM_cache.blend")
    bpy.ops.wm.save_as_mainfile(filepath=cachefilepath, copy=True)

def backup_material_cache_restore(matname):
    from os.path import join

    path_to_scripts = bpy.utils.script_paths()[0]
    path_to_script = join(path_to_scripts, 'addons_contrib', 'io_material_loader')

    material_locator = "\\Material\\"
    file_name = "practicality.blend"    

    opath = "//" + file_name + material_locator + matname
    dpath = join(path_to_script, file_name) + material_locator

    bpy.ops.wm.link_append(
            filepath=opath,     # "//filename.blend\\Folder\\"
            filename=matname,   # "material_name
            directory=dpath,    # "fullpath + \\Folder\\
            filemode=1,
            link=False,
            autoselect=False,
            active_layer=True,
            instance_groups=False,
            relative_path=True)

def HDRLM_Build_AO(self, context):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"

    prevObjRenderset = []

    #for obj in bpy.context.selected_objects:
    #    obj.hdrlm_mesh_lightmap_use = True

    #Store previous settings for hide_render
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if not obj.hide_render:
                prevObjRenderset.append(obj.name)

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj.hide_render = True

    #Bake AO for selection
    for obj in bpy.context.selected_objects:
        if obj.type == "MESH":
            obj.hide_render = False

    for obj in bpy.context.selected_objects:
        if obj.type == "MESH":

            if len(obj.material_slots) == 0:
                    single = False
                    number = 0
                    while single == False:
                        matname = obj.name + ".00" + str(number)
                        if matname in bpy.data.materials:
                            single = False
                            number = number + 1
                        else:
                            mat = bpy.data.materials.new(name=matname)
                            mat.use_nodes = True
                            obj.data.materials.append(mat)
                            single = True

            for mat in bpy.data.materials:
                if mat.name.endswith('_bakedAO'):
                    bpy.data.materials.remove(mat, do_unlink=True)
            for img in bpy.data.images:
                if img.name == obj.name + "_bakedAO":
                    bpy.data.images.remove(img, do_unlink=True)

            #Single user materials?
            ob = obj
            for slot in ob.material_slots:
                # Temp material already exists
                if slot.material.name.endswith('_tempAO'):
                    continue
                n = slot.material.name + '_' + ob.name + '_tempAO'
                if not n in bpy.data.materials:
                    slot.material = slot.material.copy()
                slot.material.name = n

            #Add images for baking
            img_name = obj.name + '_bakedAO'
            res = int(obj.hdrlm_mesh_lightmap_resolution) / int(scene.hdrlm_lightmap_scale)
            if img_name not in bpy.data.images or bpy.data.images[img_name].size[0] != res or bpy.data.images[img_name].size[1] != res:
                img = bpy.data.images.new(img_name, res, res, alpha=False, float_buffer=False)
                img.name = img_name
            else:
                img = bpy.data.images[img_name]

            for slot in obj.material_slots:
                mat = slot.material
                mat.use_nodes = True
                nodes = mat.node_tree.nodes

                if "Baked AO Image" in nodes:
                    img_node = nodes["Baked AO Image"]
                else:
                    img_node = nodes.new('ShaderNodeTexImage')
                    img_node.name = 'Baked AO Image'
                    img_node.location = (100, 100)
                    img_node.image = img
                img_node.select = True
                nodes.active = img_node

            if scene.hdrlm_apply_on_unwrap:
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            uv_layers = obj.data.uv_layers
            if not "UVMap_Lightmap" in uv_layers:
                uvmap = uv_layers.new(name="UVMap_Lightmap")
                uv_layers.active_index = len(uv_layers) - 1
                if obj.hdrlm_mesh_lightmap_unwrap_mode == "Lightmap":
                    bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.hdrlm_mesh_unwrap_margin)
                elif obj.hdrlm_mesh_lightmap_unwrap_mode == "Smart Project":
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=obj.hdrlm_mesh_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
                else:
                    pass
            else:
                for i in range(0, len(uv_layers)):
                    if uv_layers[i].name == 'UVMap_Lightmap':
                        uv_layers.active_index = i
                        break

            for slot in obj.material_slots:

                #ONLY 1 MATERIAL PER OBJECT SUPPORTED FOR NOW!
                nodetree = slot.material.node_tree
                bpy.context.active_object.active_material = slot.material

                n = slot.material.name[:-5] + '_bakedAO'
                if not n in bpy.data.materials:
                    mat = bpy.data.materials.new(name=n)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    img_node = nodes.new('ShaderNodeTexImage')
                    img_node.name = "Baked AO Image"
                    img_node.location = (100, 100)
                    img_node.image = bpy.data.images[img_name]
                    mat.node_tree.links.new(img_node.outputs[0], nodes['Principled BSDF'].inputs[0])
                else:
                    mat = bpy.data.materials[n]
                    nodes = mat.node_tree.nodes
                    nodes['Baked AO Image'].image = bpy.data.images[img_name]

            for slot in obj.material_slots:

                nodetree = bpy.data.materials[slot.name].node_tree
                nodes = nodetree.nodes
                mainNode = nodetree.nodes[0].inputs[0].links[0].from_node

                for n in nodes:
                    if "LM" in n.name:
                        nodetree.links.new(n.outputs[0], mainNode.inputs[0])

                for n in nodes:
                    if "Lightmap" in n.name:
                            #print("Remove")
                            nodes.remove(n)

            print("Baking: " + bpy.context.view_layer.objects.active.name)

            bpy.ops.object.bake(type="AO", margin=scene.hdrlm_dilation_margin)

            for slot in obj.material_slots:
                mat = slot.material
                if mat.name.endswith('_tempAO'):
                    old = slot.material
                    slot.material = bpy.data.materials[old.name.split('_' + obj.name)[0]]
                    bpy.data.materials.remove(old, do_unlink=True)

            uv_layers = obj.data.uv_layers
            uv_layers.active_index = 0

            for slot in obj.material_slots:

                nodetree = bpy.data.materials[slot.name].node_tree

                outputNode = nodetree.nodes[0]

                mainNode = outputNode.inputs[0].links[0].from_node

                if len(mainNode.inputs[0].links) == 0:
                    baseColorValue = mainNode.inputs[0].default_value
                    baseColorNode = nodetree.nodes.new(type="ShaderNodeRGB")
                    baseColorNode.outputs[0].default_value = baseColorValue
                    baseColorNode.location = ((mainNode.location[0]-500,mainNode.location[1]))
                    baseColorNode.name = "AO_BasecolorNode_A"
                else:
                    baseColorNode = mainNode.inputs[0].links[0].from_node
                    baseColorNode.name = "AO_P"

                nodePos1 = mainNode.location
                nodePos2 = baseColorNode.location

                mixNode = nodetree.nodes.new(type="ShaderNodeMixRGB")
                mixNode.name = "AO_Multiplication"
                mixNode.location = lerpNodePoints(self, nodePos1, nodePos2, 0.5)
                if scene.hdrlm_indirect_only:
                    mixNode.blend_type = 'ADD'
                else:
                    mixNode.blend_type = 'MULTIPLY'
                
                mixNode.inputs[0].default_value = 1.0

                LightmapNode = nodetree.nodes.new(type="ShaderNodeTexImage")
                LightmapNode.location = ((baseColorNode.location[0]-300,baseColorNode.location[1] + 300))
                LightmapNode.image = bpy.data.images[obj.name + "_bakedAO"]
                LightmapNode.name = "AO_Image"

                UVLightmap = nodetree.nodes.new(type="ShaderNodeUVMap")
                UVLightmap.uv_map = "UVMap_Lightmap"
                UVLightmap.name = "AO_UV"
                UVLightmap.location = ((-1000, baseColorNode.location[1] + 300))

                nodetree.links.new(baseColorNode.outputs[0], mixNode.inputs[1]) 
                nodetree.links.new(LightmapNode.outputs[0], mixNode.inputs[2])
                nodetree.links.new(mixNode.outputs[0], mainNode.inputs[0]) 
                nodetree.links.new(UVLightmap.outputs[0], LightmapNode.inputs[0])

            return{'FINISHED'}

def createWorldVolume(self, context, arm):
    camera = bpy.data.cameras.new("WVCam")
    cam_obj = bpy.data.objects.new("WVCamera", camera)
    bpy.context.collection.objects.link(cam_obj)

    cam_obj.location = bpy.context.scene.cursor.location
    camera.angle = math.radians(90)

    prevResx = bpy.context.scene.render.resolution_x
    prevResy = bpy.context.scene.render.resolution_y
    prevCam = bpy.context.scene.camera
    prevEngine = bpy.context.scene.render.engine
    bpy.context.scene.camera = cam_obj

    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.render.resolution_x = 512
    bpy.context.scene.render.resolution_y = 512

    savedir = os.path.join(os.path.dirname(bpy.data.filepath), bpy.context.scene.hdrlm_lightmap_savedir)
    directory = os.path.join(savedir, "Probes")

    t = 90

    positions = {
        "xp" : (math.radians(t),0,0),
        "zp" : (math.radians(t),0,math.radians(t)),
        "xm" : (math.radians(t),0,math.radians(t*2)),
        "zm" : (math.radians(t),0,math.radians(-t)),
        "yp" : (math.radians(t*2),0,math.radians(t)),
        "ym" : (0,0,math.radians(t))
    }

    cam = cam_obj
    image_settings = bpy.context.scene.render.image_settings
    image_settings.file_format = "HDR"
    image_settings.color_depth = '32'

    for val in positions:
        cam.rotation_euler = positions[val]
        
        filename = os.path.join(directory, val) + ".hdr"
        bpy.data.scenes['Scene'].render.filepath = filename
        bpy.ops.render.render(write_still=True)

    sdk_path = arm.utils.get_sdk_path()

    if arm.utils.get_os() == 'win':
        cmft_path = sdk_path + '/lib/armory_tools/cmft/cmft.exe'
    elif arm.utils.get_os() == 'mac':
        cmft_path = '"' + sdk_path + '/lib/armory_tools/cmft/cmft-osx"'
    else:
        cmft_path = '"' + sdk_path + '/lib/armory_tools/cmft/cmft-linux64"'

    output_file_irr = "COMBINED2.hdr"

    posx = directory + "/" + "xp" + ".hdr"
    negx = directory + "/" + "xm" + ".hdr"
    posy = directory + "/" + "yp" + ".hdr"
    negy = directory + "/" + "ym" + ".hdr"
    posz = directory + "/" + "zp" + ".hdr"
    negz = directory + "/" + "zm" + ".hdr"
    output = directory + "/" + "combined"

    if arm.utils.get_os() == 'win':
        envpipe = [cmft_path, 
        '--inputFacePosX', posx, 
        '--inputFaceNegX', negx, 
        '--inputFacePosY', posy, 
        '--inputFaceNegY', negy, 
        '--inputFacePosZ', posz, 
        '--inputFaceNegZ', negz, 
        '--output0', output, 
        '--output0params', 
        'hdr,rgbe,latlong']
        
    else:
        envpipe = [cmft_path + '--inputFacePosX' + posx 
        + '--inputFaceNegX' + negx 
        + '--inputFacePosY' + posy 
        + '--inputFaceNegY' + negy 
        + '--inputFacePosZ' + posz 
        + '--inputFaceNegZ' + negz 
        + '--output0' + output 
        + '--output0params' + 'hdr,rgbe,latlong']

    subprocess.call(envpipe, shell=True)

    input2 = output + ".hdr"
    output2 = directory + "/" + "combined2"

    if arm.utils.get_os() == 'win':
        envpipe2 = [cmft_path, 
        '--input', input2, 
        '--filter', 'shcoeffs', 
        '--outputNum', '1', 
        '--output0', output2]
        
    else:
        envpipe2 = [cmft_path + 
        '--input' + input2
        + '-filter' + 'shcoeffs'
        + '--outputNum' + '1'
        + '--output0' + output2]
        
    subprocess.call(envpipe2, shell=True)

    for obj in bpy.data.objects:
        obj.select_set(False)

    cam_obj.select_set(True)
    bpy.ops.object.delete()
    bpy.context.scene.render.resolution_x = prevResx
    bpy.context.scene.render.resolution_y = prevResy
    bpy.context.scene.camera = prevCam
    bpy.context.scene.render.engine = prevEngine
            

def HDRLM_Build(self, context):

    scene = context.scene
    cycles = bpy.data.scenes[scene.name].cycles
    
    if not bpy.data.is_saved:
        self.report({'INFO'}, "Please save your file first")
        return{'FINISHED'}

    if scene.hdrlm_denoise_use:
        if scene.hdrlm_oidn_path == "":
            scriptDir = os.path.dirname(os.path.realpath(__file__))
            if os.path.isdir(os.path.join(scriptDir,"OIDN")):
                scene.hdrlm_oidn_path = os.path.join(scriptDir,"OIDN")
                if scene.hdrlm_oidn_path == "":
                    self.report({'INFO'}, "No denoise OIDN path assigned")
                    return{'FINISHED'}

    total_time = time()

    for obj in bpy.data.objects:
        if "_" in obj.name:
            obj.name = obj.name.replace("_",".")
        if " " in obj.name:
            obj.name = obj.name.replace(" ",".")
        if "[" in obj.name:
            obj.name = obj.name.replace("[",".")
        if "]" in obj.name:
            obj.name = obj.name.replace("]",".")
        # if len(obj.name) > 60:
        #         obj.name = "TooLongName"
        #         invalidNaming = True

        for slot in obj.material_slots:
            if "_" in slot.material.name:
                slot.material.name = slot.material.name.replace("_",".")
            if " " in slot.material.name:
                slot.material.name = slot.material.name.replace(" ",".")
            if "[" in slot.material.name:
                slot.material.name = slot.material.name.replace("[",".")
            if "[" in slot.material.name:
                slot.material.name = slot.material.name.replace("]",".")
            
            # if len(slot.material.name) > 60:
            #     slot.material.name = "TooLongName"
            #     invalidNaming = True

    # if(invalidNaming):
    #     self.report({'INFO'}, "Naming errors")
    #     return{'FINISHED'}

    prevCyclesSettings = [
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
        scene.render.engine
    ]

    cycles.device = scene.hdrlm_mode
    scene.render.engine = "CYCLES"
    
    if scene.hdrlm_quality == "Preview":
        cycles.samples = 32
        cycles.max_bounces = 1
        cycles.diffuse_bounces = 1
        cycles.glossy_bounces = 1
        cycles.transparent_max_bounces = 1
        cycles.transmission_bounces = 1
        cycles.volume_bounces = 1
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.hdrlm_quality == "Medium":
        cycles.samples = 64
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.hdrlm_quality == "High":
        cycles.samples = 256
        cycles.max_bounces = 128
        cycles.diffuse_bounces = 128
        cycles.glossy_bounces = 128
        cycles.transparent_max_bounces = 128
        cycles.transmission_bounces = 128
        cycles.volume_bounces = 128
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif scene.hdrlm_quality == "Production":
        cycles.samples = 512
        cycles.max_bounces = 256
        cycles.diffuse_bounces = 256
        cycles.glossy_bounces = 256
        cycles.transparent_max_bounces = 256
        cycles.transmission_bounces = 256
        cycles.volume_bounces = 256
        cycles.caustics_reflective = True
        cycles.caustics_refractive = True
    else:
        pass

    #Configure Lights
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            if obj.hdrlm_light_lightmap_use:
                if obj.hdrlm_light_casts_shadows:
                    bpy.data.lights[obj.name].cycles.cast_shadow = True
                else:
                    bpy.data.lights[obj.name].cycles.cast_shadow = False

                bpy.data.lights[obj.name].energy = bpy.data.lights[obj.name].energy * obj.hdrlm_light_intensity_scale

    #Configure World
    for obj in bpy.data.objects:
        pass

    bakeNum = 0
    currBakeNum = 0

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.hdrlm_mesh_lightmap_use:
                bakeNum = bakeNum + 1

    #Bake
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.hdrlm_mesh_lightmap_use:
                currBakeNum = currBakeNum + 1
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                obs = bpy.context.view_layer.objects
                active = obs.active

                if len(obj.material_slots) == 0:
                    single = False
                    number = 0
                    while single == False:
                        matname = obj.name + ".00" + str(number)
                        if matname in bpy.data.materials:
                            single = False
                            number = number + 1
                        else:
                            mat = bpy.data.materials.new(name=matname)
                            mat.use_nodes = True
                            obj.data.materials.append(mat)
                            single = True

                #if len(obj.material_sl) > 1:
                for slot in obj.material_slots:
                    mat = slot.material

                    if mat.users > 1:
                         copymat = mat.copy()
                         slot.material = copymat 

                # #Make sure there's one material available
                # if len(obj.material_slots) == 0:
                #     if not "MaterialDefault" in bpy.data.materials:
                #         mat = bpy.data.materials.new(name='MaterialDefault')
                #         mat.use_nodes = True
                #     else:
                #         mat = bpy.data.materials['MaterialDefault']
                #     obj.data.materials.append(mat)


                # --------- MATERIAL BACKUP


                if scene.hdrlm_caching_mode == "Copy":
                    for slot in obj.material_slots:
                        matname = slot.material.name
                        originalName = matname + "_Original"
                        hasOriginal = False
                        if originalName in bpy.data.materials:
                            hasOriginal = True
                        else:
                            hasOriginal = False

                        if hasOriginal:
                            backup_material_restore(slot)

                        #Copy materials
                        backup_material_copy(slot)
                else: #Cache blend
                    pass


                # --------- MATERIAL BACKUP END

                #Remove existing baked materials and images
                for mat in bpy.data.materials:
                    if mat.name.endswith('_baked'):
                        bpy.data.materials.remove(mat, do_unlink=True)
                for img in bpy.data.images:
                    if img.name == obj.name + "_baked":
                        bpy.data.images.remove(img, do_unlink=True)

                #Single user materials? ONLY ONE MATERIAL SLOT?...
                #Fint så langt
                ob = obj
                for slot in ob.material_slots:
                    # Temp material already exists
                    if slot.material.name.endswith('_temp'):
                        continue
                    n = slot.material.name + '_' + ob.name + '_temp'
                    if not n in bpy.data.materials:
                        slot.material = slot.material.copy()
                    slot.material.name = n
                #Fint så langt...

                #Add images for baking
                img_name = obj.name + '_baked'
                res = int(obj.hdrlm_mesh_lightmap_resolution) / int(scene.hdrlm_lightmap_scale)
                if img_name not in bpy.data.images or bpy.data.images[img_name].size[0] != res or bpy.data.images[img_name].size[1] != res:
                    img = bpy.data.images.new(img_name, res, res, alpha=False, float_buffer=True)
                    img.name = img_name
                else:
                    img = bpy.data.images[img_name]

                for slot in obj.material_slots:
                    mat = slot.material
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes

                    if "Baked Image" in nodes:
                        img_node = nodes["Baked Image"]
                    else:
                        img_node = nodes.new('ShaderNodeTexImage')
                        img_node.name = 'Baked Image'
                        img_node.location = (100, 100)
                        img_node.image = img
                    img_node.select = True
                    nodes.active = img_node

                if scene.hdrlm_apply_on_unwrap:
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                uv_layers = obj.data.uv_layers
                if not "UVMap_Lightmap" in uv_layers:
                    uvmap = uv_layers.new(name="UVMap_Lightmap")
                    uv_layers.active_index = len(uv_layers) - 1
                    if obj.hdrlm_mesh_lightmap_unwrap_mode == "Lightmap":
                        bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.hdrlm_mesh_unwrap_margin)
                    elif obj.hdrlm_mesh_lightmap_unwrap_mode == "Smart Project":
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(True)
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=obj.hdrlm_mesh_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
                    else:
                        pass
                else:
                    for i in range(0, len(uv_layers)):
                        if uv_layers[i].name == 'UVMap_Lightmap':
                            uv_layers.active_index = i
                            break

                for slot in obj.material_slots:

                    #ONLY 1 MATERIAL PER OBJECT SUPPORTED FOR NOW!
                    nodetree = slot.material.node_tree

                    #HER FEIL?
                    #bpy.context.active_object.active_material = slot.material

                    n = slot.material.name[:-5] + '_baked'
                    if not n in bpy.data.materials:
                        mat = bpy.data.materials.new(name=n)
                        mat.use_nodes = True
                        nodes = mat.node_tree.nodes
                        img_node = nodes.new('ShaderNodeTexImage')
                        img_node.name = "Baked Image"
                        img_node.location = (100, 100)
                        img_node.image = bpy.data.images[img_name]
                        mat.node_tree.links.new(img_node.outputs[0], nodes['Principled BSDF'].inputs[0])
                    else:
                        mat = bpy.data.materials[n]
                        nodes = mat.node_tree.nodes
                        nodes['Baked Image'].image = bpy.data.images[img_name]

                for slot in obj.material_slots:

                    nodetree = bpy.data.materials[slot.name].node_tree
                    nodes = nodetree.nodes
                    mainNode = nodetree.nodes[0].inputs[0].links[0].from_node

                    for n in nodes:
                        if "LM" in n.name:
                            nodetree.links.new(n.outputs[0], mainNode.inputs[0])

                    for n in nodes:
                        if "Lightmap" in n.name:
                                #print("Remove")
                                nodes.remove(n)

                print("Baking: " + bpy.context.view_layer.objects.active.name + " | " + str(currBakeNum) + " out of " + str(bakeNum))

                if scene.hdrlm_indirect_only:
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"INDIRECT"}, margin=scene.hdrlm_dilation_margin)
                else:
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=scene.hdrlm_dilation_margin)

    #Unlinked here?..
    for mat in bpy.data.materials:
        if mat.name.endswith('_baked'):
            has_user = False
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and mat.name.endswith('_' + obj.name + '_baked'):
                    has_user = True
                    break
            if not has_user:
                bpy.data.materials.remove(mat, do_unlink=True)

    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.hdrlm_lightmap_savedir)
    print("Checking for: " + dirpath)
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)

    #Save
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.hdrlm_mesh_lightmap_use:
                img_name = obj.name + '_baked'
                bakemap_path = os.path.join(dirpath, img_name)

                bpy.data.images[img_name].filepath_raw = bakemap_path + ".hdr"
                bpy.data.images[img_name].file_format = "HDR"
                bpy.data.images[img_name].save()

                #Denoise here
                if scene.hdrlm_denoise_use:

                    if scene.hdrlm_denoiser == "OIDN":

                        image = bpy.data.images[img_name]
                        width = image.size[0]
                        height = image.size[1]

                        image_output_array = np.zeros([width, height, 3], dtype="float32")
                        image_output_array = np.array(image.pixels)
                        image_output_array = image_output_array.reshape(height, width, 4)
                        image_output_array = np.float32(image_output_array[:,:,:3])

                        image_output_destination = bakemap_path + ".pfm"

                        with open(image_output_destination, "wb") as fileWritePFM:
                            save_pfm(fileWritePFM, image_output_array)

                        denoise_output_destination = bakemap_path + "_denoised.pfm"

                        Scene = context.scene

                        verbose = Scene.hdrlm_oidn_verbose
                        affinity = Scene.hdrlm_oidn_affinity

                        if verbose:
                            v = "3"
                        else:
                            v = "0"

                        if affinity:
                            a = "1"
                        else:
                            a = "0"

                        threads = str(Scene.hdrlm_oidn_threads)
                        maxmem = str(Scene.hdrlm_oidn_maxmem)

                        if platform.system() == 'Windows':
                            oidnPath = os.path.join(bpy.path.abspath(scene.hdrlm_oidn_path),"denoise-win.exe")
                            pipePath = [oidnPath, '-hdr', image_output_destination, '-o', denoise_output_destination, '-verbose', v, '-threads', threads, '-affinity', a, '-maxmem', maxmem]
                        elif platform.system() == 'Darwin':
                            oidnPath = os.path.join(bpy.path.abspath(scene.hdrlm_oidn_path),"denoise-osx")
                            pipePath = [oidnPath + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + n]
                        else:
                            oidnPath = os.path.join(bpy.path.abspath(scene.hdrlm_oidn_path),"denoise-linux")
                            pipePath = [oidnPath + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + n]
                            
                        if not verbose:
                            denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)
                        else:
                            denoisePipe = subprocess.Popen(pipePath, shell=True)

                        denoisePipe.communicate()[0]

                        with open(denoise_output_destination, "rb") as f:
                            denoise_data, scale = load_pfm(f)

                        ndata = np.array(denoise_data)
                        ndata2 = np.dstack( (ndata, np.ones((width,height)) )  )
                        img_array = ndata2.ravel()
                        bpy.data.images[image.name].pixels = img_array
                        bpy.data.images[image.name].filepath_raw = bakemap_path + "_denoised.hdr"
                        bpy.data.images[image.name].file_format = "HDR"
                        bpy.data.images[image.name].save()
                    
                    elif scene.hdrlm_denoiser == "Optix":

                        image_output_destination = bakemap_path + ".hdr"
                        denoise_output_destination = bakemap_path + "_denoised.hdr"

                        if platform.system() == 'Windows':
                            optixPath = os.path.join(bpy.path.abspath(scene.hdrlm_optix_path),"Denoiser.exe")
                            pipePath = [optixPath, '-i', image_output_destination, '-o', denoise_output_destination]
                        elif platform.system() == 'Darwin':
                            print("Mac for Optix is still unsupported")    
                        else:
                            print("Linux for Optix is still unsupported")

                        denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)

                        #if not verbose:
                        #    denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)
                        #else:
                        #    denoisePipe = subprocess.Popen(pipePath, shell=True)

                        denoisePipe.communicate()[0]

                    else:

                        print("FATAL ERROR: DENOISER CHOICE....")

                if scene.hdrlm_filtering_use:
                    if scene.hdrlm_denoise_use:
                        filter_file_input = img_name + "_denoised.hdr"
                    else:
                        filter_file_input = img_name + ".hdr"

                    if all([module_pip, module_opencv]):

                        filter_file_output = img_name + "_finalized.hdr"
                        os.chdir(os.path.dirname(bakemap_path))
                        opencv_process_image = cv2.imread(filter_file_input, -1)

                        if scene.hdrlm_filtering_mode == "Box":
                            if scene.hdrlm_filtering_box_strength % 2 == 0:
                                kernel_size = (scene.hdrlm_filtering_box_strength + 1,scene.hdrlm_filtering_box_strength + 1)
                            else:
                                kernel_size = (scene.hdrlm_filtering_box_strength,scene.hdrlm_filtering_box_strength)
                            opencv_bl_result = cv2.blur(opencv_process_image, kernel_size)
                            if scene.hdrlm_filtering_iterations > 1:
                                for x in range(scene.hdrlm_filtering_iterations):
                                    opencv_bl_result = cv2.blur(opencv_bl_result, kernel_size)

                        elif scene.hdrlm_filtering_mode == "Gaussian":
                            if scene.hdrlm_filtering_gaussian_strength % 2 == 0:
                                kernel_size = (scene.hdrlm_filtering_gaussian_strength + 1,scene.hdrlm_filtering_gaussian_strength + 1)
                            else:
                                kernel_size = (scene.hdrlm_filtering_gaussian_strength,scene.hdrlm_filtering_gaussian_strength)
                            sigma_size = 0
                            opencv_bl_result = cv2.GaussianBlur(opencv_process_image, kernel_size, sigma_size)
                            if scene.hdrlm_filtering_iterations > 1:
                                for x in range(scene.hdrlm_filtering_iterations):
                                    opencv_bl_result = cv2.GaussianBlur(opencv_bl_result, kernel_size, sigma_size)

                        elif scene.hdrlm_filtering_mode == "Bilateral":
                            diameter_size = scene.hdrlm_filtering_bilateral_diameter
                            sigma_color = scene.hdrlm_filtering_bilateral_color_deviation
                            sigma_space = scene.hdrlm_filtering_bilateral_coordinate_deviation
                            opencv_bl_result = cv2.bilateralFilter(opencv_process_image, diameter_size, sigma_color, sigma_space)
                            if scene.hdrlm_filtering_iterations > 1:
                                for x in range(scene.hdrlm_filtering_iterations):
                                    opencv_bl_result = cv2.bilateralFilter(opencv_bl_result, diameter_size, sigma_color, sigma_space)
                        else:

                            if scene.hdrlm_filtering_median_kernel % 2 == 0:
                                kernel_size = (scene.hdrlm_filtering_median_kernel + 1 , scene.hdrlm_filtering_median_kernel + 1)
                            else:
                                kernel_size = (scene.hdrlm_filtering_median_kernel, scene.hdrlm_filtering_median_kernel)

                            opencv_bl_result = cv2.medianBlur(opencv_process_image, kernel_size[0])
                            if scene.hdrlm_filtering_iterations > 1:
                                for x in range(scene.hdrlm_filtering_iterations):
                                    opencv_bl_result = cv2.medianBlur(opencv_bl_result, kernel_size[0])

                        cv2.imwrite(filter_file_output, opencv_bl_result)
                        
                        bpy.ops.image.open(filepath=os.path.join(os.path.dirname(bakemap_path),filter_file_output))
                        bpy.data.images[obj.name+"_baked"].name = obj.name + "_temp"
                        bpy.data.images[obj.name+"_baked_finalized.hdr"].name = obj.name + "_baked"
                        bpy.data.images.remove(bpy.data.images[obj.name+"_temp"])

                    else:
                       print("Modules missing...") 

                if scene.hdrlm_encoding_mode == "RGBM":
                    encodeImageRGBM(self, bpy.data.images[obj.name+"_baked"], 6.0, bakemap_path, scene.hdrlm_compression)
                    bpy.data.images[obj.name+"_baked"].name = obj.name + "_temp"
                    bpy.data.images[obj.name+"_baked_encoded"].name = obj.name + "_baked"
                    bpy.data.images.remove(bpy.data.images[obj.name+"_temp"])
                elif scene.hdrlm_encoding_mode == "RGBD":
                    encodeImageRGBD(self, bpy.data.images[obj.name+"_baked"], 6.0, bakemap_path, scene.hdrlm_compression)
                    bpy.data.images[obj.name+"_baked"].name = obj.name + "_temp"
                    bpy.data.images[obj.name+"_baked_encoded"].name = obj.name + "_baked"
                    bpy.data.images.remove(bpy.data.images[obj.name+"_temp"])

    #Apply and restore materials
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.hdrlm_mesh_lightmap_use:

                for slot in obj.material_slots:
                    mat = slot.material
                    if mat.name.endswith('_temp'):
                        old = slot.material
                        slot.material = bpy.data.materials[old.name.split('_' + obj.name)[0]]
                        bpy.data.materials.remove(old, do_unlink=True)

                uv_layers = obj.data.uv_layers
                uv_layers.active_index = 0

                for slot in obj.material_slots:

                    if(scene.hdrlm_encoding_armory_setup):
                        print("Setup Armory")

                    nodetree = bpy.data.materials[slot.name].node_tree

                    outputNode = nodetree.nodes[0]

                    mainNode = outputNode.inputs[0].links[0].from_node

                    if len(mainNode.inputs[0].links) == 0:
                        baseColorValue = mainNode.inputs[0].default_value
                        baseColorNode = nodetree.nodes.new(type="ShaderNodeRGB")
                        baseColorNode.outputs[0].default_value = baseColorValue
                        baseColorNode.location = ((mainNode.location[0]-500,mainNode.location[1]))
                        baseColorNode.name = "Lightmap_BasecolorNode_A"
                    else:
                        baseColorNode = mainNode.inputs[0].links[0].from_node
                        baseColorNode.name = "LM_P"

                    nodePos1 = mainNode.location
                    nodePos2 = baseColorNode.location

                    mixNode = nodetree.nodes.new(type="ShaderNodeMixRGB")
                    mixNode.name = "Lightmap_Multiplication"
                    mixNode.location = lerpNodePoints(self, nodePos1, nodePos2, 0.5)
                    if scene.hdrlm_indirect_only:
                        mixNode.blend_type = 'ADD'
                    else:
                        mixNode.blend_type = 'MULTIPLY'
                    
                    mixNode.inputs[0].default_value = 1.0

                    LightmapNode = nodetree.nodes.new(type="ShaderNodeTexImage")
                    LightmapNode.location = ((baseColorNode.location[0]-300,baseColorNode.location[1] + 300))
                    LightmapNode.image = bpy.data.images[obj.name + "_baked"]
                    LightmapNode.name = "Lightmap_Image"

                    UVLightmap = nodetree.nodes.new(type="ShaderNodeUVMap")
                    UVLightmap.uv_map = "UVMap_Lightmap"
                    UVLightmap.name = "Lightmap_UV"
                    UVLightmap.location = ((-1000, baseColorNode.location[1] + 300))

                    nodetree.links.new(baseColorNode.outputs[0], mixNode.inputs[1]) 
                    nodetree.links.new(LightmapNode.outputs[0], mixNode.inputs[2])
                    nodetree.links.new(mixNode.outputs[0], mainNode.inputs[0]) 
                    nodetree.links.new(UVLightmap.outputs[0], LightmapNode.inputs[0])

    #for mat in bpy.data.materials:
    #    for node in mat.node_tree.nodes:
    #        if node.type == "RGB":
    #            mat.node_tree.nodes.remove(node)
    
    for mat in bpy.data.materials:
        if mat.name.endswith('_baked'):
            bpy.data.materials.remove(mat, do_unlink=True)

    if not scene.hdrlm_keep_cache_files:
        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.hdrlm_lightmap_savedir)
        if os.path.isdir(dirpath):
            list = os.listdir(dirpath)
            for file in list:
                if file.endswith(".pfm"):
                    os.remove(os.path.join(dirpath,file))
                if file.endswith("denoised.hdr"):
                    os.remove(os.path.join(dirpath,file))

    #for img in bpy.data.images:
    #    if not img.users:
    #        bpy.data.images.remove(img)

        #pass

    #Post bake
    cycles.samples = prevCyclesSettings[0]
    cycles.max_bounces = prevCyclesSettings[1]
    cycles.diffuse_bounces = prevCyclesSettings[2]
    cycles.glossy_bounces = prevCyclesSettings[3]
    cycles.transparent_max_bounces = prevCyclesSettings[4]
    cycles.transmission_bounces = prevCyclesSettings[5]
    cycles.volume_bounces = prevCyclesSettings[6]
    cycles.caustics_reflective = prevCyclesSettings[7]
    cycles.caustics_refractive = prevCyclesSettings[8]
    cycles.device = prevCyclesSettings[9]
    scene.render.engine = prevCyclesSettings[10]

    for mat in bpy.data.materials:
        mat.update_tag()

    print("The whole ordeal took: %.3f s" % (time() - total_time))

    return{'FINISHED'}

def register():
    bpy.utils.register_class(HDRLM_EncodeToRGBM)
    bpy.utils.register_class(HDRLM_BuildAO)
    bpy.utils.register_class(HDRLM_BuildLighting)
    bpy.utils.register_class(HDRLM_BuildLightingSelected)
    bpy.utils.register_class(HDRLM_ToggleEnableforSelection)
    bpy.utils.register_class(HDRLM_ToggleDisableforSelection)
    bpy.utils.register_class(HDRLM_CleanLighting)
    bpy.utils.register_class(HDRLM_LightmapFolder)
    bpy.utils.register_class(HDRLM_PT_Panel)
    bpy.utils.register_class(HDRLM_PT_Unwrap)
    bpy.utils.register_class(HDRLM_PT_Denoise)
    bpy.utils.register_class(HDRLM_PT_Filtering)
    bpy.utils.register_class(HDRLM_PT_Encoding)
    bpy.utils.register_class(HDRLM_PT_Compression)
    bpy.utils.register_class(HDRLM_PT_Additional)
    bpy.utils.register_class(HDRLM_CreateWorldVolume)
    #bpy.utils.register_class(HDRLM_PT_LightmapList)
    bpy.utils.register_class(HDRLM_PT_MeshMenu)
    bpy.utils.register_class(HDRLM_PT_LightMenu)
    bpy.utils.register_class(HDRLM_InstallOpenCV)
    bpy.types.IMAGE_PT_image_properties.append(draw)

    bpy.types.Scene.hdrlm_quality = EnumProperty(
        items = [('Preview', 'Preview', 'TODO'),
                 ('Medium', 'Medium', 'TODO'),
                 ('High', 'High', 'TODO'),
                 ('Production', 'Production', 'TODO'),
                 ('Custom', 'Custom', 'TODO')],
                name = "Lightmapping Quality", description="TODO", default='Preview')
    bpy.types.Scene.hdrlm_lightmap_scale = EnumProperty(
        items = [('16', '1/16', 'TODO'),
                 ('8', '1/8', 'TODO'),
                 ('4', '1/4', 'TODO'),
                 ('2', '1/2', 'TODO'),
                 ('1', '1/1', 'TODO')],
                name = "Lightmap Resolution scale", description="TODO", default="1")
    bpy.types.Scene.hdrlm_lightmap_savedir = StringProperty(name="Lightmap Directory", description="TODO", default="Lightmaps", subtype="FILE_PATH")
    bpy.types.Scene.hdrlm_mode = EnumProperty(
        items = [('CPU', 'CPU', 'TODO'),
                 ('GPU', 'GPU', 'TODO')],
                name = "Device", description="TODO", default="CPU")
    bpy.types.Scene.hdrlm_apply_on_unwrap = BoolProperty(name="Apply scale", description="TODO", default=False)
    bpy.types.Scene.hdrlm_indirect_only = BoolProperty(name="Indirect Only", description="TODO", default=False)
    bpy.types.Scene.hdrlm_keep_cache_files = BoolProperty(name="Keep cache files", description="TODO", default=False)
    bpy.types.Scene.hdrlm_dilation_margin = IntProperty(name="Dilation margin", default=16, min=1, max=64, subtype='PIXEL')
    bpy.types.Scene.hdrlm_delete_cache = BoolProperty(name="Delete cache", description="TODO", default=True)
    bpy.types.Scene.hdrlm_denoise_use = BoolProperty(name="Enable denoising", description="TODO", default=False)
    bpy.types.Scene.hdrlm_oidn_path = StringProperty(name="OIDN Path", description="TODO", default="", subtype="FILE_PATH")
    bpy.types.Scene.hdrlm_oidn_verbose = BoolProperty(name="Verbose", description="TODO")
    bpy.types.Scene.hdrlm_oidn_threads = IntProperty(name="Threads", default=0, min=0, max=64, description="Amount of threads to use. Set to 0 for auto-detect.")
    bpy.types.Scene.hdrlm_oidn_maxmem = IntProperty(name="Tiling max Memory", default=0, min=512, max=32768, description="Use tiling for memory conservation. Set to 0 to disable tiling.")
    bpy.types.Scene.hdrlm_oidn_affinity = BoolProperty(name="Set Affinity", description="TODO")
    bpy.types.Scene.hdrlm_oidn_use_albedo = BoolProperty(name="Use albedo map", description="TODO")
    bpy.types.Scene.hdrlm_oidn_use_normal = BoolProperty(name="Use normal map", description="TODO")
    bpy.types.Scene.hdrlm_denoiser = EnumProperty(
        items = [('OIDN', 'OIDN', 'TODO.'),
                 ('Optix', 'Optix', 'TODO.')],
                name = "Denoiser", description="TODO", default='OIDN')
    bpy.types.Scene.hdrlm_optix_path = StringProperty(name="Optix Path", description="TODO", default="", subtype="FILE_PATH")
    bpy.types.Scene.hdrlm_filtering_use = BoolProperty(name="Enable filtering", description="TODO", default=False)
    #bpy.types.Scene.hdrlm_filtering_gimp_path = StringProperty(name="Gimp Path", description="TODO", default="", subtype="FILE_PATH")
    bpy.types.Scene.hdrlm_filtering_mode = EnumProperty(
        items = [('Box', 'Box', 'TODO'),
                 ('Gaussian', 'Gaussian', 'TODO'),
                 ('Bilateral', 'Bilateral', 'TODO'),
                 ('Median', 'Median', 'TODO')],
                name = "Filter", description="TODO", default='Gaussian')
    bpy.types.Scene.hdrlm_caching_mode = EnumProperty(
        items = [('Copy', 'Copy Material', 'TODO'),
                 ('Cache', 'Blend Cache', 'TODO')],
                name = "Caching mode", description="TODO", default='Copy')
    bpy.types.Scene.hdrlm_filtering_gaussian_strength = IntProperty(name="Gaussian Strength", default=3, min=1, max=50)
    bpy.types.Scene.hdrlm_filtering_iterations = IntProperty(name="Filter Iterations", default=1, min=1, max=50)
    bpy.types.Scene.hdrlm_filtering_box_strength = IntProperty(name="Box Strength", default=1, min=1, max=50)
    bpy.types.Scene.hdrlm_filtering_bilateral_diameter = IntProperty(name="Pixel diameter", default=3, min=1, max=50)
    bpy.types.Scene.hdrlm_filtering_bilateral_color_deviation = IntProperty(name="Color deviation", default=75, min=1, max=100)
    bpy.types.Scene.hdrlm_filtering_bilateral_coordinate_deviation = IntProperty(name="Color deviation", default=75, min=1, max=100)
    bpy.types.Scene.hdrlm_filtering_median_kernel = IntProperty(name="Median kernel", default=3, min=1, max=5)
    bpy.types.Scene.hdrlm_encoding_mode = EnumProperty(
        items = [('RGBM', 'RGBM', '8-bit HDR encoding. Good for compatibility, good for memory but has banding issues.'),
                 ('RGBD', 'RGBD', '8-bit HDR encoding. Same as RGBM, but better for highlights and stylized looks.'),
                 ('RGBE', 'RGBE', '32-bit HDR RGBE encoding. Best quality, but high memory usage and not compatible with all devices.')],
                name = "Encoding Mode", description="TODO", default='RGBE')
    bpy.types.Scene.hdrlm_encoding_range = IntProperty(name="Encoding range", description="Higher gives a larger HDR range, but also gives more banding.", default=6, min=1, max=10)
    bpy.types.Scene.hdrlm_encoding_armory_setup = BoolProperty(name="Use Armory decoder", description="TODO", default=True)
    bpy.types.Scene.hdrlm_encoding_colorspace = EnumProperty(
        items = [('XYZ', 'XYZ', 'TODO'),
                 ('sRGB', 'sRGB', 'TODO'),
                 ('Raw', 'Raw', 'TODO'),
                 ('Non-Color', 'Non-Color', 'TODO'),
                 ('Linear ACES', 'Linear ACES', 'TODO'),
                 ('Linear', 'Linear', 'TODO'),
                 ('Filmic Log', 'Filmic Log', 'TODO')],
                name = "Color Space", description="TODO", default='Linear')
    bpy.types.Scene.hdrlm_on_identical_mat = EnumProperty(
        items = [('Create', 'Create', 'TODO.'),
                 ('Share', 'Share', 'TODO.')],
                name = "On identical materials", description="TODO", default='Create')
    bpy.types.Scene.hdrlm_baking_mode = EnumProperty(
        items = [('Sequential', 'Sequential', 'TODO.'),
                 ('Invoked', 'Invoked', 'TODO.')],
                name = "On identical materials", description="TODO", default='Sequential')
    bpy.types.Scene.hdrlm_lightmap_mode = EnumProperty(
        items = [('Only Light', 'Only Light', 'TODO.'),
                 ('With Albedo', 'With Albedo', 'TODO.'),
                 ('Full', 'Full', 'TODO.')],
                name = "On identical materials", description="TODO", default='Full')
    bpy.types.Scene.hdrlm_compression = IntProperty(name="PNG Compression", description="0 = No compression. 100 = Maximum compression.", default=0, min=0, max=100)
    bpy.types.Object.hdrlm_mesh_lightmap_use = BoolProperty(name="Enable Lightmapping", description="TODO", default=False)
    bpy.types.Object.hdrlm_mesh_apply_after = BoolProperty(name="Apply after build", description="TODO", default=False)
    bpy.types.Object.hdrlm_mesh_emissive = BoolProperty(name="Include emissive light", description="TODO", default=False)
    bpy.types.Object.hdrlm_mesh_emissive_shadow = BoolProperty(name="Emissive casts shadows", description="TODO", default=False)
    bpy.types.Object.hdrlm_mesh_lightmap_resolution = EnumProperty(
        items = [('32', '32', 'TODO'),
                 ('64', '64', 'TODO'),
                 ('128', '128', 'TODO'),
                 ('256', '256', 'TODO'),
                 ('512', '512', 'TODO'),
                 ('1024', '1024', 'TODO'),
                 ('2048', '2048', 'TODO'),
                 ('4096', '4096', 'TODO'),
                 ('8192', '8192', 'TODO')],
                name = "Lightmap Resolution", description="TODO", default='256')
    bpy.types.Object.hdrlm_mesh_lightmap_unwrap_mode = EnumProperty(
        items = [('Lightmap', 'Lightmap', 'TODO'),
                 ('Smart Project', 'Smart Project', 'TODO'),
                 ('Copy Existing', 'Copy Existing', 'TODO')],
                name = "Unwrap Mode", description="TODO", default='Smart Project')
    bpy.types.Object.hdrlm_mesh_unwrap_margin = FloatProperty(name="Unwrap Margin", default=0.1, min=0.0, max=1.0, subtype='FACTOR')
    bpy.types.Object.hdrlm_mesh_bake_ao = BoolProperty(name="Bake AO", description="TODO", default=False)
    bpy.types.Object.hdrlm_light_lightmap_use = BoolProperty(name="Enable for Lightmapping", description="TODO", default=True)
    bpy.types.Object.hdrlm_light_type = EnumProperty(
        items = [('Static', 'Static', 'Static baked light with both indirect and direct. Hidden after baking.'),
                 ('Stationary', 'Stationary', 'Semi dynamic light. Indirect baked, but can be moved, change intensity and color.')],
                name = "Light Type", description="TODO", default='Static')
    bpy.types.Object.hdrlm_light_intensity_scale = FloatProperty(name="Intensity Scale", default=1.0, min=0.0, max=10.0, subtype='FACTOR')
    bpy.types.Object.hdrlm_light_casts_shadows = BoolProperty(name="Casts shadows", description="TODO", default=True)

def unregister():
    bpy.utils.unregister_class(HDRLM_EncodeToRGBM)
    bpy.utils.unregister_class(HDRLM_BuildAO)
    bpy.utils.unregister_class(HDRLM_BuildLighting)
    bpy.utils.unregister_class(HDRLM_BuildLightingSelected)
    bpy.utils.unregister_class(HDRLM_ToggleEnableforSelection)
    bpy.utils.unregister_class(HDRLM_ToggleDisableforSelection)
    bpy.utils.unregister_class(HDRLM_CleanLighting)
    bpy.utils.unregister_class(HDRLM_LightmapFolder)
    bpy.utils.unregister_class(HDRLM_PT_Panel)
    bpy.utils.unregister_class(HDRLM_PT_Unwrap)
    bpy.utils.unregister_class(HDRLM_PT_Denoise)
    bpy.utils.unregister_class(HDRLM_PT_Filtering)
    bpy.utils.unregister_class(HDRLM_PT_Encoding)
    bpy.utils.unregister_class(HDRLM_PT_Compression)
    bpy.utils.unregister_class(HDRLM_PT_Additional)
    bpy.utils.unregister_class(HDRLM_CreateWorldVolume)
    #bpy.utils.unregister_class(HDRLM_PT_LightmapList)
    bpy.utils.unregister_class(HDRLM_PT_MeshMenu)
    bpy.utils.unregister_class(HDRLM_PT_LightMenu)
    bpy.utils.unregister_class(HDRLM_InstallOpenCV)
    bpy.types.IMAGE_PT_image_properties.remove(draw)

if __name__ == "__main__":
    register()


#OPTION!:
#BAKE WITH ALBEDO
#BAKE WITH DESIGNATED MATERIAL

#Mesh name follows object name..
#
#import bpy
#
#for obj in bpy.data.objects:
#    obj.data.name = obj.name