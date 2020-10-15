import bpy, os, math

from bpy.types import Menu, Operator, Panel, UIList

from bpy.props import (
	StringProperty,
	BoolProperty,
	IntProperty,
	FloatProperty,
	FloatVectorProperty,
	EnumProperty,
	PointerProperty,
)

class TLM_PT_Imagetools(bpy.types.Panel):
    bl_label = "TLM Imagetools"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = 'UI'
    bl_category = "TLM Imagetools"

    def draw_header(self, _):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text ="TexTools")

    def draw(self, context):
        layout = self.layout

        activeImg = None

        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                activeImg = area.spaces.active.image

        if activeImg is not None and activeImg.name != "Render Result" and activeImg.name != "Viewer Node":
                print(activeImg)
                row = layout.row(align=True)
                row.operator("tlm.image_upscale")
                row = layout.row(align=True)
                row.operator("tlm.image_downscale")
                row = layout.row(align=True)
                row.label(text ="Method")
                row = layout.row(align=True)
                row.label(text ="If hdr: Exposure")
                row = layout.row(align=True)
                row.label(text ="Select an image")
                row = layout.row(align=True)
                row.label(text ="ORM Combine")
                row = layout.row(align=True)
                row.label(text ="Filter image")
                row = layout.row(align=True)
                row.label(text ="Denoise image")
                row = layout.row(align=True)
                row.label(text ="Adjust exposure")
        else:
            row = layout.row(align=True)
            row.label(text ="Select an image")