import arm.utils
import arm.assets
import os
import shutil
import bpy
import subprocess
from bpy.types import Menu, Panel, UIList
from bpy.props import *
import numpy as np
import math

class ArmBakeListItem(bpy.types.PropertyGroup):
    obj: PointerProperty(type=bpy.types.Object, description="The object to bake")
    res_x: IntProperty(name="X", description="Texture resolution", default=1024)
    res_y: IntProperty(name="Y", description="Texture resolution", default=1024)
    object_name: StringProperty(name="Name", description="", default="") # TODO: deprecated

class ArmBakeList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # We could write some code to decide which icon to use here...
        custom_icon = 'OBJECT_DATAMODE'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(item, "obj", text="", emboss=False, icon=custom_icon)
            col = row.column()
            col.alignment = 'RIGHT'
            col.label(text=str(item.res_x) + 'x' + str(item.res_y))

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)

class ArmBakeListNewItem(bpy.types.Operator):
    # Add a new item to the list
    bl_idname = "arm_bakelist.new_item"
    bl_label = "Add a new item"

    def execute(self, context):
        scn = context.scene
        scn.arm_bakelist.add()
        scn.arm_bakelist_index = len(scn.arm_bakelist) - 1
        return{'FINISHED'}


class ArmBakeListDeleteItem(bpy.types.Operator):
    # Delete the selected item from the list
    bl_idname = "arm_bakelist.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(self, context):
        """ Enable if there's something in the list """
        scn = context.scene
        return len(scn.arm_bakelist) > 0

    def execute(self, context):
        scn = context.scene
        list = scn.arm_bakelist
        index = scn.arm_bakelist_index

        list.remove(index)

        if index > 0:
            index = index - 1

        scn.arm_bakelist_index = index
        return{'FINISHED'}

class ArmBakeListMoveItem(bpy.types.Operator):
    # Move an item in the list
    bl_idname = "arm_bakelist.move_item"
    bl_label = "Move an item in the list"
    direction: EnumProperty(
                items=(
                    ('UP', 'Up', ""),
                    ('DOWN', 'Down', ""),))

    def move_index(self):
        # Move index of an item render queue while clamping it
        obj = bpy.context.scene
        index = obj.arm_bakelist_index
        list_length = len(obj.arm_bakelist) - 1
        new_index = 0

        if self.direction == 'UP':
            new_index = index - 1
        elif self.direction == 'DOWN':
            new_index = index + 1

        new_index = max(0, min(new_index, list_length))
        obj.arm_bakelist.move(index, new_index)
        obj.arm_bakelist_index = new_index

    def execute(self, context):
        obj = bpy.context.scene
        list = obj.arm_bakelist
        index = obj.arm_bakelist_index

        if self.direction == 'DOWN':
            neighbor = index + 1
            self.move_index()

        elif self.direction == 'UP':
            neighbor = index - 1
            self.move_index()
        else:
            return{'CANCELLED'}
        return{'FINISHED'}

