import bpy, math
from bpy.props import *

class TLM_ObjectProperties(bpy.types.PropertyGroup):
    tlm_mesh_lightmap_use : BoolProperty(
        name="Enable Lightmapping", 
        description="Enable Lightmapping for this object", 
        default=False)
    
    tlm_mesh_lightmap_resolution : EnumProperty(
        items = [('32', '32', '32'),
                 ('64', '64', '64'),
                 ('128', '128', '128'),
                 ('256', '256', '256'),
                 ('512', '512', '512'),
                 ('1024', '1024', '1024'),
                 ('2048', '2048', '2048'),
                 ('4096', '4096', '4096'),
                 ('8192', '8192', '8192')],
                name = "Lightmap Resolution", 
                description="The lightmap resolution for this object", 
                default='256')
    
    unwrap_modes = [('Lightmap',     'Lightmap Pack',   'Pack each face\'s UVs into the UV bounds using Blender\'s Lightmap Pack operator'),
                    ('SmartProject', 'Smart Project',   'Unwrap using Smart UV Project')]
    
    tlm_mesh_lightmap_unwrap_mode : EnumProperty(
        items = unwrap_modes,
                name = "Unwrap Mode",
                description="The unwrap mode for this object", 
                default='SmartProject')
    
    tlm_mesh_unwrap_margin : FloatProperty(
        name="Unwrap Margin",
        description="The unwrap margin for this object",
        default=0.1,
        min=0.0,
        max=1.0,
        subtype='FACTOR')

    tlm_uv_channel : StringProperty(
        name="UV Channel",
        description="Name of the UV channel to bake into. If it already exists it will be used as-is, skipping unwrap.",
        default="UVMap-Lightmap")

    tlm_use_per_object_lightmap_pack : BoolProperty(
        name="Override Lightmap Pack Settings",
        description="Use per-object Lightmap Pack settings instead of the global defaults",
        default=False)

    tlm_lightmap_pack_selection : EnumProperty(
        items=[
            ('ALL_FACES',   'All Faces',    'Pack all faces'),
            ('SEL_FACES',   'Selected Faces', 'Pack only selected faces'),
            ('ALL_OBJECTS', 'All Objects',  'Pack faces from all objects sharing the same texture')],
        name="Selection",
        default='ALL_FACES')

    tlm_lightmap_pack_share_space : BoolProperty(
        name="Share Texture Space",
        description="Share the UV space between multiple objects",
        default=True)

    tlm_lightmap_pack_new_uv : BoolProperty(
        name="New UV Map",
        description="Create a new UV map instead of overwriting the existing one",
        default=False)

    tlm_lightmap_pack_quality : IntProperty(
        name="Pack Quality",
        description="Higher quality gives a tighter pack but is slower",
        default=12,
        min=1,
        max=48)

    tlm_lightmap_pack_margin : FloatProperty(
        name="Margin",
        description="Margin between UV islands",
        default=0.1,
        min=0.0,
        max=1.0)

    tlm_use_per_object_unwrap : BoolProperty(
        name="Override Unwrap Settings",
        description="Use per-object Smart Project settings instead of the global defaults",
        default=False)

    tlm_smart_project_angle_limit : FloatProperty(
        name="Angle Limit",
        description="Lower-angle faces are smoothed",
        default=math.radians(66.0),
        min=0.0,
        max=math.pi,
        subtype='ANGLE')

    tlm_smart_project_margin_method : EnumProperty(
        items=[
            ('SCALED',   'Scaled',   'Margin is scaled by the island area'),
            ('ADD',      'Add',      'Margin is added as a fixed amount'),
            ('FRACTION', 'Fraction', 'Margin is a fraction of the UV space')],
        name="Margin Method",
        default='SCALED')

    tlm_smart_project_rotation_method : EnumProperty(
        items=[
            ('AXIS_ALIGNED',   'Axis-aligned (Vertical)',   'Align islands to the vertical axis'),
            ('AXIS_ALIGNED_X', 'Axis-aligned (Horizontal)', 'Align islands to the horizontal axis'),
            ('ARBITRARY',      'Arbitrary',                 'Rotate islands for best fit')],
        name="Rotation Method",
        default='AXIS_ALIGNED')

    tlm_smart_project_island_margin : FloatProperty(
        name="Island Margin",
        description="Margin between UV islands",
        default=0.0,
        min=0.0,
        max=1.0)

    tlm_smart_project_area_weight : FloatProperty(
        name="Area Weight",
        description="Weight projection by face area",
        default=0.0,
        min=0.0,
        max=1.0)

    tlm_smart_project_correct_aspect : BoolProperty(
        name="Correct Aspect",
        description="Map UVs taking image aspect ratio into account",
        default=True)

    tlm_smart_project_scale_to_bounds : BoolProperty(
        name="Scale to Bounds",
        description="Scale UV coordinates to fill the UV space",
        default=False)