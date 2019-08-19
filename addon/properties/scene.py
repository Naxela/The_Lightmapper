import bpy
from bpy.props import *

def register():

    bpy.types.Scene.tlm_bake_for_selection = BoolProperty(name="Bake for selection", description="Only bake for the selected objects", default=False)

    bpy.types.Scene.tlm_clean_for_selection = BoolProperty(name="Clean for selection", description="Only clean for the selected objects", default=False)

    bpy.types.Scene.tlm_quality = EnumProperty(
        items = [('Preview', 'Preview', 'TODO'),
                    ('Medium', 'Medium', 'TODO'),
                    ('High', 'High', 'TODO'),
                    ('Production', 'Production', 'TODO'),
                    ('Custom', 'Custom', 'TODO')],
                name = "Lightmapping Quality", description="TODO", default='Preview')

    bpy.types.Scene.tlm_lightmap_scale = EnumProperty(
        items = [('16', '1/16', 'TODO'),
                    ('8', '1/8', 'TODO'),
                    ('4', '1/4', 'TODO'),
                    ('2', '1/2', 'TODO'),
                    ('1', '1/1', 'TODO')],
                name = "Lightmap Resolution scale", description="TODO", default="1")

    bpy.types.Scene.tlm_lightmap_savedir = StringProperty(name="Lightmap Directory", description="TODO", default="Lightmaps", subtype="FILE_PATH")

    bpy.types.Scene.tlm_mode = EnumProperty(
        items = [('CPU', 'CPU', 'TODO'),
                    ('GPU', 'GPU', 'TODO')],
                name = "Device", description="TODO", default="CPU")

    bpy.types.Scene.tlm_apply_on_unwrap = BoolProperty(name="Apply scale", description="TODO", default=False)

    bpy.types.Scene.tlm_indirect_only = BoolProperty(name="Indirect Only", description="TODO", default=False)

    bpy.types.Scene.tlm_dilation_margin = IntProperty(name="Dilation margin", default=16, min=1, max=64, subtype='PIXEL')

    bpy.types.Scene.tlm_delete_cache = BoolProperty(name="Delete cache", description="TODO", default=True)

    bpy.types.Scene.tlm_denoise_use = BoolProperty(name="Enable denoising", description="TODO", default=False)

    bpy.types.Scene.tlm_oidn_path = StringProperty(name="OIDN Path", description="TODO", default="", subtype="FILE_PATH")

    bpy.types.Scene.tlm_oidn_verbose = BoolProperty(name="Verbose", description="TODO")

    bpy.types.Scene.tlm_oidn_threads = IntProperty(name="Threads", default=0, min=0, max=64, description="Amount of threads to use. Set to 0 for auto-detect.")

    bpy.types.Scene.tlm_oidn_maxmem = IntProperty(name="Tiling max Memory", default=0, min=512, max=32768, description="Use tiling for memory conservation. Set to 0 to disable tiling.")

    bpy.types.Scene.tlm_oidn_affinity = BoolProperty(name="Set Affinity", description="TODO")

    bpy.types.Scene.tlm_oidn_use_albedo = BoolProperty(name="Use albedo map", description="TODO")

    bpy.types.Scene.tlm_oidn_use_normal = BoolProperty(name="Use normal map", description="TODO")

    bpy.types.Scene.tlm_filtering_use = BoolProperty(name="Enable filtering", description="TODO", default=False)

    bpy.types.Scene.tlm_filtering_mode = EnumProperty(
        items = [('Box', 'Box', 'TODO'),
                    ('Gaussian', 'Gaussian', 'TODO'),
                    ('Bilateral', 'Bilateral', 'TODO'),
                    ('Median', 'Median', 'TODO')],
                name = "Filter", description="TODO", default='Gaussian')

    bpy.types.Scene.tlm_filtering_gaussian_strength = IntProperty(name="Gaussian Strength", default=3, min=1, max=50)

    bpy.types.Scene.tlm_filtering_iterations = IntProperty(name="Filter Iterations", default=1, min=1, max=50)

    bpy.types.Scene.tlm_filtering_box_strength = IntProperty(name="Box Strength", default=1, min=1, max=50)

    bpy.types.Scene.tlm_filtering_bilateral_diameter = IntProperty(name="Pixel diameter", default=3, min=1, max=50)

    bpy.types.Scene.tlm_filtering_bilateral_color_deviation = IntProperty(name="Color deviation", default=75, min=1, max=100)

    bpy.types.Scene.tlm_filtering_bilateral_coordinate_deviation = IntProperty(name="Color deviation", default=75, min=1, max=100)

    bpy.types.Scene.tlm_filtering_median_kernel = IntProperty(name="Median kernel", default=3, min=1, max=5)

    bpy.types.Scene.tlm_encoding_mode = EnumProperty(
        items = [('RGBM', 'RGBM', '8-bit HDR encoding. Good for compatibility, good for memory but has banding issues.'),
                    ('RGBD', 'RGBD', '8-bit HDR encoding. Same as RGBM, but better for highlights and stylized looks.'),
                    ('RGBE', 'RGBE', '32-bit HDR RGBE encoding. Best quality, but high memory usage and not compatible with all devices.')],
                name = "Encoding Mode", description="TODO", default='RGBE')

    bpy.types.Scene.tlm_encoding_range = IntProperty(name="Encoding range", description="Higher gives a larger HDR range, but also gives more banding.", default=6, min=1, max=10)

    bpy.types.Scene.tlm_encoding_armory_setup = BoolProperty(name="Use Armory decoder", description="TODO", default=True)

    bpy.types.Scene.tlm_encoding_colorspace = EnumProperty(
        items = [('XYZ', 'XYZ', 'TODO'),
                    ('sRGB', 'sRGB', 'TODO'),
                    ('Raw', 'Raw', 'TODO'),
                    ('Non-Color', 'Non-Color', 'TODO'),
                    ('Linear ACES', 'Linear ACES', 'TODO'),
                    ('Linear', 'Linear', 'TODO'),
                    ('Filmic Log', 'Filmic Log', 'TODO')],
                name = "Color Space", description="TODO", default='Linear')

    bpy.types.Scene.tlm_compression = IntProperty(name="PNG Compression", description="0 = No compression. 100 = Maximum compression.", default=0, min=0, max=100)