class ArmBakeButton(bpy.types.Operator):
    '''Bake textures for listed objects'''
    bl_idname = 'arm.bake_textures'
    bl_label = 'Bake'

    def execute(self, context):
        scn = context.scene
        if len(scn.arm_bakelist) == 0:
            return{'FINISHED'}

        self.report({'INFO'}, "Once baked, hit 'Armory Bake - Apply' to pack lightmaps")

        # At least one material required for now..
        for o in scn.arm_bakelist:
            ob = o.obj
            if len(ob.material_slots) == 0:
                if not 'MaterialDefault' in bpy.data.materials:
                    mat = bpy.data.materials.new(name='MaterialDefault')
                    mat.use_nodes = True
                else:
                    mat = bpy.data.materials['MaterialDefault']
                ob.data.materials.append(mat)

        # Single user materials
        for o in scn.arm_bakelist:
            ob = o.obj
            for slot in ob.material_slots:
                # Temp material already exists
                if slot.material.name.endswith('_temp'):
                    continue
                n = slot.material.name + '_' + ob.name + '_temp'
                if not n in bpy.data.materials:
                    slot.material = slot.material.copy()
                    slot.material.name = n

        # Images for baking
        for o in scn.arm_bakelist:
            ob = o.obj
            img_name = ob.name + '_baked'
            sc = scn.arm_bakelist_scale / 100
            rx = o.res_x * sc
            ry = o.res_y * sc
            # Get image
            if img_name not in bpy.data.images or bpy.data.images[img_name].size[0] != rx or bpy.data.images[img_name].size[1] != ry:
                if scn.arm_bakelist_type == "Lightmap":
                    img = bpy.data.images.new(img_name, rx, ry, alpha=False, float_buffer=True)
                else:
                    img = bpy.data.images.new(img_name, rx, ry)
                img.name = img_name # Force img_name (in case Blender picked img_name.001)
            else:
                img = bpy.data.images[img_name]
            for slot in ob.material_slots:
                # Add image nodes
                mat = slot.material
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                if 'Baked Image' in nodes:
                    img_node = nodes['Baked Image']
                else:
                    img_node = nodes.new('ShaderNodeTexImage')
                    img_node.name = 'Baked Image'
                    img_node.location = (100, 100)
                    img_node.image = img
                img_node.select = True
                nodes.active = img_node
        
        obs = bpy.context.view_layer.objects

        # Unwrap
        active = obs.active
        for o in scn.arm_bakelist:
            ob = o.obj
            uv_layers = ob.data.uv_layers
            if not 'UVMap_baked' in uv_layers:
                uvmap = uv_layers.new(name='UVMap_baked')
                uv_layers.active_index = len(uv_layers) - 1
                obs.active = ob
                if scn.arm_bakelist_unwrap == 'Lightmap Pack':
                    bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES')
                else:
                    bpy.ops.object.select_all(action='DESELECT')
                    ob.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    #bpy.ops.uv.smart_project(45, scn.arm_bakelist_margin, 1.0, True, False)
                    bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=scn.arm_bakelist_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
            else:
                for i in range(0, len(uv_layers)):
                    if uv_layers[i].name == 'UVMap_baked':
                        uv_layers.active_index = i
                        break
        obs.active = active

        # Materials for runtime
        # TODO: use single mat per object
        for o in scn.arm_bakelist:
            ob = o.obj
            img_name = ob.name + '_baked'
            for slot in ob.material_slots:
                n = slot.material.name[:-5] + '_baked'
                if not n in bpy.data.materials:
                    mat = bpy.data.materials.new(name=n)
                    mat.use_nodes = True
                    mat.use_fake_user = True
                    nodes = mat.node_tree.nodes
                    img_node = nodes.new('ShaderNodeTexImage')
                    img_node.name = 'Baked Image'
                    img_node.location = (100, 100)
                    img_node.image = bpy.data.images[img_name]
                    mat.node_tree.links.new(img_node.outputs[0], nodes['Principled BSDF'].inputs[0])
                else:
                    mat = bpy.data.materials[n]
                    nodes = mat.node_tree.nodes
                    nodes['Baked Image'].image = bpy.data.images[img_name]

        # Bake
        bpy.ops.object.select_all(action='DESELECT')
        for o in scn.arm_bakelist:
            o.obj.select_set(True)
        obs.active = scn.arm_bakelist[0].obj

        if scn.arm_bakelist_type == "Lightmap":
            bpy.ops.object.bake('INVOKE_DEFAULT', type='DIFFUSE', pass_filter={"DIRECT", "INDIRECT"}, margin=4)
        else:
            bpy.ops.object.bake('INVOKE_DEFAULT', type='COMBINED')

        bpy.ops.object.select_all(action='DESELECT')

        return{'FINISHED'}

