import bpy, time
from bpy.props import *

class TLM_BuildLightmaps(bpy.types.Operator):
    """Builds the lightmaps"""
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        backup_original(bpy.data.materials["Material"].node_tree, self)
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

def get_override(area_type):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        
        for area in screen.areas:
            if area.type == area_type:
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'window': window,
                                    'screen': screen,
                                    'area': area,
                                    'region': region,
                                    'blend_data': bpy.context.blend_data,
                                    'scene' : bpy.context.scene}
                        
                        if (area_type == 'VIEW_3D'):
                            if bpy.context.object != None:
                                override.update({'object': bpy.context.object})
                            if bpy.context.active_object != None:
                                override.update({'active_object': bpy.context.active_object})
                        
                        return override

def backup_original(nodetree, self):
    currentctx = bpy.context.area.type
    #currentspc = bpy.context.area.spaces.active.tree_type
    
    bpy.context.area.type = "NODE_EDITOR"
    bpy.context.area.spaces.active.tree_type = 'ShaderNodeTree'
    bpy.context.space_data.show_region_ui = False
    bpy.context.space_data.show_region_toolbar = False
    
    for node in nodetree.nodes:
        if node.name == "Material Output":
            node.select = False
        else:
            node.select = True
            
    SurfacePointNode = None
    DisplacementPointNode = None
            
    if(len(nodetree.nodes["Material Output"].inputs[0].links) > 0):
        SurfacePointNode = nodetree.nodes["Material Output"].inputs[0].links[0].from_node.name
    if(len(nodetree.nodes["Material Output"].inputs[2].links) > 0):
        DisplacementPointNode = nodetree.nodes["Material Output"].inputs[2].links[0].from_node.name

    bpy.ops.node.clipboard_copy(get_override('NODE_EDITOR'))
    bpy.ops.node.clipboard_paste(get_override('NODE_EDITOR'))
    
    for node in nodetree.nodes:
        if node.select == True:
            locx = node.location[0] - 9999
            locy = node.location[1] - 9999
            node.location = ((locx,locy))
            
    matname = bpy.context.active_object.active_material.name
    bpy.ops.node.group_make(get_override('NODE_EDITOR'))
    nodetree.nodes[-1].name = matname + "_Original"
    nodetree.nodes[-1].label = matname + "_Original"
    
    if SurfacePointNode is not None:
        nodetree.nodes[-1]["SPN"] = SurfacePointNode
    else:
        print("WARNING: Main output has no connection")
        print("DESIGNATE OUTPUT NODE FROM SELECTION!")
        
    if DisplacementPointNode is not None:
        nodetree.nodes[-1]["DPN"] = DisplacementPointNode
    
    bpy.ops.node.group_edit(get_override('NODE_EDITOR'))
    
    bpy.context.area.type = currentctx
    
def restore_original(nodetree):
    currentctx = bpy.context.area.type

    bpy.context.area.type = "NODE_EDITOR"
    bpy.context.area.spaces.active.tree_type = 'ShaderNodeTree'
    
    matname = bpy.context.active_object.active_material.name
    nodename = matname + "_Original"
    if nodename not in nodetree.nodes:
        print("Not found")
    else:
        print("Found")
        
        for node in nodetree.nodes:
            if node.name == nodename:
                node.select = False
            elif node.name == "Material Output":
                node.select = False
            else:
                node.select = True
        bpy.ops.node.delete()
        
        for node in nodetree.nodes:
            if node.name == nodename:
                node.select = True
            else:
                node.select = False
                
        for node in nodetree.nodes:
            if node.select == True:
                locx = node.location[0] + 9999
                locy = node.location[1] + 9999
                node.location = ((locx,locy))
                
        node = nodetree.nodes[nodename]
        
        SurfacePointNode = None
        DisplacementPointNode = None
        
        if node.get("SPN", None) is not None:
            SurfacePointNode = node["SPN"]
            print("SPN Found")
        if node.get("DPN", None) is not None:
            DisplacementPointNode = node["DPN"]
            print("DPN Found")
            
        bpy.ops.node.group_ungroup()
        exNode = nodetree.nodes.get(nodename,None)
        if exNode is not None:
            nodetree.nodes.remove(exNode)
            
        outNode = nodetree.nodes["Material Output"]

        if SurfacePointNode is not None:
            if not SurfacePointNode[-3:].isdigit():
                SurfacePointNode = SurfacePointNode + ".001" 
            else:
                Prefix = SurfacePointNode[:-3]
                Postfix = str(int(SurfacePointNode[-3:])+1).zfill(3)
                SurfacePointNode = Prefix + Postfix
            SPN = nodetree.nodes[SurfacePointNode]
            nodetree.links.new(SPN.outputs[0], outNode.inputs[0])
            print(SPN.name)
            
        if DisplacementPointNode is not None:
            if not DisplacementPointNode[-3:].isdigit():
                DisplacementPointNode = DisplacementPointNode + ".001"
            else:
                Prefix = DisplacementPointNode[:-3]
                Postfix = str(int(DisplacementPointNode[-3:])+1).zfill(3)
                DisplacementPointNode = Prefix + Postfix
            DPN = nodetree.nodes[DisplacementPointNode]
            nodetree.links.new(DPN.outputs[0], outNode.inputs[0])
        
    bpy.context.area.type = currentctx