# class TLMSceneProperties(bpy.types.PropertyGroup):

#     tlm_bake_for_selection : BoolProperty(name="Bake for selection", description="Only bake for the selected objects", default=False)

#     tlm_quality : EnumProperty(
#         items = [('16', '1/16', 'TODO'),
#                  ('8', '1/8', 'TODO'),
#                  ('4', '1/4', 'TODO'),
#                  ('2', '1/2', 'TODO'),
#                  ('1', '1/1', 'TODO')],
#                 name = "Lightmap Resolution scale", description="TODO", default="1")

#     tlm_lightmap_savedir : StringProperty(name="Lightmap Directory", description="TODO", default="Lightmaps", subtype="FILE_PATH")

#     tlm_mode : EnumProperty(
#         items = [('CPU', 'CPU', 'TODO'),
#                  ('GPU', 'GPU', 'TODO')],
#                 name = "Device", description="TODO", default="CPU")

#     tlm_apply_on_unwrap : BoolProperty(name="Apply scale", description="Apply the scale and rotation transformation before unwrap", default=False)

#     tlm_indirect_only : BoolProperty(name="Indirect Only", description="Bake only indirect light contribution", default=False)

#     tlm_dilation_margin : IntProperty(name="Dilation margin", description="Baking dilation margin", default=16, min=1, max=64, subtype='PIXEL')

#     tlm_delete_cache : BoolProperty(name="Delete cache", description="Delete temporary cache files after baking", default=True)

#     tlm_denoise_use : BoolProperty(name="Enable denoising", description="Enable denoising of baked textures", default=False)

#     tlm_oidn_path : StringProperty(name="OIDN Path", description="Path to OIDN. Uses bundled path by default", default="", subtype="FILE_PATH")