class ArmBakeApplyButton(bpy.types.Operator):
    '''Pack baked textures, denoise and restore materials'''
    bl_idname = 'arm.bake_apply'
    bl_label = 'Apply'

    def lerpNodePoints(self, a, b, c):
        return (a + c * (b - a))

    def lin2srgb(lin):
        if lin > 0.0031308:
            s = 1.055 * (pow(lin, (1.0 / 2.4))) - 0.055
        else:
            s = 12.92 * lin
        return s

    def saturate(self, num, floats=True):
        if num < 0:
            num = 0
        elif num > (1 if floats else 255):
            num = (1 if floats else 255)
        return num

    def execute(self, context):
        scn = context.scene
        if len(scn.arm_bakelist) == 0:
            return{'FINISHED'}
        # Remove leftover _baked materials for removed objects
        for mat in bpy.data.materials:
            if mat.name.endswith('_baked'):
                has_user = False
                for ob in bpy.data.objects:
                    if ob.type == 'MESH' and mat.name.endswith('_' + ob.name + '_baked'):
                        has_user = True
                        break
                if not has_user:
                    bpy.data.materials.remove(mat, do_unlink=True)
        # Recache lightmaps
        arm.assets.invalidate_unpacked_data(None, None)
        for o in scn.arm_bakelist:
            ob = o.obj
            img_name = ob.name + '_baked'
            # Save images

            if scn.arm_bakelist_save == "Save":

                if arm.utils.get_fp() == "":
                    self.report({'INFO'}, "Please save your file first")
                    return{'FINISHED'}

                if not os.path.isdir(arm.utils.get_fp() + "\\Bakedmaps"):
                    os.mkdir(arm.utils.get_fp() + "\\Bakedmaps")

                bakemap_path = arm.utils.get_fp() +  '\\' + 'Bakedmaps' + '\\' + img_name

                if scn.arm_bakelist_type == "Lightmap":
                    print("Writing: " + bakemap_path + ".exr")
                    bpy.data.images[img_name].filepath_raw = bakemap_path + ".exr"
                    bpy.data.images[img_name].file_format = "OPEN_EXR"
                    bpy.data.images[img_name].save()
                    print("Saved image: " + bakemap_path + ".exr")
                else:
                    print("Writing image: " + bakemap_path + ".exr")
                    bpy.data.images[img_name].filepath_raw = bakemap_path + ".png"
                    bpy.data.images[img_name].file_format = "PNG"
                    bpy.data.images[img_name].save()
                    print("Saved image: " + bakemap_path + ".png")

                # Convert to PFM

                if scn.arm_bakelist_denoise:

                    image = bpy.data.images[img_name]
                    width = image.size[0]
                    height = image.size[1]

                    print("Setting array")
                    #Todo - Linear to SRGB color conversion for combined maps
                    image_output_array = np.zeros([width, height, 3], dtype="float32")
                    image_output_array = np.array(image.pixels)
                    image_output_array = image_output_array.reshape(height, width, 4)
                    image_output_array = np.float32(image_output_array[:,:,:3])

                    #TOOOOOO SLOW! For debugging only
                    # for x in range(width):
                    #     for y in range(height):
                            
                    #         print("x: " + str(x) + "| y: " + str(y))

                    #         target = [y, x]

                    #         index = (target[1] * width + target[0]) * 4

                    #         pixel = [
                    #             image.pixels[index],
                    #             image.pixels[index + 1],
                    #             image.pixels[index + 2],
                    #             image.pixels[index + 3]
                    #         ]

                    #         image_output_array[y][x] = [pixel[0], pixel[1], pixel[2]]

                    #print("Denoising: C")
                    #ar_rotations = 3
                    #image_output_array = np.rot90(image_output_array, ar_rotations)

                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    # REMEMBER TO CHECK FOR THE FOLLOWING!!!
                    # IF MATERIAL NAMES HAS UNDERSCORES _ IN THE NAME, IT BREAKS THE SCRIPT

                    image_output_destination = bakemap_path + ".pfm" 

                    print("Writing PFM: " + image.name + ".pfm | Resolution: " + str(width) + " x " + str(height) + " px")
                    with open(image_output_destination, "wb") as fileWritePFM:
                        arm.utils.save_pfm(fileWritePFM, image_output_array)
                    print("PFM File exported: " + image.name + ".pfm")

                    print("Denoising file...")
                    if arm.utils.denoise_file(bakemap_path):
                        print("File denoised: " + bakemap_path + ".pfm")

                    print("Loading file back")
                    image_denoised_input_destination = bakemap_path + "_denoised.pfm" 
                    #denoised_img = bpy.data.images.new(image.name+"_denoised", width, height, alpha=False, float_buffer=True)

                    with open(image_denoised_input_destination, "rb") as f:
                        denoise_data, scale = arm.utils.load_pfm(f)

                    ndata = np.array(denoise_data)
                    ndata2 = np.dstack( (ndata, np.ones((width,height)) )  )
                    img_array = ndata2.ravel()
                    bpy.data.images[image.name].pixels = img_array

                    #Encode it to RGBM or RGBD

                    if scn.arm_bakelist_encoding == "RGBM":
                        
                        #encode_cache = bpy.data.images[image.name]

                        #sima = context.space_data
                        # Image
                        ima = bpy.data.images[image.name]
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
                            result_pixel[i+3] = self.saturate(max(result_pixel[i], result_pixel[i+1], result_pixel[i+2], 1e-6))
                            result_pixel[i+3] = math.ceil(result_pixel[i+3] * 255.0) / 255.0
                            for j in range(3):
                                result_pixel[i+j] /= result_pixel[i+3]
                        
                        target_ima.pixels = result_pixel
                        
                        ima = target_ima

                    else:
                        pass
            else:
                print("Packing images")
                bpy.data.images[img_name].pack(as_png=True)
                bpy.data.images[img_name].save()

            for slot in ob.material_slots:
                mat = slot.material
                # Remove temp material
                if mat.name.endswith('_temp'):
                    old = slot.material
                    slot.material = bpy.data.materials[old.name.split('_' + ob.name)[0]]
                    bpy.data.materials.remove(old, do_unlink=True)

        # Convert to RGBM/RGBD
        #for o in scn.arm_bakelist:

            

        #Restore uv slots
        for o in scn.arm_bakelist:
            ob = o.obj
            uv_layers = ob.data.uv_layers
            uv_layers.active_index = 0

        #Add the lightmaps to the materials
        for o in scn.arm_bakelist:
            ob = o.obj
            
            for m in ob.material_slots:

                #Todo! IF NO BASECOLOR EXISTS
                #MAKE SOME EXCEPTION!
                
                
                #Need to check if the lightmaps haven't already been setup
                
                nodetree = bpy.data.materials[m.name].node_tree

                #Get the material output node
                OutputNode = nodetree.nodes[0]

                #Get the connected node (usually either principled bsdf or armory)
                mainNode = OutputNode.inputs[0].links[0].from_node

                #We check if a lightmap setup already exists
                for n in nodetree.nodes:

                    a,b,c = False, False, False

                    prefix = "Lightmap_"
                    if n.name == prefix + "Image":
                        a = True
                    if n.name == prefix + "Multiplication":
                        b = True
                    if n.name == prefix + "UV":
                        c = True

                if a == False and b == False and c == False :

                    #Get the base color node after checking
                    if len(mainNode.inputs[0].links) == 0:
                        baseColorValue = mainNode.inputs[0].default_value
                        baseColorNode = nodetree.nodes.new(type="ShaderNodeRGB")
                        baseColorNode.outputs[0].default_value = baseColorValue
                        baseColorNode.location = ((mainNode.location[0]-500,mainNode.location[1]))
                        baseColorNode.name = "Lightmap_BasecolorNode"
                    else:
                        baseColorNode = mainNode.inputs[0].links[0].from_node
                        baseColorNode.name = "Lightmap_BasecolorNode"

                    #Interpolate between these nodes and add a mix RGB node set to multiply

                    #Todo! - Make sure reroutes are respected, currently it breaks I think
                    
                    nodePos1 = mainNode.location
                    nodePos2 = baseColorNode.location

                    mixNode = nodetree.nodes.new(type="ShaderNodeMixRGB")
                    mixNode.name = "Lightmap_Multiplication"
                    mixNode.location = self.lerpNodePoints(nodePos1, nodePos2, 0.5)
                    mixNode.blend_type = 'MULTIPLY'
                    mixNode.inputs[0].default_value = 1.0

                    #Unlink mainNode and baseColorNode
                    for l in nodetree.links:
                        if l.from_node == baseColorNode:
                            if l.to_node == mainNode:
                                nodetree.links.remove(l)

                    #Connect baseColor and MixRGB
                    nodetree.links.new(baseColorNode.outputs[0], mixNode.inputs[1])
                    #Connect MixRGB and principled
                    nodetree.links.new(mixNode.outputs[0], mainNode.inputs[0]) 

                    #Add another image texture node above
                    LightmapNode = nodetree.nodes.new(type="ShaderNodeTexImage")
                    LightmapNode.location = ((baseColorNode.location[0]-300,baseColorNode.location[1] + 300))
                    LightmapNode.image = bpy.data.images[ob.name + "_baked_RGBM.png"]
                    LightmapNode.name = "Lightmap_Image"

                    #Add the Decode RGBM
                    DecodeNode = nodetree.nodes.new(type="ShaderNodeGroup")
                    DecodeNode.node_tree = bpy.data.node_groups["RGBM Decode"]
                    DecodeNode.location = self.lerpNodePoints(LightmapNode.location, mixNode.location, 0.5)

                    nodetree.links.new(LightmapNode.outputs[0], DecodeNode.inputs[0])
                    nodetree.links.new(LightmapNode.outputs[1], DecodeNode.inputs[1])
                    nodetree.links.new(DecodeNode.outputs[0], mixNode.inputs[2])
                    
                    #Add a uv map behind and set it to -1
                    UVLightmap = nodetree.nodes.new(type="ShaderNodeUVMap")
                    UVLightmap.location = ((LightmapNode.location[0] - 400, LightmapNode.location[1]))
                    UVLightmap.uv_map = "UVMap_baked"
                    UVLightmap.name = "Lightmap_UV"

                    nodetree.links.new(UVLightmap.outputs[0], LightmapNode.inputs[0])

                else:

                    pass

        return{'FINISHED'}

