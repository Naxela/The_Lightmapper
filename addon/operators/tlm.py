import bpy, os, time, blf, webbrowser, platform
from .. utility import build
from .. utility.cycles import cache
from .. network import server

class TLM_BuildLightmaps(bpy.types.Operator):
    bl_idname = "tlm.build_lightmaps"
    bl_label = "Build Lightmaps"
    bl_description = "Build Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):

        #Add progress bar from 0.15

        print("MODAL")

        return {'PASS_THROUGH'}

    def invoke(self, context, event):

        if not bpy.app.background:

            build.prepare_build(self, False)

        else:

            print("Running in background mode. Contextual operator not available. Use command 'thelightmapper.addon.build.prepare_build()'")

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        pass

    def draw_callback_px(self, context, event):
        pass

class TLM_CleanLightmaps(bpy.types.Operator):
    bl_idname = "tlm.clean_lightmaps"
    bl_label = "Clean Lightmaps"
    bl_description = "Clean Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_EngineProperties.tlm_lightmap_savedir)
        if os.path.isdir(dirpath):
            for file in os.listdir(dirpath):
                os.remove(os.path.join(dirpath + "/" + file))

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    cache.backup_material_restore(obj)

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    cache.backup_material_rename(obj)

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

        return {'FINISHED'}

class TLM_ExploreLightmaps(bpy.types.Operator):
    bl_idname = "tlm.explore_lightmaps"
    bl_label = "Explore Lightmaps"
    bl_description = "Explore Lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        cycles = scene.cycles

        if not bpy.data.is_saved:
            self.report({'INFO'}, "Please save your file first")
            return {"CANCELLED"}

        filepath = bpy.data.filepath
        dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_EngineProperties.tlm_lightmap_savedir)
        
        if platform.system() != "Linux":

            if os.path.isdir(dirpath):
                webbrowser.open('file://' + dirpath)
            else:
                os.mkdir(dirpath)
                webbrowser.open('file://' + dirpath)
        else:

            if os.path.isdir(dirpath):
                os.system('xdg-open "%s"' % dirpath)
                #webbrowser.open('file://' + dirpath)
            else:
                os.mkdir(dirpath)
                os.system('xdg-open "%s"' % dirpath)
                #webbrowser.open('file://' + dirpath)

        return {'FINISHED'}

class TLM_EnableSelection(bpy.types.Operator):
    """Enable for selection"""
    bl_idname = "tlm.enable_selection"
    bl_label = "Enable for selection"
    bl_description = "Enable for selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        for obj in bpy.context.selected_objects:
            obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = True

            if scene.TLM_SceneProperties.tlm_override_object_settings:
                obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = scene.TLM_SceneProperties.tlm_mesh_lightmap_resolution
                obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode = scene.TLM_SceneProperties.tlm_mesh_lightmap_unwrap_mode
                obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin = scene.TLM_SceneProperties.tlm_mesh_unwrap_margin
                obj.TLM_ObjectProperties.tlm_postpack_object = scene.TLM_SceneProperties.tlm_postpack_object

                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroupA":
                    obj.TLM_ObjectProperties.tlm_atlas_pointer = scene.TLM_SceneProperties.tlm_atlas_pointer

                obj.TLM_ObjectProperties.tlm_postatlas_pointer = scene.TLM_SceneProperties.tlm_postatlas_pointer

        return{'FINISHED'}

class TLM_DisableSelection(bpy.types.Operator):
    """Disable for selection"""
    bl_idname = "tlm.disable_selection"
    bl_label = "Disable for selection"
    bl_description = "Disable for selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        for obj in bpy.context.selected_objects:
            obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = False

        return{'FINISHED'}

class TLM_RemoveLightmapUV(bpy.types.Operator):
    """Remove Lightmap UV for selection"""
    bl_idname = "tlm.remove_uv_selection"
    bl_label = "Remove Lightmap UV"
    bl_description = "Remove Lightmap UV for selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                uv_layers = obj.data.uv_layers

                for uvlayer in uv_layers:
                    if uvlayer.name == "UVMap_Lightmap":
                        uv_layers.remove(uvlayer)

        return{'FINISHED'}

class TLM_SelectLightmapped(bpy.types.Operator):
    """Select all objects for lightmapping"""
    bl_idname = "tlm.select_lightmapped_objects"
    bl_label = "Select lightmap objects"
    bl_description = "Remove Lightmap UV for selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                    obj.select_set(True)

        return{'FINISHED'}

class TLM_AtlasListNewItem(bpy.types.Operator):
    # Add a new item to the list
    bl_idname = "tlm_atlaslist.new_item"
    bl_label = "Add a new item"
    bl_description = "Create a new AtlasGroup"

    def execute(self, context):
        scene = context.scene
        scene.TLM_AtlasList.add()
        scene.TLM_AtlasListItem = len(scene.TLM_AtlasList) - 1

        scene.TLM_AtlasList[len(scene.TLM_AtlasList) - 1].name = "AtlasGroup"

        return{'FINISHED'}