#     tlm_oidn_verbose : BoolProperty(name="Verbose", description="Make output verbose. Better information output.")

#     tlm_oidn_threads : IntProperty(name="Threads", default=0, min=0, max=64, description="Amount of threads to use. Set to 0 for auto-detect.")

#     tlm_oidn_maxmem : IntProperty(name="Tiling max Memory", default=0, min=512, max=32768, description="Use tiling for memory conservation. Set to 0 to disable tiling.")

#     tlm_oidn_affinity : BoolProperty(name="Set Affinity", description="Automatic thread affinity")

#     tlm_filtering_use : BoolProperty(name="Enable filtering", description="Enable filtering for baked textures", default=False)

#     tlm_filtering_mode : EnumProperty(
#         items = [('Box', 'Box', 'Fast box filtering'),
#                  ('Gaussian', 'Gaussian', 'Smooth gaussian filtering'),
#                  ('Bilateral', 'Bilateral', 'Edge-aware bilateral filtering, best but slowest'),
#                  ('Median', 'Median', 'Fast median filtering')],
#                 name = "Filter", description="Filtering mode", default='Gaussian')

#     tlm_filtering_gaussian_strength : IntProperty(name="Gaussian Strength", description="Gaussian filtering strength", default=3, min=1, max=50)

#     tlm_filtering_iterations : IntProperty(name="Filter Iterations", description="Filtering iterations", default=1, min=1, max=50)

#     tlm_filtering_box_strength : IntProperty(name="Box Strength", description="Box filtering strength", default=1, min=1, max=50)

#     tlm_filtering_bilateral_diameter : IntProperty(name="Pixel diameter", description="Bilaterial pixel diameter", default=3, min=1, max=50)

#     tlm_filtering_bilateral_color_deviation : IntProperty(name="Color deviation", description="Bilaterial color deviation", default=75, min=1, max=100)

#     tlm_filtering_bilateral_coordinate_deviation : IntProperty(name="Color deviation", description="Bilaterial coordinate deviation", default=75, min=1, max=100)

#     tlm_filtering_median_kernel : IntProperty(name="Median kernel", description="Median filtering kernel", default=3, min=1, max=5)

#     tlm_encoding_mode : EnumProperty(
#         items = [('RGBM', 'RGBM', '8-bit HDR encoding. Good for compatibility, good for memory but has banding issues.'),
#                  ('RGBD', 'RGBD', '8-bit HDR encoding. Same as RGBM, but better for highlights and stylized looks.'),
#                  ('RGBE', 'RGBE', '32-bit HDR RGBE encoding. Best quality, but high memory usage and not compatible with all devices.')],
#                 name = "Encoding Mode", description="Encoding mode for compatibility.", default='RGBE')

#     tlm_encoding_range : IntProperty(name="Encoding range", description="Higher gives a larger HDR range, but also gives more banding.", default=6, min=1, max=10)

#     tlm_encoding_armory_setup : BoolProperty(name="Use Armory decoder", description="Setup Armory RGBM/RGBD node decoder in the material", default=True)

#     tlm_encoding_colorspace : EnumProperty(
#         items = [('XYZ', 'XYZ', 'XYZ colorspace'),
#                  ('sRGB', 'sRGB', 'sRGB colorspace'),
#                  ('Raw', 'Raw', 'Raw colorspace'),
#                  ('Non-Color', 'Non-Color', 'Use no encoding'),
#                  ('Linear ACES', 'Linear ACES', 'Use filmic ACES encoding'),
#                  ('Linear', 'Linear', 'Use Linear encoding'),
#                  ('Filmic Log', 'Filmic Log', 'Use Filmic Logarithmic encoding')],
#                 name = "Color Space", description="Colorspace encoding for lightmaps. Linear by default.", default='Linear')

#     tlm_compression : IntProperty(name="PNG Compression", description="0 = No compression. 100 = Maximum compression.", default=0, min=0, max=100)

# def register():
#     bpy.types.Scene.tlm_props = CollectionProperty(type=TLMSceneProperties)