class ArmBakeCleanButton(bpy.types.Operator):
    '''Clean baked textures folder and reset textures'''
    bl_idname = 'arm.bake_clean'
    bl_label = 'Clean'

    def execute(self, context):

        scn = context.scene
        
        if os.path.isdir(arm.utils.get_fp() + "\\BakedMaps"):
            shutil.rmtree(arm.utils.get_fp() + "\\Bakedmaps")

        for o in scn.arm_bakelist:
            ob = o.obj
            
            for m in ob.material_slots:

                #Todo! IF NO BASECOLOR EXISTS
                #MAKE SOME EXCEPTION!
                
                #Need to check if the lightmaps haven't already been setup
                
                nodetree = bpy.data.materials[m.name].node_tree

                #Get the material output node
                OutputNode = nodetree.nodes[0]

                #Get the connected node (usually either principled bsdf or armory)
                mainNode = OutputNode.inputs[0].links[0].from_node

                hasPreviousBasecolor = False

                for n in nodetree.nodes:

                    prefix = "Lightmap_"
                    if n.name == prefix + "Image":
                        print("Remove: " + str(n) + prefix + "Image")
                        nodetree.nodes.remove(nodetree.nodes[n.name])

                    if n.name == prefix + "Multiplication":
                        print("Remove: " + str(n) + prefix + "Multiplication")
                        nodetree.nodes.remove(nodetree.nodes[n.name])

                    if n.name == prefix + "UV":
                        print("Remove: " + str(n) + prefix + "UV")
                        nodetree.nodes.remove(nodetree.nodes[n.name])

                    if n.name == prefix + "BasecolorNode":
                        hasPreviousBasecolor = True

                if hasPreviousBasecolor:
                    nodetree.links.new(mainNode.inputs[0], nodetree.nodes[prefix+"BasecolorNode"].outputs[0])
                

        return{'FINISHED'}

