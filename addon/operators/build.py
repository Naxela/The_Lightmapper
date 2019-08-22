import bpy
from time import time
from bpy.props import *

class TLM_BuildLightmaps(bpy.types.Operator):
    """Builds the lightmaps"""
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    stored_settings_cycles = []

    def setUVLayer(self, obj):
        uv_layers = obj.data.uv_layers
        if not "UVMap_Lightmap" in uv_layers:
            uvmap = uv_layers.new(name="UVMap_Lightmap")
            uv_layers.active_index = len(uv_layers) - 1
            if obj.tlm_mesh_lightmap_unwrap_mode == "Lightmap":
                bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.tlm_mesh_unwrap_margin)
            elif obj.tlm_mesh_lightmap_unwrap_mode == "Smart Project":
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=obj.tlm_mesh_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
            else:
                pass
        else:
            for i in range(0, len(uv_layers)):
                if uv_layers[i].name == 'UVMap_Lightmap':
                    uv_layers.active_index = i
                    break

    def applyScale(self, obj):
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    def createBakeImages(self, obj):
        img_name = obj.name + '_baked'
        res = int(obj.tlm_mesh_lightmap_resolution) / int(scene.tlm_lightmap_scale)
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

    def makeTemp(self, obj):
        for slot in obj.material_slots:
            if slot.material.name.endswith('_temp'):
                continue
            n = slot.material.name + '_' + obj.name + '_temp'
            if not n in bpy.data.materials:
                slot.material = slot.material.copy()
            slot.material.name = n

    def ensure_material(self, obj):
        if len(obj.material_slots) == 0:
            if not "MaterialDefault" in bpy.data.materials:
                mat = bpy.data.materials.new(name='MaterialDefault')
                mat.use_nodes = True
            else:
                mat = bpy.data.materials['MaterialDefault']
            obj.data.materials.append(mat)

    def remove_baked_elements(self, obj):
        for mat in bpy.data.materials:
            if mat.name.endswith('_baked'):
                bpy.data.materials.remove(mat, do_unlink=True)
        for img in bpy.data.images:
            if img.name == obj.name + "_baked":
                bpy.data.images.remove(img, do_unlink=True)

    def backup_material_copy(self, slot):
        material = slot.material
        dup = material.copy()
        dup.name = material.name + "_Original"
        dup.use_fake_user = True

    def backup_material_restore(self, slot):
        material = slot.material
        original = bpy.data.materials[material.name + "_Original"]
        slot.material = original
        material.name = material.name + "_temp"
        original.name = original.name[:-9]
        original.use_fake_user = False
        material.user_clear()
        bpy.data.materials.remove(material)

    def configureObjects(self, scene, context):
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.tlm_mesh_lightmap_use:

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                    obs = bpy.context.view_layer.objects
                    active = obs.active

                    for slot in obj.material_slots:
                        matname = slot.material.name
                        originalName = matname + "_Original"
                        hasOriginal = False
                        if originalName in bpy.data.materials:
                            hasOriginal = True
                        else:
                            hasOriginal = False

                        if hasOriginal:
                            self.backup_material_restore(slot)

                        #Copy materials
                        self.backup_material_copy(slot)

                    self.remove_baked_elements(obj)
                    self.ensure_material(obj)

                    self.makeTemp(obj)
                    
                    self.createBakeImages(obj)

                    if scene.tlm_apply_on_unwrap:
                        self.applyScale(obj)

                    self.setUVLayer(obj)

                    for slot in obj.material_slots:

                        #ONLY 1 MATERIAL PER OBJECT SUPPORTED FOR NOW!
                        nodetree = slot.material.node_tree
                        bpy.context.active_object.active_material = slot.material

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
                                    nodes.remove(n)

                print("Baking: " + bpy.context.view_layer.objects.active.name)

                if scene.tlm_indirect_only:
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"INDIRECT"}, margin=scene.tlm_dilation_margin)
                else:
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT","INDIRECT"}, margin=scene.tlm_dilation_margin)

    def configureWorld(self):
        for obj in bpy.data.objects:
            pass

    def configureLights(self):
        for obj in bpy.data.objects:
            if obj.type == "LIGHT":
                if obj.tlm_light_lightmap_use:
                    if obj.tlm_light_casts_shadows:
                        bpy.data.lights[obj.name].cycles.cast_shadow = True
                    else:
                        bpy.data.lights[obj.name].cycles.cast_shadow = False

                    bpy.data.lights[obj.name].energy = bpy.data.lights[obj.name].energy * obj.tlm_light_intensity_scale

    def setCyclesSettings(self, scene, cycles):

        if scene.tlm_quality == "Preview":
            cycles.samples = 32
            cycles.max_bounces = 1
            cycles.diffuse_bounces = 1
            cycles.glossy_bounces = 1
            cycles.transparent_max_bounces = 1
            cycles.transmission_bounces = 1
            cycles.volume_bounces = 1
            cycles.caustics_reflective = False
            cycles.caustics_refractive = False
        elif scene.tlm_quality == "Medium":
            cycles.samples = 64
            cycles.max_bounces = 2
            cycles.diffuse_bounces = 2
            cycles.glossy_bounces = 2
            cycles.transparent_max_bounces = 2
            cycles.transmission_bounces = 2
            cycles.volume_bounces = 2
            cycles.caustics_reflective = False
            cycles.caustics_refractive = False
        elif scene.tlm_quality == "High":
            cycles.samples = 256
            cycles.max_bounces = 128
            cycles.diffuse_bounces = 128
            cycles.glossy_bounces = 128
            cycles.transparent_max_bounces = 128
            cycles.transmission_bounces = 128
            cycles.volume_bounces = 128
            cycles.caustics_reflective = False
            cycles.caustics_refractive = False
        elif scene.tlm_quality == "Production":
            cycles.samples = 512
            cycles.max_bounces = 128
            cycles.diffuse_bounces = 128
            cycles.glossy_bounces = 128
            cycles.transparent_max_bounces = 128
            cycles.transmission_bounces = 128
            cycles.volume_bounces = 128
            cycles.caustics_reflective = True
            cycles.caustics_refractive = True
        else:
            pass

        return True

    def store_settings(self, cycles, scene):
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

        self.stored_settings_cycles = prevCyclesSettings

        return True

    def pre_process_check(self, context): #TODO UTILITY FUNCTION

        scene = context.scene

        if not bpy.data.is_saved:
            return [0,0]

        if scene.tlm_denoise_use:
            if scene.tlm_oidn_path == "":
                scriptDir = os.path.dirname(os.path.realpath(__file__))
                if os.path.isdir(os.path.join(scriptDir,"OIDN")):
                    scene.tlm_oidn_path = os.path.join(scriptDir,"OIDN")
                    if scene.tlm_oidn_path == "":
                        return [0,1]

        name_change = False

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.hdrlm_mesh_lightmap_use:
                    for obj in bpy.data.objects:
                        if "_" in obj.name:
                            obj.name = obj.name.replace("_",".")
                            name_change = True
                        if " " in obj.name:
                            obj.name = obj.name.replace(" ",".")
                            name_change = True
                        if "[" in obj.name:
                            obj.name = obj.name.replace("[",".")
                            name_change = True
                        if "]" in obj.name:
                            obj.name = obj.name.replace("]",".")
                            name_change = True

                        for slot in obj.material_slots:
                            if "_" in slot.material.name:
                                slot.material.name = slot.material.name.replace("_",".")
                                name_change = True
                            if " " in slot.material.name:
                                slot.material.name = slot.material.name.replace(" ",".")
                                name_change = True
                            if "[" in slot.material.name:
                                slot.material.name = slot.material.name.replace("[",".")
                                name_change = True
                            if "[" in slot.material.name:
                                slot.material.name = slot.material.name.replace("]",".")
                                name_change = True
            
            if name_change:
                return [0,2]
                        
        return [1,0]

    def execute(self, context):

        print("Baking...")

        total_time = time()

        scene = context.scene
        cycles = bpy.data.scenes[scene.name].cycles

        ppc_status = self.pre_process_check(context)
        if not ppc_status[0]:
            if ppc_status[1] == 0:
                self.report({'INFO'}, "Please save your file first")
                return{'FINISHED'}
            if ppc_status[1] == 1:
                self.report({'INFO'}, "Denoising enabled, but no OIDN binaries found...")
                return{'FINISHED'}
            if ppc_status[1] == 2:
                self.report({'INFO'}, "Unsupported character in lightmap object. Character changed to supported . (dot)")
            else:
                self.report({'INFO'}, "TLM: Unknown error catch - Continuing...")

        self.store_settings(cycles, scene)

        cycles.device = scene.tlm_mode
        scene.render.engine = "CYCLES"

        self.setCyclesSettings(scene, cycles)
        self.configureLights()

        self.configureObjects(scene, context)







        #backup_original(bpy.data.materials["Material"].node_tree, self)


        return {'FINISHED'}

def HDRLM_Build(self, context):

    total_time = time()

    scene = context.scene
    cycles = bpy.data.scenes[scene.name].cycles

    if not bpy.data.is_saved:
        self.report({'INFO'}, "Please save your file first")
        return{'FINISHED'}

    if scene.tlm_denoise_use:
        if scene.tlm_oidn_path == "":
            scriptDir = os.path.dirname(os.path.realpath(__file__))
            if os.path.isdir(os.path.join(scriptDir,"OIDN")):
                scene.tlm_oidn_path = os.path.join(scriptDir,"OIDN")
                if scene.tlm_oidn_path == "":
                    self.report({'INFO'}, "No denoise OIDN path assigned")
                    return{'FINISHED'}