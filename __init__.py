"""
Copyright (C) 2024 Alexander "Naxela" Kleemann.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# file: __init__.py
# brief: Addon registration
# author Alexander "Naxela" Kleemann
# copyright 2024 Alexander "Naxela" Kleemann.
# TheLightmapper2

bl_info = {
    "name": "The Lightmapper",
    "author": "Alexander 'Naxela' Kleemann",
    "location": "T",
    "version": (1, 0, 0),
    "blender": (4, 20, 0),
    "description": "",
    'tracker_url': "",
    "category": "Node"
}

try:
    import traceback
    import bpy

    from bpy.utils import register_class, unregister_class

    from . import operators, panels, properties, utility

    def register():
        panels.register()
        operators.register()
        properties.register() 

    def unregister():
        panels.unregister()
        operators.unregister()
        properties.unregister()
        

except Exception:
    print(traceback.format_exc())