class ArmBakeSpecialsMenu(bpy.types.Menu):
    bl_label = "Bake"
    bl_idname = "arm_bakelist_specials"

    def draw(self, context):
        layout = self.layout
        layout.operator("arm.bake_add_all")
        layout.operator("arm.bake_add_selected")
        layout.operator("arm.bake_clear_all")
        layout.operator("arm.bake_remove_baked_materials")

class ArmBakeAddAllButton(bpy.types.Operator):
    '''Fill the list with scene objects'''
    bl_idname = 'arm.bake_add_all'
    bl_label = 'Add All'

    def execute(self, context):
        scn = context.scene
        scn.arm_bakelist.clear()
        for ob in scn.objects:
            if ob.type == 'MESH':
                scn.arm_bakelist.add().obj = ob
        return{'FINISHED'}

class ArmBakeAddSelectedButton(bpy.types.Operator):
    '''Add selected objects to the list'''
    bl_idname = 'arm.bake_add_selected'
    bl_label = 'Add Selected'

    def contains(self, scn, ob):
        for o in scn.arm_bakelist:
            if o == ob:
                return True
        return False

    def execute(self, context):
        scn = context.scene
        for ob in context.selected_objects:
            if ob.type == 'MESH' and not self.contains(scn, ob):
                scn.arm_bakelist.add().obj = ob
        return{'FINISHED'}

