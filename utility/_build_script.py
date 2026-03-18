import bpy, os, json, math
import numpy as np

class TLMBuilder:
    
    # Initializes the TLMBuilder class with a list of objects and sets up the lightmap directory
    def __init__(self, obj_list):
        self.obj_list = obj_list
        self.lightmap_dir = "//" + bpy.context.scene.TLM_SceneProperties.tlm_setting_savedir
        self.abs_dir = bpy.path.abspath(self.lightmap_dir)
        if not os.path.exists(self.abs_dir):
            os.makedirs(self.abs_dir)

    # Creates bake images for each object if they do not already exist
    def create_bake_images(self, obj):
        img_name = "TLM-" + obj.name
        if img_name not in bpy.data.images:
            ss = int(bpy.context.scene.TLM_SceneProperties.tlm_supersampling)
            ss_factor = ss if ss > 0 else 1
            resolution = (int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) // int(bpy.context.scene.TLM_SceneProperties.tlm_setting_scale)) * ss_factor
            image = bpy.data.images.new(img_name, resolution, resolution, alpha=True, float_buffer=True)

        if bpy.context.scene.TLM_SceneProperties.tlm_material_missing == "Create":
            if len(obj.material_slots) == 0:
                single = False
                number = 0
                while single == False:
                    matname = obj.name + ".00" + str(number)
                    if matname in bpy.data.materials:
                        single = False
                        number = number + 1
                    else:
                        mat = bpy.data.materials.new(name=matname)
                        mat.use_nodes = True
                        obj.data.materials.append(mat)
                        single = True

        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue #Shouldn't occur
            if not mat.use_nodes:
                mat.use_nodes = True
                print(f"No nodes in: {obj.name} w/ {mat.name}")
                print(f"[TLM]:2:Error no nodes in {obj.name} - {msg}", flush=True)
                continue

            nodes = mat.node_tree.nodes
            if "TLM-Lightmap" in nodes:
                nodes["TLM-Lightmap"].image = bpy.data.images[img_name]
                nodes.active = nodes["TLM-Lightmap"]
            else:
                img_node = nodes.new('ShaderNodeTexImage')
                img_node.name = 'TLM-Lightmap'
                img_node.location = (100, 100)
                img_node.image = bpy.data.images[img_name]
                nodes.active = img_node

        mesh = obj.data
        uv_channel = obj.TLM_ObjectProperties.tlm_uv_channel or "UVMap-Lightmap"
        if uv_channel in mesh.uv_layers:
            mesh.uv_layers.active = mesh.uv_layers[uv_channel]
        elif "UVMap-Lightmap-part" in mesh.uv_layers:
            # Object was previously atlassed: UVMap-Lightmap was renamed to UVMap-Atlas.
            # Use the backed-up per-object UVs so the bake is in object UV space.
            mesh.uv_layers.active = mesh.uv_layers["UVMap-Lightmap-part"]

    # Bakes the diffuse lighting for the given object
    def bake_object(self, obj):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        #We don't wanna bake it if there isn't any materials
        if len(obj.material_slots) != 0:
            try:
                bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=bpy.context.scene.TLM_SceneProperties.tlm_dilation_margin, use_clear=True)
                print(f"[TLM]:1:Baking object '{obj.name}' with diffuse lighting...", flush=True)
            except RuntimeError as e:
                msg = str(e).replace(":", " - ")
                print(f"[TLM]:2:Error baking {obj.name} - {msg}", flush=True)

    # Creates a custom property linking the lightmap to the object
    def create_link_properties(self, obj):
        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue
            if mat.use_nodes and "TLM-Lightmap" in mat.node_tree.nodes:
                image = mat.node_tree.nodes["TLM-Lightmap"].image
                if image:
                    obj["TLM-Lightmap"] = image.name
                    print(f"Property for {obj.name} set to: {image.name}")

    # Saves the baked lightmaps for the given object to the lightmap directory
    def save_lightmaps(self, obj):
        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue
            if mat.use_nodes and "TLM-Lightmap" in mat.node_tree.nodes:
                image = mat.node_tree.nodes["TLM-Lightmap"].image
                if image:

                    if bpy.context.scene.TLM_SceneProperties.tlm_format == "EXR" or bpy.context.scene.TLM_SceneProperties.tlm_format == "KTX":
                        file_path = os.path.join(self.abs_dir, f"{image.name}.exr")
                    else:
                        file_path = os.path.join(self.abs_dir, f"{image.name}.hdr")


                    if not os.path.exists(file_path):

                        if bpy.context.scene.TLM_SceneProperties.tlm_format == "EXR" or bpy.context.scene.TLM_SceneProperties.tlm_format == "KTX":

                            print("[TLM]:1:Saving as EXR File...", flush=True)

                            bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR'
                            image.save_render(filepath=file_path)

                        else:

                            print("[TLM]:1:Saving as HDR File...", flush=True)

                            bpy.context.scene.render.image_settings.file_format = 'HDR'
                            bpy.context.scene.render.image_settings.color_depth = '32'
                            image.save_render(filepath=file_path)

                        print(f"Image saved to {file_path}")
                    else:
                        print(f"Image already exists at {file_path}")
                else:
                    print(f"Image not found for material in {obj.name}")

    # Applies the lightmap to the object's material by linking it to the Principled BSDF shader
    def apply_lightmap(self, obj):
        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue
            if mat.use_nodes:
                lightmap_node = mat.node_tree.nodes.get("TLM-Lightmap")
                bsdf_node = mat.node_tree.nodes.get("Principled BSDF")
                if lightmap_node and bsdf_node:
                    mat.node_tree.links.new(lightmap_node.outputs[0], bsdf_node.inputs[0])

    # Compiles a manifest of all baked lightmaps, storing the information in a JSON file
    def compile_manifest(self):

        if bpy.context.scene.TLM_SceneProperties.tlm_format == "EXR" or bpy.context.scene.TLM_SceneProperties.tlm_format == "KTX":
            
            manifest = {"ext": "exr"}

        elif bpy.context.scene.TLM_SceneProperties.tlm_format == "KTX":

            # For KTX we would rather change this manually, since the denoiser (nor Blender) can't work with KTX files
            manifest = {"ext": "exr"}

        else:

            manifest = {"ext": "hdr"}

        manifest["lightmaps"] = {}

        for obj_name in self.obj_list:
            obj = bpy.data.objects[obj_name]
            if "TLM-Lightmap" in obj:
                manifest["lightmaps"][obj.name] = obj["TLM-Lightmap"]

        file_path = os.path.join(self.abs_dir, "manifest.json")
        with open(file_path, "w") as f:
            json.dump(manifest, f)
        print("Manifest compiled:", manifest)

    def downscale_if_supersampled(self, obj):
        ss = int(bpy.context.scene.TLM_SceneProperties.tlm_supersampling)
        if ss <= 0:
            return
        img_name = "TLM-" + obj.name
        if img_name not in bpy.data.images:
            return
        img = bpy.data.images[img_name]
        target_res = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) // int(bpy.context.scene.TLM_SceneProperties.tlm_setting_scale)
        filter_mode = bpy.context.scene.TLM_SceneProperties.tlm_supersampling_filter

        if filter_mode == 'BOX':
            # Box filter: reshape into ss x ss blocks and average each block.
            # Every high-res pixel contributes equally to its output pixel.
            src = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
            downsampled = src.reshape(target_res, ss, target_res, ss, 4).mean(axis=(1, 3))
            img.scale(target_res, target_res)
            img.pixels[:] = downsampled.flatten().tolist()
        elif filter_mode == 'GAUSSIAN':
            # Gaussian filter: weighted average per block, center pixels weighted more.
            # Produces softer, smoother results than box — reduces block artifacts.
            src = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
            ax = np.arange(ss) - (ss - 1) / 2.0
            kernel_1d = np.exp(-ax ** 2 / (2 * (ss / 2.0) ** 2))
            kernel_1d /= kernel_1d.sum()
            kernel_2d = np.outer(kernel_1d, kernel_1d)  # (ss, ss)
            weights = kernel_2d[np.newaxis, :, np.newaxis, :, np.newaxis]  # broadcast over blocks
            blocks = src.reshape(target_res, ss, target_res, ss, 4)
            downsampled = (blocks * weights).sum(axis=(1, 3))
            img.scale(target_res, target_res)
            img.pixels[:] = downsampled.flatten().tolist()
        elif filter_mode == 'BICUBIC':
            # Bicubic: uses scipy.ndimage.zoom (order=3) — smooth cubic interpolation.
            # Blender bundles scipy, so this should always be available.
            try:
                from scipy.ndimage import zoom
                src = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
                scale = target_res / img.size[0]
                downsampled = zoom(src, (scale, scale, 1), order=3)
                downsampled = np.clip(downsampled, 0.0, None)  # HDR — no upper clamp
                img.scale(target_res, target_res)
                img.pixels[:] = downsampled.flatten().tolist()
            except ImportError:
                print("[TLM]:2:scipy not available for Bicubic — falling back to Box filter.", flush=True)
                src = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
                downsampled = src.reshape(target_res, ss, target_res, ss, 4).mean(axis=(1, 3))
                img.scale(target_res, target_res)
                img.pixels[:] = downsampled.flatten().tolist()
        else:
            # Bilinear: Blender's built-in scale (bilinear interpolation at grid points).
            img.scale(target_res, target_res)

    # Manages the entire bake process, reporting progress throughout
    def bake_objects_and_report_progress(self):
        print("[TLM]:1:Starting the baking process for all objects...", flush=True)
        print(f"[TLM]:0:0.0", flush=True)

        scene = bpy.context.scene
        scene.render.engine = "CYCLES"

        total = len(self.obj_list)
        for index, obj_name in enumerate(self.obj_list):
            obj = bpy.data.objects[obj_name]
            self.create_bake_images(obj)
            self.bake_object(obj)
            self.downscale_if_supersampled(obj)  # Downscale before saving
            self.save_lightmaps(obj)
            print(f"[TLM]:0: {(index + 1) / total}", flush=True)

        for obj_name in self.obj_list:
            obj = bpy.data.objects[obj_name]
            self.create_link_properties(obj)

        self.compile_manifest()
        print("[TLM]:1:Finished the baking process for all objects.", flush=True)


####################################################
################## FUNCTION RUN ####################

obj_list = [obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH' and hasattr(obj, 'TLM_ObjectProperties') and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use]

tlm_builder = TLMBuilder(obj_list)
tlm_builder.bake_objects_and_report_progress()