class TLM_PostAtlasListNewItem(bpy.types.Operator):
    # Add a new item to the list
    bl_idname = "tlm_postatlaslist.new_item"
    bl_label = "Add a new item"
    bl_description = "Create a new AtlasGroup"
    bl_description = ""

    def execute(self, context):
        scene = context.scene
        scene.TLM_PostAtlasList.add()
        scene.TLM_PostAtlasListItem = len(scene.TLM_PostAtlasList) - 1

        scene.TLM_PostAtlasList[len(scene.TLM_PostAtlasList) - 1].name = "AtlasGroup"

        return{'FINISHED'}

class TLM_AtlastListDeleteItem(bpy.types.Operator):
    # Delete the selected item from the list
    bl_idname = "tlm_atlaslist.delete_item"
    bl_label = "Deletes an item"
    bl_description = "Delete an AtlasGroup"

    @classmethod
    def poll(self, context):
        """ Enable if there's something in the list """
        scene = context.scene
        return len(scene.TLM_AtlasList) > 0

    def execute(self, context):
        scene = context.scene
        list = scene.TLM_AtlasList
        index = scene.TLM_AtlasListItem

        for obj in bpy.data.objects:

            atlasName = scene.TLM_AtlasList[index].name

            if obj.TLM_ObjectProperties.tlm_atlas_pointer == atlasName:
                obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode = "SmartProject"

        list.remove(index)

        if index > 0:
            index = index - 1

        scene.TLM_AtlasListItem = index
        return{'FINISHED'}

class TLM_PostAtlastListDeleteItem(bpy.types.Operator):
    # Delete the selected item from the list
    bl_idname = "tlm_postatlaslist.delete_item"
    bl_label = "Deletes an item"
    bl_description = "Delete an AtlasGroup"

    @classmethod
    def poll(self, context):
        """ Enable if there's something in the list """
        scene = context.scene
        return len(scene.TLM_PostAtlasList) > 0

    def execute(self, context):
        scene = context.scene
        list = scene.TLM_PostAtlasList
        index = scene.TLM_PostAtlasListItem

        for obj in bpy.data.objects:

            atlasName = scene.TLM_PostAtlasList[index].name

            if obj.TLM_ObjectProperties.tlm_atlas_pointer == atlasName:
                obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode = "SmartProject"

        list.remove(index)

        if index > 0:
            index = index - 1

        scene.TLM_PostAtlasListItem = index
        return{'FINISHED'}

class TLM_AtlasListMoveItem(bpy.types.Operator):
    # Move an item in the list
    bl_idname = "tlm_atlaslist.move_item"
    bl_label = "Move an item in the list"
    bl_description = "Move an item in the list"
    direction: bpy.props.EnumProperty(
                items=(
                    ('UP', 'Up', ""),
                    ('DOWN', 'Down', ""),))

    def move_index(self):
        # Move index of an item render queue while clamping it
        scene = context.scene
        index = scene.TLM_AtlasListItem
        list_length = len(scene.TLM_AtlasList) - 1
        new_index = 0

        if self.direction == 'UP':
            new_index = index - 1
        elif self.direction == 'DOWN':
            new_index = index + 1

        new_index = max(0, min(new_index, list_length))
        scene.TLM_AtlasList.move(index, new_index)
        scene.TLM_AtlasListItem = new_index

    def execute(self, context):
        scene = context.scene
        list = scene.TLM_AtlasList
        index = scene.TLM_AtlasListItem

        if self.direction == 'DOWN':
            neighbor = index + 1
            self.move_index()

        elif self.direction == 'UP':
            neighbor = index - 1
            self.move_index()
        else:
            return{'CANCELLED'}
        return{'FINISHED'}

class TLM_PostAtlasListMoveItem(bpy.types.Operator):
    # Move an item in the list
    bl_idname = "tlm_postatlaslist.move_item"
    bl_label = "Move an item in the list"
    bl_description = "Move an item in the list"
    direction: bpy.props.EnumProperty(
                items=(
                    ('UP', 'Up', ""),
                    ('DOWN', 'Down', ""),))

    def move_index(self):
        # Move index of an item render queue while clamping it
        scene = context.scene
        index = scene.TLM_PostAtlasListItem
        list_length = len(scene.TLM_PostAtlasList) - 1
        new_index = 0

        if self.direction == 'UP':
            new_index = index - 1
        elif self.direction == 'DOWN':
            new_index = index + 1

        new_index = max(0, min(new_index, list_length))
        scene.TLM_PostAtlasList.move(index, new_index)
        scene.TLM_PostAtlasListItem = new_index

    def execute(self, context):
        scene = context.scene
        list = scene.TLM_PostAtlasList
        index = scene.TLM_PostAtlasListItem

        if self.direction == 'DOWN':
            neighbor = index + 1
            self.move_index()

        elif self.direction == 'UP':
            neighbor = index - 1
            self.move_index()
        else:
            return{'CANCELLED'}
        return{'FINISHED'}

class TLM_StartServer(bpy.types.Operator):
    bl_idname = "tlm.start_server"
    bl_label = "Start Network Server"
    bl_description = "Start Network Server"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):

        #Add progress bar from 0.15

        print("MODAL")

        return {'PASS_THROUGH'}

    def invoke(self, context, event):

        server.startServer()

        return {'RUNNING_MODAL'}