class ArmBakeClearAllButton(bpy.types.Operator):
    '''Clear the list'''
    bl_idname = 'arm.bake_clear_all'
    bl_label = 'Clear'

    def execute(self, context):
        #print(os.getcwd())
        #gimpPath = "C:/Program Files/GIMP 2/bin/gimp-2.10.exe"
        #subprocess.call([gimpPath + ])
        scn = context.scene
        scn.arm_bakelist.clear()
        return{'FINISHED'}

class ArmBakeRemoveBakedMaterialsButton(bpy.types.Operator):
    '''Clear the list'''
    bl_idname = 'arm.bake_remove_baked_materials'
    bl_label = 'Remove Baked Materials'

    def execute(self, context):
        for mat in bpy.data.materials:
            if mat.name.endswith('_baked'):
                bpy.data.materials.remove(mat, do_unlink=True)
        return{'FINISHED'}

def register():
    bpy.utils.register_class(ArmBakeListItem)
    bpy.utils.register_class(ArmBakeList)
    bpy.utils.register_class(ArmBakeListNewItem)
    bpy.utils.register_class(ArmBakeListDeleteItem)
    bpy.utils.register_class(ArmBakeListMoveItem)
    bpy.utils.register_class(ArmBakeButton)
    bpy.utils.register_class(ArmBakeApplyButton)
    bpy.utils.register_class(ArmBakeCleanButton)
    bpy.utils.register_class(ArmBakeSpecialsMenu)
    bpy.utils.register_class(ArmBakeAddAllButton)
    bpy.utils.register_class(ArmBakeAddSelectedButton)
    bpy.utils.register_class(ArmBakeClearAllButton)
    bpy.utils.register_class(ArmBakeRemoveBakedMaterialsButton)
    bpy.types.Scene.arm_bakelist_scale = FloatProperty(name="Resolution", description="Resolution scale", default=100.0, min=1, max=1000, soft_min=1, soft_max=100.0, subtype='PERCENTAGE')
    bpy.types.Scene.arm_bakelist_margin = FloatProperty(name="UV Margin", description="UV Island Margin", default=0.0, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
    bpy.types.Scene.arm_bakelist = CollectionProperty(type=ArmBakeListItem)
    bpy.types.Scene.arm_bakelist_index = IntProperty(name="Index for my_list", default=0)
    bpy.types.Scene.arm_bakelist_unwrap = EnumProperty(
        items = [('Lightmap Pack', 'Lightmap Pack', 'Lightmap Pack'),
                 ('Smart UV Project', 'Smart UV Project', 'Smart UV Project')],
        name = "UV Unwrap", default='Smart UV Project')
    bpy.types.Scene.arm_bakelist_type = EnumProperty(
        items = [('Lightmap', 'Lightmap', 'Lightmap'),
                 ('Combined Map', 'Combined Map', 'Combined Map')],
        name = "Bake Type", default='Combined Map')
    bpy.types.Scene.arm_bakelist_encoding = EnumProperty(
        items = [('RGBD', 'RGBD', 'RGBD'),
                 ('RGBM', 'RGBM', 'RGBM')],
        name = "Encoding Scheme", default='RGBM')
    bpy.types.Scene.arm_bakelist_save = EnumProperty(
        items = [('Save', 'Save', 'Save'),
                 ('Pack', 'Pack', 'Pack')],
        name = "Save or pack on apply", default='Save')

    bpy.types.Scene.arm_bakelist_filtering = EnumProperty(
        items = [('Gaussian', 'Gaussian', 'Gaussian'),
                 ('Selective Gaussian', 'Selective Gaussian', 'Selective Gaussian')],
        name = "Lightmap Filtering", default='Gaussian')
    bpy.types.Scene.arm_bakelist_filtering_gauss_mode = EnumProperty(
        items = [('Light', 'Light', 'Light'), #1.0
                 ('Easy', 'Easy', 'Easy'), #2.0
                 ('Medium', 'Medium', 'Medium'), #4.0
                 ('Hard', 'Hard', 'Hard'), #8.0
                 ('Aggressive', 'Aggressive', 'Aggressive')], #16.0
        name = "Gaussian filter strength", default='Medium')
    bpy.types.Scene.arm_bakelist_filtering_selective_gauss_blur_radius = FloatProperty(name="Blur Radius", description="Selective Gaussian Blur Radius", default=15.0, min=100.0, max=1.0)
    bpy.types.Scene.arm_bakelist_filtering_selective_gauss_blur_delta = FloatProperty(name="Max Delta", description="Threshold value for selection filter", default=1.0, min=1.0, max=0.0)
    bpy.types.Scene.arm_bakelist_filtering_despeckle = BoolProperty(name="Despeckle Filter", description="Despeckle filter", default=False) #Adaptive / Radius: 1 / BlackLvl: -1 / WhiteLvl: 256

    bpy.types.Scene.arm_bakelist_direct = BoolProperty(name="Direct Contribution", description="Direct Contribution", default=True)
    bpy.types.Scene.arm_bakelist_indirect = BoolProperty(name="Indirect Contribution", description="Indirect Contribution", default=True)
    bpy.types.Scene.arm_bakelist_color = BoolProperty(name="Color Contribution", description="Color Contribution", default=False)
    bpy.types.Scene.arm_bakelist_denoise = BoolProperty(name="Denoise", description="Denoise baked maps", default=True)

def unregister():
    bpy.utils.unregister_class(ArmBakeListItem)
    bpy.utils.unregister_class(ArmBakeList)
    bpy.utils.unregister_class(ArmBakeListNewItem)
    bpy.utils.unregister_class(ArmBakeListDeleteItem)
    bpy.utils.unregister_class(ArmBakeListMoveItem)
    bpy.utils.unregister_class(ArmBakeButton)
    bpy.utils.unregister_class(ArmBakeApplyButton)
    bpy.utils.unregister_class(ArmBakeCleanButton)
    bpy.utils.unregister_class(ArmBakeSpecialsMenu)
    bpy.utils.unregister_class(ArmBakeAddAllButton)
    bpy.utils.unregister_class(ArmBakeAddSelectedButton)
    bpy.utils.unregister_class(ArmBakeClearAllButton)
    bpy.utils.unregister_class(ArmBakeRemoveBakedMaterialsButton)
