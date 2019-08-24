import bpy

arm_keymaps = []

def register():
    print("Registering keymapp...")
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Window', space_type='EMPTY', region_type="WINDOW")
    km.keymap_items.new(bpy.ops.tlm.build_lightmaps(), type='F6', value='PRESS')
    arm_keymaps.append(km)

def unregister():
    wm = bpy.context.window_manager
    for km in arm_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    del arm_keymaps[:]