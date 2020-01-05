import bpy
from bpy.props import *

class TLM_SceneProperties(bpy.types.PropertyGroup):
    tlm_bake_for_selection : BoolProperty(
        name="Bake for selection", 
        description="Only bake for the selected objects", 
        default=False)

    tlm_clean_for_selection : BoolProperty(
        name="Clean for selection", 
        description="Only clean for the selected objects", 
        default=False)

    tlm_clean_option : EnumProperty(
        items = [('Clean and restore', 'Clean and restore', 'TODO'),
                    ('Selection', 'Selection', 'TODO'),
                    ('Clean cache', 'Clean cache', 'TODO')],
                name = "Clean option", 
                description="TODO", 
                default='Clean and restore')

    tlm_quality : EnumProperty(
        items = [('Preview', 'Preview', 'TODO'),
                    ('Medium', 'Medium', 'TODO'),
                    ('High', 'High', 'TODO'),
                    ('Production', 'Production', 'TODO'),
                    ('Custom', 'Custom', 'TODO')],
                name = "Lightmapping Quality", 
                description="TODO", 
                default='Preview')

    tlm_lightmap_scale : EnumProperty(
        items = [('16', '1/16', 'TODO'),
                    ('8', '1/8', 'TODO'),
                    ('4', '1/4', 'TODO'),
                    ('2', '1/2', 'TODO'),
                    ('1', '1/1', 'TODO')],
                name = "Lightmap Resolution scale", 
                description="TODO", 
                default="1")

    tlm_lightmap_savedir : StringProperty(
        name="Lightmap Directory", 
        description="TODO", 
        default="Lightmaps", 
        subtype="FILE_PATH")

    tlm_mode : EnumProperty(
        items = [('CPU', 'CPU', 'TODO'),
                    ('GPU', 'GPU', 'TODO')],
                name = "Device", 
                description="TODO", 
                default="CPU")

    tlm_bake_mode : EnumProperty(
        items = [('Ordered', 'Foreground', 'TODO')],
                name = "Baking Mode", 
                description="TODO", 
                default="Ordered")

    tlm_baketime_material: EnumProperty(
        items = [('Inherit', 'Inherit', 'TODO'), 
                    ('Blank', 'Blank', 'TODO')],
                name = "Baketime material", 
                description="TODO", 
                default="Inherit")

    tlm_directional_mode: EnumProperty(
        items = [('None', 'None', 'TODO'), 
                    ('Baked normal', 'Baked normal', 'TODO')],
                name = "Directional Mode", 
                description="TODO", 
                default="None")

    tlm_bake_normal_denoising : BoolProperty(
        name="Bake normal for denoising", 
        description="TODO", 
        default=False)

    tlm_exposure_multiplier : FloatProperty(
        name="Exposure Multiplier", 
        default=0,
        description="0 to disable. Multiplies GI value"
    )

    # tlm_bake_mode : EnumProperty(
    #     items = [('Ordered', 'Foreground', 'TODO'),
    #                 ('Sequential', 'Background', 'TODO')],
    #             name = "Baking Mode", 
    #             description="TODO", 
    #             default="Ordered")

    tlm_keep_cache_files : BoolProperty(
        name="Keep cache files", 
        description="TODO", 
        default=True)

    tlm_apply_on_unwrap : BoolProperty(
        name="Apply scale", 
        description="TODO", 
        default=False)

    # tlm_caching_mode : EnumProperty(
    #     items = [('Copy', 'Copy', 'TODO'),
    #              ('Cache', 'Cache', 'TODO')],
    #             name = "Caching mode", 
    #             description="TODO", 
    #             default='Copy')

    tlm_caching_mode : EnumProperty(
        items = [('Copy', 'Copy', 'TODO')],
                name = "Caching mode", 
                description="TODO", 
                default='Copy')

    tlm_indirect_only : BoolProperty(
        name="Indirect Only", 
        description="TODO", 
        default=False)

    tlm_indirect_mode : EnumProperty(
        items = [('Multiply', 'Multiply', 'Multiply'),
                ('Additive', 'Additive', 'Additive')],
                name = "Indirect mode", 
                description="TODO", 
                default='Multiply')

    tlm_dilation_margin : IntProperty(
        name="Dilation margin", 
        default=16, 
        min=1, 
        max=64, 
        subtype='PIXEL')

    tlm_denoiser = EnumProperty(
        items = [('OIDN', 'OIDN', 'TODO.'),
                 ('Optix', 'Optix', 'TODO.')],
                name = "Denoiser", 
                description="TODO", 
                default='OIDN')

    tlm_delete_cache : BoolProperty(
        name="Delete cache", 
        description="TODO", 
        default=True)

    tlm_denoise_use : BoolProperty(
        name="Enable denoising", 
        description="TODO", 
        default=False)

    tlm_oidn_path : StringProperty(
        name="OIDN Path", 
        description="TODO", 
        default="", 
        subtype="FILE_PATH")

    tlm_oidn_verbose : BoolProperty(
        name="Verbose", 
        description="TODO")

    tlm_oidn_threads : IntProperty(
        name="Threads", 
        default=0, 
        min=0, 
        max=64, 
        description="Amount of threads to use. Set to 0 for auto-detect.")

    tlm_oidn_maxmem : IntProperty(
        name="Tiling max Memory", 
        default=0, 
        min=512, 
        max=32768, 
        description="Use tiling for memory conservation. Set to 0 to disable tiling.")

    tlm_oidn_affinity : BoolProperty(
        name="Set Affinity", 
        description="TODO")

    tlm_oidn_use_albedo : BoolProperty(
        name="Use albedo map", 
        description="TODO")

    tlm_oidn_use_normal : BoolProperty(
        name="Use normal map", 
        description="TODO")

    tlm_filtering_use : BoolProperty(
        name="Enable filtering", 
        description="TODO", 
        default=False)

    tlm_filtering_mode : EnumProperty(
        items = [('Box', 'Box', 'TODO'),
                    ('Gaussian', 'Gaussian', 'TODO'),
                    ('Bilateral', 'Bilateral', 'TODO'),
                    ('Median', 'Median', 'TODO')],
                name = "Filter", 
                description="TODO", 
                default='Gaussian')

    tlm_filtering_gaussian_strength : IntProperty(
        name="Gaussian Strength", 
        default=3, 
        min=1, 
        max=50)

    tlm_filtering_iterations : IntProperty(
        name="Filter Iterations", 
        default=1, 
        min=1, 
        max=50)

    tlm_filtering_box_strength : IntProperty(
        name="Box Strength", 
        default=1, 
        min=1, 
        max=50)

    tlm_filtering_bilateral_diameter : IntProperty(
        name="Pixel diameter", 
        default=3, 
        min=1, 
        max=50)

    tlm_filtering_bilateral_color_deviation : IntProperty(
        name="Color deviation", 
        default=75, 
        min=1, 
        max=100)

    tlm_filtering_bilateral_coordinate_deviation : IntProperty(
        name="Color deviation", 
        default=75, 
        min=1, 
        max=100)

    tlm_filtering_median_kernel : IntProperty(
        name="Median kernel", 
        default=3, 
        min=1, 
        max=5)

    tlm_encoding_mode : EnumProperty(
        items = [('RGBM', 'RGBM', '8-bit HDR encoding. Good for compatibility, good for memory but has banding issues.'),
                    ('RGBD', 'RGBD', '8-bit HDR encoding. Same as RGBM, but better for highlights and stylized looks.'),
                    ('RGBE', 'RGBE', '32-bit HDR RGBE encoding. Best quality, but high memory usage and not compatible with all devices.')],
                name = "Encoding Mode", 
                description="TODO", 
                default='RGBE')

    tlm_encoding_range : IntProperty(
        name="Encoding range", 
        description="Higher gives a larger HDR range, but also gives more banding.", 
        default=6, 
        min=1, 
        max=10)

    tlm_encoding_armory_setup : BoolProperty(
        name="Use Armory decoder", 
        description="TODO", 
        default=False)

    tlm_encoding_colorspace : EnumProperty(
        items = [('XYZ', 'XYZ', 'TODO'),
                    ('sRGB', 'sRGB', 'TODO'),
                    ('Raw', 'Raw', 'TODO'),
                    ('Non-Color', 'Non-Color', 'TODO'),
                    ('Linear ACES', 'Linear ACES', 'TODO'),
                    ('Linear', 'Linear', 'TODO'),
                    ('Filmic Log', 'Filmic Log', 'TODO')],
                name = "Color Space", 
                description="TODO", 
                default='Linear')

    tlm_compression : IntProperty(
        name="PNG Compression", 
        description="0 = No compression. 100 = Maximum compression.", 
        default=0, 
        min=0, 
        max=100)





    tlm_override_object_settings : BoolProperty(
        name="Override settings", 
        description="TODO", 
        default=False)

    tlm_mesh_lightmap_use : BoolProperty(
        name="Enable Lightmapping", 
        description="TODO", 
        default=False)

    tlm_mesh_apply_after : BoolProperty(
        name="Apply after build", 
        description="TODO", 
        default=False)

    tlm_mesh_emissive : BoolProperty(
        name="Include emissive light", 
        description="TODO", 
        default=False)

    tlm_mesh_emissive_shadow : BoolProperty(
        name="Emissive casts shadows", 
        description="TODO", 
        default=False)

    tlm_mesh_lightmap_resolution : EnumProperty(
        items = [('32', '32', 'TODO'),
                 ('64', '64', 'TODO'),
                 ('128', '128', 'TODO'),
                 ('256', '256', 'TODO'),
                 ('512', '512', 'TODO'),
                 ('1024', '1024', 'TODO'),
                 ('2048', '2048', 'TODO'),
                 ('4096', '4096', 'TODO'),
                 ('8192', '8192', 'TODO')],
                name = "Lightmap Resolution", 
                description="TODO", 
                default='256')

    tlm_mesh_lightmap_unwrap_mode : EnumProperty(
        items = [('Lightmap', 'Lightmap', 'TODO'),
                 ('Smart Project', 'Smart Project', 'TODO'),
                 ('Copy Existing', 'Copy Existing', 'TODO')],
                name = "Unwrap Mode", 
                description="TODO", 
                default='Smart Project')

    tlm_mesh_unwrap_margin : FloatProperty(
        name="Unwrap Margin", 
        default=0.1, 
        min=0.0, 
        max=1.0, 
        subtype='FACTOR')

    tlm_mesh_bake_ao : BoolProperty(
        name="Bake AO", 
        description="TODO", 
        default=False)

    tlm_light_lightmap_use : BoolProperty(
        name="Enable for Lightmapping", 
        description="TODO", 
        default=True)

    tlm_light_type : EnumProperty(
        items = [('Static', 'Static', 'Static baked light with both indirect and direct. Hidden after baking.'),
                 ('Stationary', 'Stationary', 'Semi dynamic light. Indirect baked, but can be moved, change intensity and color.')],
                name = "Light Type", 
                description="TODO", 
                default='Static')

    tlm_light_intensity_scale : FloatProperty(
        name="Intensity Scale", 
        default=1.0, 
        min=0.0, 
        max=10.0, 
        subtype='FACTOR')

    tlm_light_casts_shadows : BoolProperty(
        name="Casts shadows", 
        description="TODO", 
        default=True)
