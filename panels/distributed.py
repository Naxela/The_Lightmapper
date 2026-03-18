"""
Copyright (C) 2024 Alexander "Naxela" Kleemann.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

# file: panels/distributed.py
# brief: UI panel for distributed lightmap baking
# author: Alexander "Naxela" Kleemann

import bpy
from bpy.types import Panel
from ..operators.distributed import get_coordinator, get_worker


class TLM_PT_Distributed(bpy.types.Panel):
    bl_label = "Distributed Baking"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "TLM_PT_Panel"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.TLM_SceneProperties
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        # ── Role Selection ──
        row = layout.row(align=True)
        row.prop(props, "tlm_dist_role", expand=True)
        
        layout.separator()
        
        # ── Common Settings ──
        row = layout.row(align=True)
        row.prop(props, "tlm_dist_port")
        
        # ── Coordinator Mode ──
        if props.tlm_dist_role == "COORDINATOR":
            self._draw_coordinator(layout, props)
        
        # ── Worker Mode ──
        else:
            self._draw_worker(layout, props)
    
    def _draw_coordinator(self, layout, props):
        coordinator = get_coordinator()
        is_running = coordinator is not None and coordinator.running
        
        # Status
        box = layout.box()
        row = box.row()
        if is_running:
            row.label(text="Status: Running", icon='PLAY')
            
            # Worker count
            worker_count = coordinator.get_worker_count() if coordinator else 0
            row = box.row()
            row.label(text=f"Connected Workers: {worker_count}", icon='COMMUNITY')
            
            # Worker list
            if coordinator and coordinator.workers:
                for key, worker in coordinator.workers.items():
                    row = box.row()
                    state_icon = 'RADIOBUT_ON' if worker.is_alive else 'RADIOBUT_OFF'
                    status = worker.state
                    if worker.current_object:
                        status = f"Baking: {worker.current_object}"
                    row.label(text=f"  {worker.display_name} [{status}]", 
                             icon=state_icon)
        else:
            row.label(text="Status: Stopped", icon='PAUSE')
        
        # Start/Stop
        layout.separator()
        row = layout.row(align=True)
        if is_running:
            row.operator("tlm.stop_coordinator", icon='CANCEL')
            
            # Distributed build button
            layout.separator()
            row = layout.row(align=True)
            row.scale_y = 1.5
            row.operator("tlm.build_lightmaps_distributed", icon='RENDER_STILL')
        else:
            row.operator("tlm.start_coordinator", icon='PLAY')
    
    def _draw_worker(self, layout, props):
        worker = get_worker()
        is_connected = worker is not None and worker.is_connected()
        
        # Coordinator address
        row = layout.row(align=True)
        row.prop(props, "tlm_dist_coordinator_address")
        
        # Status
        box = layout.box()
        row = box.row()
        if is_connected:
            row.label(text="Status: Connected", icon='CHECKMARK')
            if worker.current_job_id:
                row = box.row()
                row.label(text=f"Job: {worker.current_job_id}", icon='RENDER_STILL')
        else:
            row.label(text="Status: Disconnected", icon='UNLINKED')
        
        # Connect/Disconnect
        layout.separator()
        row = layout.row(align=True)
        if is_connected:
            row.operator("tlm.stop_worker", icon='CANCEL')
        else:
            row.operator("tlm.start_worker", icon='LINKED')


# ──────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────

classes = [
    TLM_PT_Distributed,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
