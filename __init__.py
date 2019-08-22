'''
Copyright (c) 2018-2019 Naxela

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
    'version': (0, 0, 1, 3),
    'blender': (2, 80, 0),
    'location': 'View3D',
    'category': '3D View'
}

from . addon import operators, panels, properties, utility

def register():
    operators.register()
    properties.register()
    panels.register()
    #utility.register()

def unregister():
    operators.unregister()
    properties.unregister()
    panels.unregister()
    #utility.unregister()