import bpy
from bpy.props import *
from bpy.types import Menu, Panel

class TLM_PT_ObjectMenu(bpy.types.Panel):
    bl_label = "The Lightmapper"
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
            row.prop(obj.TLM_ObjectProperties, "tlm_mesh_lightmap_use")
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                #row = layout.row()
                #row.prop(obj, "tlm_mesh_apply_after")
                #row = layout.row()
                #row.prop(obj, "tlm_mesh_emissive")
                #row = layout.row()
                #row.prop(obj, "tlm_mesh_emissive_shadow")
                row = layout.row()
                row.prop(obj.TLM_ObjectProperties, "tlm_mesh_lightmap_unwrap_mode")
                row = layout.row()

                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Atlas Group":

                    if scene.TLM_AtlasList_index >= 0 and len(scene.TLM_AtlasList) > 0:
                        row = layout.row()
                        item = scene.TLM_AtlasList[scene.TLM_AtlasList_index]
                        row.prop_search(obj.TLM_ObjectProperties, "tlm_atlas_pointer", scene, "TLM_AtlasList", text='Atlas Group')
                    else:
                        row = layout.label(text="Add Atlas Groups from the scene lightmapping settings.")

                else:

                    row.prop(obj.TLM_ObjectProperties, "tlm_mesh_lightmap_resolution")
                    row = layout.row()
                            #ADD ERROR CHECKING HERE! (ELSE)

                    row = layout.row()
                    row.prop(obj.TLM_ObjectProperties, "tlm_mesh_unwrap_margin")
                    row = layout.row()
                    row.prop(obj.TLM_ObjectProperties, "tlm_mesh_bake_ao")

                if not scene.TLM_SceneProperties.tlm_directional_mode == "None":

                    for slot in obj.material_slots:
                        nodetree = slot.material.node_tree
                        outputNode = nodetree.nodes[0]

                        if(outputNode.type != "OUTPUT_MATERIAL"):
                            for node in nodetree.nodes:
                                if node.type == "OUTPUT_MATERIAL":
                                    outputNode = node
                                    break

                        mainNode = outputNode.inputs[0].links[0].from_node

                        if len(mainNode.inputs[20].links) > 0:
                            if mainNode.inputs[20].links[0].from_node.type == "NORMAL_MAP":
                                NormalMap = mainNode.inputs[19].links[0].from_node
                                if NormalMap.inputs[1].links[0].from_node.type == "TEX_IMAGE":
                                    NormalMapTex = NormalMap.inputs[1].links[0].from_node.image
                                    if NormalMapTex.size[0] > int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution):
                                        row = layout.label(text="A connected normal map is larger than lightmap resolution")
                                    if NormalMapTex.size[0] < int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution):
                                        row = layout.label(text="A connected normal map is smaller than lightmap resolution")

