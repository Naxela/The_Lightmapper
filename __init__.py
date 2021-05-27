'''
Copyright (c) 2018-2020 Naxela

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
'''

bl_info = {
    'name': 'The Lightmapper',
    'description': 'The Lightmapper is a lightmapping utility addon for Blender, made specifically for making lightmaps for game engines.',
    'author': 'Alexander Kleemann @ Naxela',
    'version': (0, 5, 5, 0),
    'blender': (2, 92, 0),
    'location': 'View3D',
    'category': '3D View'
}

from . addon import operators, panels, properties, preferences, utility, keymap

def register():
    operators.register()
    properties.register()
    preferences.register()
    panels.register()
    keymap.register()

def unregister():
    operators.unregister()
    properties.unregister()
    preferences.unregister()
    panels.unregister()
    keymap.unregister()

'''
Changes:

- 18.08.2020
0.3.0.0 - Initial version
0.3.0.1 - Fix for https://github.com/Naxela/The_Lightmapper/issues/38
0.3.0.2 - Added sound alert on finish
0.3.0.3 - Fix for resolution scale
0.3.0.4 - Begin supersampling, only internal resizing for now
0.3.0.5 - Fix for multiple materials while encoding

- 21.08.2020
0.3.0.6 - Expose sound alert
0.3.0.7 - Hide undetected engines, and display in preferences
0.3.0.8 - Smart Filtering for lightmaps
0.3.0.9 - Possible fix for https://github.com/Naxela/The_Lightmapper/issues/33
0.3.1.0 - Display baking process as percentage
0.3.1.1 - Revert render engine after baking is finished

- 26.08.2020
0.3.1.2 - Revert resolution after integrated denoiser is used
0.3.1.3 - Temporarily hide shader based filtering until it’s ready
0.3.1.4 - Fix for https://github.com/Naxela/The_Lightmapper/issues/40
0.3.1.5 - Reimplement Optix AI denoising

- 27.08.2020
0.3.1.6 - Safeguard against unassigned material slots
0.3.1.7 - Unhide objects before unwrapping (Possibly due to Blender bug regarding SmartUV projection)
0.3.1.8 - Fix for lightmaps won’t bake either due to hidden objects
0.3.1.9 - Use nodes for unassigned materials
0.3.2.0 - Fix for restoring unassigned materials (causing NoneType error)

- 29.08.2020
0.3.2.1 - Fix for context error when in Edit mode
0.3.2.2 - Fix for audio, additional alert sounds

- 02.09.2020
0.4.0.0 - Reimplement keymaps to F6 (Build) and F7 (Clean)
0.4.0.1 - Ignore keymapping in background mode
0.4.0.2 - Removed filtering file
0.4.0.3 - Reimplement atlas group classes
0.4.0.4 - Reimplement atlas group pointer
0.4.0.5 - Reimplement atlas group process
0.4.0.6 - Fix for filter override with atlas groups
0.4.0.7 - Add ability to skip materials on lightmap designated objects
0.4.0.8 - Automatically configure tile size
0.4.0.9 - Reset to SmartProject when AtlasGroup is deleted
0.4.1.0 - Begin clamping for value based links

- 07.09.2020
0.4.1.1 - Fix for importlib utility call
0.4.1.2 - Fix for background bake
0.4.1.3 - Disable GPU offscreen function for background bake
0.4.1.4 - Fix for unregister error

- 08.09.2020
0.4.1.5 - Fixed AtlasGroup assignments for selections
0.4.1.6 - Implement indirect baking as an option
0.4.1.7 - Implement AO baking as an option
0.4.1.8 - Begin to sort verbose console output
0.4.1.9 - Added custom BG color

- 13.09.2020
0.4.2.0 - Stubs for network rendering
0.4.2.1 - Reimplement process for background baking (No more unstable threading)
0.4.2.2 - Fix denoising path errors on Linux and Mac
0.4.2.3 - Fix infinite OpenCV installation on Linux

- 15.09.2020
0.4.2.4 - Reimplement RGBD encoding
0.4.2.5 - Add decoder options for RGBM, RGBD and LogLuv
0.4.2.6 - Begin network rendering server
0.4.2.7 - Begin network rendering client

- 29.09.2020
0.4.2.9 - Fix Xatlas bug
0.4.3.0 - Begin AtlasGroup postpacking
0.4.3.1 - Improve AtlasGroup postpacking (Rectmap packing)
0.4.3.2 - Improve AtlasGroup postpacking
0.4.3.3 - Add UV manipulation for AtlasGroup postpacking
0.4.3.4 - Fix for encoding with AtlasGroup

- 01.10.2020
0.4.3.5 - Fixes for postpacking
0.4.3.6 - Fixes for prepacking
0.4.3.7 - Xatlas atlasgroup packing
0.4.3.8 - Begin combinedAO

- 02.10.2020
0.4.3.9 - Add Xatlas bulk selection
0.4.4.0 - Ensure lightmap status on postpacking

- 04.10.2020
0.4.4.1 - Begin environment probe building
0.4.4.2 - CMFT path fixes
0.4.4.3 - Probe resolution
0.4.4.4 - SH coefficients option
0.4.4.5 - Add clean environment probe

- 06.10.2020
0.4.4.6 - Fix for environment probe direction
0.4.4.7 - Begin radiance maps
0.4.4.8 - Begin texel density integration
0.4.4.9 - Begin merge adjacent actors

- 10.10.2020
0.4.5.0 - Add shutdown parameter
0.4.5.1 - Remove matplotlib dependency

- 15.10.2020
0.4.5.2 - Begin imagetools
0.4.5.3 - Begin GPU shaders
0.4.5.4 - Extend RGBD Range

- 19.10.2020
0.4.5.5 - Update RGBD CPU encoding

- 26.10.2020
0.4.5.6 - Fixes for RGBD encoding

- 01.11.2020
0.4.5.7 - Node fixes

- 15.11.2020
0.4.5.8 - Fixes for postpacking
0.4.5.9 - Fix for CV2 check
0.4.6.0 - Pack cleanup
0.4.6.1 - Begin dilation

- 01.12.2020
0.4.6.2 - Add metallic clamping features (limit, zero, ignore) for principled BSDF
0.4.6.3 - Begin work on Octane Render implementation (Currently only way for dominant light information)
0.4.6.4 - Fixes for 2.91 API changes

- 14.12.2020
0.4.6.5 - Add option for select uv channels for lightmaps
0.4.6.6 - Limited time decimals
0.4.6.7 - Added options for interpolation and extrapolation
'''