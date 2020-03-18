import bpy, os, shutil
from .. Utility import utility
from bpy.props import *

class TLM_AtlasListNewItem(bpy.types.Operator):
    # Add a new item to the list
    bl_idname = "tlm_atlaslist.new_item"
    bl_label = "Add a new item"
    bl_description = ""

    def execute(self, context):
        scene = context.scene
        scene.TLM_AtlasList.add()
        scene.TLM_AtlasList_index = len(scene.TLM_AtlasList) - 1

        scene.TLM_AtlasList[len(scene.TLM_AtlasList) - 1].name = "Atlas Group"

        return{'FINISHED'}

class TLM_AtlastListDeleteItem(bpy.types.Operator):
    # Delete the selected item from the list
    bl_idname = "tlm_atlaslist.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(self, context):
        """ Enable if there's something in the list """
        scene = context.scene
        return len(scene.TLM_AtlasList) > 0

    def execute(self, context):
        scene = context.scene
        list = scene.TLM_AtlasList
        index = scene.TLM_AtlasList_index

        list.remove(index)

        if index > 0:
            index = index - 1

        scene.TLM_AtlasList_index = index
        return{'FINISHED'}

class TLM_AtlasListMoveItem(bpy.types.Operator):
    # Move an item in the list
    bl_idname = "tlm_atlaslist.move_item"
    bl_label = "Move an item in the list"
    direction: EnumProperty(
                items=(
                    ('UP', 'Up', ""),
                    ('DOWN', 'Down', ""),))

    def move_index(self):
        # Move index of an item render queue while clamping it
        scene = context.scene
        index = scene.TLM_AtlasList_index
        list_length = len(scene.TLM_AtlasList) - 1
        new_index = 0

        if self.direction == 'UP':
            new_index = index - 1
        elif self.direction == 'DOWN':
            new_index = index + 1

        new_index = max(0, min(new_index, list_length))
        scene.TLM_AtlasList.move(index, new_index)
        scene.TLM_AtlasList_index = new_index

    def execute(self, context):
        scene = context.scene
        list = scene.TLM_AtlasList
        index = scene.TLM_AtlasList_index

        if self.direction == 'DOWN':
            neighbor = index + 1
            self.move_index()

        elif self.direction == 'UP':
            neighbor = index - 1
            self.move_index()
        else:
            return{'CANCELLED'}
        return{'FINISHED'}