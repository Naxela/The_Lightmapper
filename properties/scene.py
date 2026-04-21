import bpy, os
from bpy.props import *

class TLM_SceneProperties(bpy.types.PropertyGroup):

    tlm_setting_renderer : EnumProperty(
        items = [('CPU', 'CPU', 'Bake using the processor'),
                ('GPU', 'GPU', 'Bake using the graphics card')],
                name = "Device", 
                description="Select whether to use the CPU or the GPU", 
                default="CPU")

    tlm_setting_scale : EnumProperty(
        items = [('8', '1/8', '1/8th of set scale'),
                ('4', '1/4', '1/4th of set scale'),
                ('2', '1/2', 'Half of set scale'),
                ('1', '1/1', 'Full scale')],
                name = "Lightmap Resolution scale", 
                description="Lightmap resolution scaling. Adjust for previewing.", 
                default="1")

    tlm_supersampling: EnumProperty(
        items=[
            ('0', 'None', 'No supersampling. Bake at native resolution.'),
            ('2', '2x', 'Bake at 2x resolution and downscale. Smoother results with moderate memory cost.'),
            ('4', '4x', 'Bake at 4x resolution and downscale. Highest quality with significant memory cost.')
        ],
        name="Supersampling",
        description="Supersample lightmaps by baking at a higher resolution and downscaling.",
        default='0'
    )

    tlm_supersampling_filter: EnumProperty(
        items=[
            ('BOX',      'Box (Average)', 'Average all contributing high-res pixels into each output pixel. Most accurate for supersampling — preserves energy and avoids aliasing.'),
            ('GAUSSIAN', 'Gaussian',      'Weighted average per block — center pixels contribute more. Produces softer, smoother results than Box.'),
            ('BICUBIC',  'Bicubic',       'Smooth cubic interpolation via scipy.ndimage. Best quality but slowest. Falls back to Box if scipy is unavailable.'),
            ('BILINEAR', 'Bilinear',      'Blender\'s built-in bilinear scale. Fast but only samples at grid points, missing some pixel contributions.'),
        ],
        name="Downsample Filter",
        description="Filter algorithm used when downscaling the supersampled lightmap to its final resolution.",
        default='BOX'
    )

    tlm_dilation_margin : IntProperty(
        name="Dilation margin", 
        default=4,
        min=1, 
        max=64, 
        subtype='PIXEL')

    tlm_setting_savedir : StringProperty(
        name="Lightmap Directory", 
        description="Your baked lightmaps will be stored here.", 
        default="Lightmaps", 
        subtype="FILE_PATH")
    
    tlm_play_sound : BoolProperty(
        name="Play sound on finish", 
        description="Play sound on finish", 
        default=False)
    
    tlm_autoApply : BoolProperty(
        name="Apply lightmaps on finish", 
        description="Automatically apply lightmaps on finish", 
        default=False)
    
    tlm_resetUV : BoolProperty(
        name="Reset lightmaps UVs", 
        description="Delete existing lightmap UVs and recalculate them", 
        default=False)
    
    tlm_quality : EnumProperty(
        items = [('0', 'Exterior Preview', 'Best for fast exterior previz'),
                    ('1', 'Interior Preview', 'Best for fast interior previz with bounces'),
                    ('2', 'Medium', 'Best for complicated interior preview and final for isometric environments'),
                    ('3', 'High', 'Best used for final baking for 3rd person games'),
                    ('4', 'Production', 'Best for first-person and Archviz'),
                    ('5', 'Custom', 'Uses the cycles sample settings provided the user')],
                name = "Quality", 
                description="Select baking quality", 
                default="0")
    
    tlm_bake_mode : EnumProperty(
        items = [('DIFFUSE', 'Lightmap',          'Bake direct + indirect diffuse lighting'),
                 ('AO',     'Ambient Occlusion',  'Bake ambient occlusion')],
        name = "Bake Mode",
        description = "Select what to bake",
        default = 'DIFFUSE')

    tlm_denoise_use : BoolProperty(
        name="Enable denoising",
        description="Enable denoising for lightmaps",
        default=False)
    
    tlm_material_multi_user : EnumProperty(
        items = [('Ignore', 'Ignore', 'Ignore multi-user'),
                ('Unique', 'Unique', 'Every lightmapped object will get unique lightmap materials'),
                ('Shared', 'Shared', 'Objects sharing materials will also share UV space')],
                name = "Material multi-option", 
                description="Select how to handle shared materials across objects", 
                default='Unique')

    tlm_material_missing : EnumProperty(
        items = [('Ignore', 'Ignore', 'Ignore lightmapping on object'),
                #COPY MATERIAL + MATERIAL SELECTION
                ('Create', 'Create', 'Create a new empty material')],
                name = "Missing material", 
                description="Select how to handle missing materials on objects. There needs to be at least one", 
                default='Ignore')

    tlm_denoise_engine : EnumProperty(
        items = [('None', 'None', 'Don\'t use any denoising'),
                #('Integrated', 'Integrated', 'Use the Blender native denoiser (Compositor; Slow)'),
                ('OIDN', 'OIDN', 'Use the Intel OIDN denoiser if available')],
                name = "Denoiser", 
                description="Select which denoising engine to use.", 
                default='None')

    tlm_setting_keep_cache_files : BoolProperty(
        name="Keep cache files", 
        description="Keep cache files (non-filtered and non-denoised)", 
        default=True)

    tlm_format: EnumProperty(
        items=[
            ('HDR', 'HDR', 'Use the .HDR file format for storing HDR textures. Supports high dynamic range.'),
            ('EXR', 'EXR', 'Use the .EXR file format for HDR textures. Offers high precision and compatibility.'),
            ('KTX', 'KTX', 'Use the .KTX (KTX2) file format. Requires KTX binaries. Provides advanced compression and GPU-optimized formats.')],
        name="File Format",
        description="Select the file format to use for lightmaps.",
        default='HDR'
    )

    tlm_tex_format: EnumProperty(
        items=[
            ('F32', '32-bit Float (High Precision)', 'Maximum precision for HDR textures. Ideal for detailed lighting at the cost of higher memory usage.'),
            ('F16', '16-bit Float (Medium Precision)', 'Balances memory usage and quality. Suitable for most HDR use cases.'),
            ('VK', 'Packed HDR (Vulkan Optimized)', 'Uses Vulkan’s compact B10G11R11_UFLOAT_PACK32 format for efficient memory usage. No alpha channel.')
        ],
        name="Texture Format",
        description="Select the encoded format for KTX lightmaps.",
        default='F32'
    )

    tlm_tex_compression: BoolProperty(
        name="Enable Texture Compression",
        description="Use Zstandard compression to reduce file size for KTX lightmaps. Compression is lossless.",
        default=False
    )

    tlm_tex_compression_level: EnumProperty(
        items=[
            ('18', '18 (Maximum)', 'Maximum compression. Slowest encoding but smallest file size.'),
            ('10', '10 (Balanced)', 'Balanced compression. Good trade-off between size and encoding speed.'),
            ('4', '4 (Fast)', 'Faster encoding with moderate compression.'),
            ('1', '1 (Fastest)', 'Fastest encoding speed with minimal compression.')
        ],
        name="Compression Level",
        description="Select the level of Zstandard compression for KTX lightmaps.",
        default='10'
    )

    tlm_directional: BoolProperty(
        name="Directional Lightmaps",
        description="Bake 3 additional directional passes for Spherical Harmonics lightmaps",
        default=False
    )

    tlm_directional_mode: EnumProperty(
        items=[('SH', 'Spherical Harmonics', 'Godot-compatible SH directional lightmaps (3 axis-normal bake passes)')],
        name="Directional Mode",
        description="Encoding method for directional lightmaps",
        default='SH'
    )

    tlm_reset_lightmap_uv: BoolProperty(
        name="Remove Lightmap UV",
        description="",
        default=False
    )

    tlm_create_atlas: BoolProperty(
        name="Create Lightmap Atlases",
        description="",
        default=False
    )

    tlm_atlas_max_resolution : EnumProperty(
        items = [('1024', '1024', 'TODO'),
                ('2048', '2048', 'TODO'),
                ('4096', '4096', 'TODO'),
                ('8192', '8192', 'TODO'),
                ('16384', '16384', 'TODO')],
                name = "Atlas Max Resolution",
                description="TODO",
                default="1024")

    tlm_texel_size_cm : FloatProperty(
        name="Texel Size (cm)",
        description="Target size of one texel in centimeters. Resolution = (sqrt(world_area_m²) × 100) / texel_size, rounded to nearest power of 2, clamped 32-8192.",
        default=5.0,
        min=0.01,
        max=1000.0,
        soft_min=0.5,
        soft_max=50.0,
        precision=2
    )

    # ── Distributed Baking ──
    tlm_dist_role : EnumProperty(
        items = [('COORDINATOR', 'Coordinator', 'This machine distributes bake jobs to workers'),
                 ('WORKER', 'Worker', 'This machine receives and executes bake jobs')],
        name = "Role",
        description = "Role of this machine in distributed baking",
        default = "COORDINATOR")
    
    tlm_dist_port : IntProperty(
        name = "Port",
        description = "TCP port for coordinator/worker communication",
        default = 9274,
        min = 1024,
        max = 65535)
    
    tlm_dist_coordinator_address : StringProperty(
        name = "Coordinator Address",
        description = "IP address or hostname of the coordinator machine",
        default = "127.0.0.1")
    
    tlm_dist_coordinator_status : StringProperty(
        name = "Status",
        default = "Stopped")
    
    tlm_dist_worker_status : StringProperty(
        name = "Status",
        default = "Disconnected")