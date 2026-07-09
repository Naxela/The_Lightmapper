import bpy, os

class TLM_Integrated_Denoise:

    image_array = []
    image_output_destination = ""

    def load(self, images):
        self.image_array = images

        self.cull_undefined()

    def setOutputDir(self, dir):
        self.image_output_destination = dir

    def cull_undefined(self):
        
        #Do a validation check before denoising

        cam = bpy.context.scene.camera
        if not cam:
            bpy.ops.object.camera_add()

            #Just select the first camera we find, needed for the compositor
            for obj in bpy.context.scene.objects:
                if obj.type == "CAMERA":
                    bpy.context.scene.camera = obj
                    return

    def _get_compositor_tree(self, scene):
        if hasattr(scene, 'compositing_node_group'):
            tree = scene.compositing_node_group
            if tree is None:
                tree = bpy.data.node_groups.new("TLM Compositor", 'CompositorNodeTree')
                scene.compositing_node_group = tree
            scene.render.use_compositing = True
            return tree

        if not scene.use_nodes:
            scene.use_nodes = True
        return scene.node_tree

    def _create_output_node(self, tree):
        if bpy.app.version >= (5, 0, 0):
            has_output = False
            for item in tree.interface.items_tree:
                if item.item_type == 'SOCKET' and item.in_out == 'OUTPUT' and item.name == "Image":
                    has_output = True
                    break
            if not has_output:
                tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            output_node = tree.nodes.new(type='NodeGroupOutput')
            return output_node, output_node.inputs["Image"]

        comp_node = tree.nodes.new('CompositorNodeComposite')
        return comp_node, comp_node.inputs[0]

    def denoise(self):

        scene = bpy.context.scene
        tree = self._get_compositor_tree(scene)
        
        #Remove existing nodes (which comes by default in Blender 3.4/3.5?)
        for node in list(tree.nodes):
                tree.nodes.remove(node)

        for image in self.image_array:

            if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
                print("Image...: " + image)

            img = bpy.data.images.load(self.image_output_destination + "/" + image)

            image_node = tree.nodes.new(type='CompositorNodeImage')
            image_node.image = img
            image_node.location = 0, 0

            denoise_node = tree.nodes.new(type='CompositorNodeDenoise')
            denoise_node.location = 300, 0

            comp_node, comp_input = self._create_output_node(tree)
            comp_node.location = 600, 0

            links = tree.links
            links.new(image_node.outputs[0], denoise_node.inputs[0])
            links.new(denoise_node.outputs[0], comp_input)

            # set output resolution to image res
            bpy.context.scene.render.resolution_x = img.size[0]
            bpy.context.scene.render.resolution_y = img.size[1]
            bpy.context.scene.render.resolution_percentage = 100

            filePath = bpy.data.filepath
            path = os.path.dirname(filePath)

            base = os.path.basename(image)
            filename, file_extension = os.path.splitext(image)
            filename = filename[:-6]

            bpy.context.scene.render.filepath = self.image_output_destination + "/" + filename + "_denoised" + file_extension

            denoised_image_path = self.image_output_destination
            bpy.context.scene.render.image_settings.file_format = "HDR"

            bpy.ops.render.render(write_still=True)

            #Cleanup
            comp_nodes = [image_node, denoise_node, comp_node]
            for node in comp_nodes:
                tree.nodes.remove(node)
