import bpy, math, os
from bpy.app.handlers import persistent

def Log2(x): 
    if x == 0: 
        return False
    return (math.log10(x) / math.log10(2))
  
def isPowerOfTwo(n): 
    return (math.ceil(Log2(n)) == math.floor(Log2(n)))

class TLM_Downsize(bpy.types.Operator):
    """Downsize the current image by two"""
    bl_idname = "image.downsize"
    bl_label = "Downsize"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.type == 'IMAGE_EDITOR'

    def execute(self, context):
        print("Downsize")

        #Check if saved
        sima = context.space_data
        ima = sima.image
        ima_path = ima.filepath_raw

        if ima_path == "":
            self.report({'INFO'}, "Please save the image first")
            return {'FINISHED'}

        if not isPowerOfTwo(ima.size[0]):
            self.report({'INFO'}, "Only power of two supported")
            return {'FINISHED'}

        ext = ima_path[-4:]
        base = ima_path[:-4]

        sizeList = ["_x32","_x64","_x128","_x256","_x512","_x1024","_x2048","_x4096","_8192"]

        endScale = ""

        for size in sizeList:
            if base.endswith(size):
                endScale = size

        stock = False

        opencv_process_image = cv2.imread(ima_path, -1)
        width = int(ima.size[0] /2)
        height = int(ima.size[1] /2)

        if len(endScale) > 0:
            slice = 4 + len(endScale)
            filter_file_output = ima_path[:-slice] + "_x" + str(width) + ext
        else:
            stock = True
            filter_file_output = ima_path[:-4] + "_x" + str(width) + ext

        dim = (width, height)

        if bpy.context.scene.tlm_image_interpolation == "INTER_LINEAR":
            interp = cv2.INTER_LINEAR
        elif bpy.context.scene.tlm_image_interpolation == "INTER_NEAREST":
            interp = cv2.INTER_NEAREST
        elif bpy.context.scene.tlm_image_interpolation == "INTER_AREA":
            interp = cv2.INTER_AREA
        elif bpy.context.scene.tlm_image_interpolation == "INTER_CUBIC":
            interp = cv2.INTER_CUBIC
        elif bpy.context.scene.tlm_image_interpolation == "INTER_LANCZOS4":
            interp = cv2.INTER_LANCZOS4

        opencv_bl_result = cv2.resize(opencv_process_image, dim, interpolation = interp)
        cv2.imwrite(filter_file_output, opencv_bl_result)

        if stock:
            os.rename(ima_path, ima_path[:-4] + "_x" + str(width * 2) + ext)

        bpy.ops.image.open(filepath=filter_file_output)

        return {'FINISHED'}

class TLM_Upsize(bpy.types.Operator):
    """Upsize the current image by two"""
    bl_idname = "image.upsize"
    bl_label = "Upsize"
    bl_description = "TODO"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sima = context.space_data
    
        ima = sima.image
        ima_path = ima.filepath_raw

        if ima_path == "":
            self.report({'INFO'}, "Please save the image first")
            return {'FINISHED'}

        ext = ima_path[-4:] # .jpg
        base = ima_path[:-4] # abc_x512

        sizeList = ["_x32","_x64","_x128","_x256","_x512","_x1024","_x2048","_x4096","_8192"]

        endScale = ""

        for size in sizeList:
            if base.endswith(size):
                endScale = size

        file = ""

        if endScale == "":
            stock = True
        else:
            stock = False
            slice = len(endScale)
            ground = base[:-slice]
            current = sizeList.index(endScale)
            file = ground + sizeList[current + 1] + ext

        if os.path.exists(file) and not stock:
            return sima.type == 'IMAGE_EDITOR'

    def execute(self, context):

        sima = context.space_data
        ima = sima.image
        ima_path = ima.filepath_raw

        if ima_path == "":
            self.report({'INFO'}, "Please save the image first")
            return {'FINISHED'}

        ext = ima_path[-4:] # .jpg
        base = ima_path[:-4] # abc_x512

        sizeList = ["_x32","_x64","_x128","_x256","_x512","_x1024","_x2048","_x4096","_8192"]

        endScale = ""

        for size in sizeList:
            if base.endswith(size):
                endScale = size

        file = ""

        if endScale == "":
            stock = True
        else:
            stock = False
            slice = len(endScale)
            ground = base[:-slice]
            current = sizeList.index(endScale)
            file = ground + sizeList[current + 1] + ext

        if os.path.exists(file) and not stock:
            bpy.ops.image.open(filepath=file)

        return {'FINISHED'}


def draw(self, context):
    row = self.layout.row()
    row.label(text="Convert:")
    row = self.layout.row()
    row.operator("image.downsize")
    row = self.layout.row()
    row.operator("image.upsize")
    row = self.layout.row()
    row.label(text="Interpolation")
    row = self.layout.row()
    row.prop(bpy.context.scene,"tlm_image_interpolation")
    row = self.layout.row()

def register():
    bpy.utils.register_class(TLM_Downsize)
    bpy.types.IMAGE_PT_image_properties.append(draw)

def unregister():
    bpy.types.IMAGE_PT_image_properties.remove(draw)
    bpy.utils.unregister_class(TLM_Upsize)