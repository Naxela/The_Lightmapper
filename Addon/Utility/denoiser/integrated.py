import bpy

class TLM_Integrated_Denoise:

    image_array = []
    image_output_destination = ""

    def load(self, images):
        self.image_array = images

    def setOutputDir(self, dir):
        self.image_output_destination = dir

    def cull_undefined(self):
        #Do a validation check before denoising
        pass

        cam = bpy.context.scene.camera
        if not cam:
            bpy.ops.object.camera_add()

    def setup(self):

        if not bpy.context.scene.use_nodes:
            bpy.context.scene.use_nodes = True

        tree = bpy.context.scene.node_tree

        #Only noisy result so far, as denoiser expects a screen-space normal;
        #Blender uses object-space. Maybe tangent space could work.

        for image in self.image_array:

            img = bpy.data.images.load(self.image_output_destination + "/" + image)

            image_node = tree.nodes.new(type='CompositorNodeImage')
            image_node.image = img
            image_node.location = 0, 0

            denoise_node = tree.nodes.new(type='CompositorNodeDenoise')
            denoise_node.location = 300, 0

            comp_node = tree.nodes.new('CompositorNodeComposite')
            comp_node.location = 600, 0

            links = tree.links
            links.new(image_node.outputs[0], denoise_node.inputs[0])
            links.new(denoise_node.outputs[0], comp_node.inputs[0])

            # set output resolution to image res
            bpy.context.scene.render.resolution_x = img.size[0]
            bpy.context.scene.render.resolution_y = img.size[1]

            filePath = bpy.data.filepath
            path = os.path.dirname(filePath)

            # bpy.data.scenes["Scene"].render.filepath = image_output_destination

            # denoised_image_path = bpy.data.scenes["Scene"].render.filepath + "." + \
            #     bpy.data.scenes["Scene"].render.image_settings.file_format.lower()

            # bpy.ops.render.render(write_still=True)

            # #Cleanup
            # comp_nodes = [image_node,nrm_image_node,color_image_node,denoise_node,comp_node]
            # for node in comp_nodes:
            #     tree.nodes.remove(node)


    def denoise():

        bpy.ops.render.render(write_still=True)

        #Cleanup
        comp_nodes = [image_node,nrm_image_node,color_image_node,denoise_node,comp_node]
        for node in comp_nodes:
            tree.nodes.remove(node)

        pass