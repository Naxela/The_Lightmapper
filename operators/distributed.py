"""
Copyright (C) 2024 Alexander "Naxela" Kleemann.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

# file: operators/distributed.py
# brief: Blender operators for distributed lightmap baking
# author: Alexander "Naxela" Kleemann

import bpy
import os
import threading
from queue import Queue, Empty

from ..network.coordinator import TLM_Coordinator
from ..network.worker import TLM_Worker
from ..utility import util

# ──────────────────────────────────────────────
# Module-level singletons
# ──────────────────────────────────────────────

_coordinator = None
_worker = None
_message_queue = Queue()  # Thread-safe queue for UI updates


def get_coordinator():
    global _coordinator
    return _coordinator


def get_worker():
    global _worker
    return _worker


# ──────────────────────────────────────────────
# Coordinator Operators
# ──────────────────────────────────────────────

class TLM_OT_start_coordinator(bpy.types.Operator):
    bl_idname = "tlm.start_coordinator"
    bl_label = "Start Coordinator"
    bl_description = "Start listening for worker connections"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        global _coordinator
        
        if _coordinator and _coordinator.running:
            self.report({'WARNING'}, "Coordinator is already running")
            return {'CANCELLED'}
        
        scene = context.scene
        port = scene.TLM_SceneProperties.tlm_dist_port
        
        try:
            _coordinator = TLM_Coordinator(port=port)
            
            # Wire up callbacks that post to the thread-safe queue
            _coordinator.on_progress = lambda p, m: _message_queue.put(("progress", p, m))
            _coordinator.on_worker_connect = lambda w: _message_queue.put(("worker_connect", w.display_name))
            _coordinator.on_worker_disconnect = lambda w: _message_queue.put(("worker_disconnect", w.display_name))
            _coordinator.on_job_complete = lambda c, f: _message_queue.put(("job_complete", c, f))
            _coordinator.on_error = lambda w, o, e: _message_queue.put(("error", w, o, e))
            
            _coordinator.start()
            
            scene.TLM_SceneProperties.tlm_dist_coordinator_status = f"Listening on port {port}"
            self.report({'INFO'}, f"Coordinator started on port {port}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to start coordinator: {e}")
            _coordinator = None
            return {'CANCELLED'}
        
        return {'FINISHED'}


class TLM_OT_stop_coordinator(bpy.types.Operator):
    bl_idname = "tlm.stop_coordinator"
    bl_label = "Stop Coordinator"
    bl_description = "Stop the coordinator and disconnect all workers"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        global _coordinator
        
        if not _coordinator or not _coordinator.running:
            self.report({'WARNING'}, "Coordinator is not running")
            return {'CANCELLED'}
        
        _coordinator.stop()
        _coordinator = None
        
        context.scene.TLM_SceneProperties.tlm_dist_coordinator_status = "Stopped"
        self.report({'INFO'}, "Coordinator stopped")
        
        return {'FINISHED'}


# ──────────────────────────────────────────────
# Worker Operators
# ──────────────────────────────────────────────

class TLM_OT_start_worker(bpy.types.Operator):
    bl_idname = "tlm.start_worker"
    bl_label = "Start Worker"
    bl_description = "Connect to a coordinator and listen for bake jobs"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        global _worker
        
        if _worker and _worker.is_connected():
            self.report({'WARNING'}, "Worker is already connected")
            return {'CANCELLED'}
        
        scene = context.scene
        host = scene.TLM_SceneProperties.tlm_dist_coordinator_address
        port = scene.TLM_SceneProperties.tlm_dist_port
        
        try:
            _worker = TLM_Worker(blender_path=bpy.app.binary_path)
            
            _worker.on_connected = lambda: _message_queue.put(("worker_connected",))
            _worker.on_disconnected = lambda: _message_queue.put(("worker_disconnected",))
            _worker.on_job_started = lambda j, o: _message_queue.put(("job_started", j, o))
            _worker.on_job_finished = lambda j: _message_queue.put(("job_finished", j))
            
            _worker.connect(host, port)
            
            scene.TLM_SceneProperties.tlm_dist_worker_status = f"Connected to {host}:{port}"
            self.report({'INFO'}, f"Worker connected to {host}:{port}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to connect: {e}")
            _worker = None
            return {'CANCELLED'}
        
        return {'FINISHED'}


class TLM_OT_stop_worker(bpy.types.Operator):
    bl_idname = "tlm.stop_worker"
    bl_label = "Stop Worker"
    bl_description = "Disconnect from the coordinator"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        global _worker
        
        if not _worker:
            self.report({'WARNING'}, "Worker is not running")
            return {'CANCELLED'}
        
        _worker.disconnect()
        _worker = None
        
        context.scene.TLM_SceneProperties.tlm_dist_worker_status = "Disconnected"
        self.report({'INFO'}, "Worker disconnected")
        
        return {'FINISHED'}


# ──────────────────────────────────────────────
# Distributed Build Operator
# ──────────────────────────────────────────────

class TLM_OT_build_lightmaps_distributed(bpy.types.Operator):
    bl_idname = "tlm.build_lightmaps_distributed"
    bl_label = "Build Lightmaps (Distributed)"
    bl_description = "Distribute lightmap baking across connected workers"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    
    def execute(self, context):
        global _coordinator
        
        if not _coordinator or not _coordinator.running:
            self.report({'ERROR'}, "Coordinator is not running. Start it first.")
            return {'CANCELLED'}
        
        worker_count = _coordinator.get_worker_count()
        if worker_count == 0:
            self.report({'ERROR'}, "No workers connected")
            return {'CANCELLED'}
        
        scene = context.scene
        
        # Ensure file is saved
        if not util.ensureFilesave():
            self.report({'ERROR'}, "Please save the .blend file first")
            return {'CANCELLED'}
        
        # Prepare objects (UV unwrap, material setup) on coordinator side
        # This modifies the .blend and saves it so workers see the changes
        from ..utility import unwrap
        
        if scene.TLM_SceneProperties.tlm_reset_lightmap_uv:
            for obj in scene.objects:
                if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                    if obj.type == "MESH":
                        uv_layers = obj.data.uv_layers
                        for name in ["UVMap-Lightmap", "UVMap_Lightmap"]:
                            for uvlayer in uv_layers:
                                if uvlayer.name == name:
                                    uv_layers.remove(uvlayer)
        
        util.removeLightmapFolder()
        util.configureEngine()
        unwrap.prepareObjectsForBaking()
        
        # Gather the object list
        obj_list = [
            obj.name for obj in scene.objects
            if obj.type == 'MESH'
            and hasattr(obj, 'TLM_ObjectProperties')
            and obj.TLM_ObjectProperties.tlm_mesh_lightmap_use
        ]
        
        if not obj_list:
            self.report({'WARNING'}, "No objects marked for lightmapping")
            return {'CANCELLED'}
        
        # Build paths — these must be absolute paths accessible on the 
        # shared network storage
        blend_path = bpy.data.filepath
        lightmap_dir = bpy.path.abspath(
            "//" + scene.TLM_SceneProperties.tlm_setting_savedir
        )
        os.makedirs(lightmap_dir, exist_ok=True)
        
        # Collect settings
        settings = {
            "quality": scene.TLM_SceneProperties.tlm_quality,
            "renderer": scene.TLM_SceneProperties.tlm_setting_renderer,
            "scale": scene.TLM_SceneProperties.tlm_setting_scale,
            "format": scene.TLM_SceneProperties.tlm_format,
            "dilation_margin": scene.TLM_SceneProperties.tlm_dilation_margin,
        }
        
        # Distribute
        success = _coordinator.distribute_job(
            blend_path=blend_path,
            object_names=obj_list,
            output_dir=lightmap_dir,
            settings=settings,
        )
        
        if not success:
            self.report({'ERROR'}, "Failed to distribute job — no available workers")
            return {'CANCELLED'}
        
        self.report({'INFO'}, 
            f"Distributed {len(obj_list)} objects to {worker_count} workers")
        
        # Start modal timer to poll for completion
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        global _coordinator
        
        if event.type == 'TIMER':
            # Drain the message queue for UI updates
            while not _message_queue.empty():
                try:
                    msg = _message_queue.get_nowait()
                    self._handle_ui_message(context, msg)
                except Empty:
                    break
            
            # Check if job is done
            if _coordinator and _coordinator.is_job_finished():
                return self.finish(context)
        
        return {'PASS_THROUGH'}
    
    def _handle_ui_message(self, context, msg):
        """Process a message from the coordinator callbacks."""
        msg_type = msg[0]
        
        if msg_type == "progress":
            progress, message = msg[1], msg[2]
            context.scene["baking_progress"] = progress
            print(f"[TLM-Distributed] {progress:.1%} - {message}")
        
        elif msg_type == "worker_connect":
            print(f"[TLM-Distributed] Worker connected: {msg[1]}")
        
        elif msg_type == "worker_disconnect":
            print(f"[TLM-Distributed] Worker disconnected: {msg[1]}")
        
        elif msg_type == "error":
            worker_name, obj_name, error = msg[1], msg[2], msg[3]
            print(f"[TLM-Distributed] Error from {worker_name}: {obj_name} - {error}")
        
        elif msg_type == "job_complete":
            completed, failed = msg[1], msg[2]
            print(f"[TLM-Distributed] Job complete: "
                  f"{len(completed)} done, {len(failed)} failed")
    
    def finish(self, context):
        """Clean up after job completion and run post-processing."""
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        
        # Post-process (denoising, KTX conversion, UV reset)
        util.postprocessBuild()
        
        self.report({'INFO'}, "Distributed lightmap baking complete")
        return {'CANCELLED'}
    
    def cancel(self, context):
        global _coordinator
        
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        
        if _coordinator and _coordinator.job_active:
            _coordinator.cancel_job()


# ──────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────

classes = [
    TLM_OT_start_coordinator,
    TLM_OT_stop_coordinator,
    TLM_OT_start_worker,
    TLM_OT_stop_worker,
    TLM_OT_build_lightmaps_distributed,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    # Clean up singletons
    global _coordinator, _worker
    
    if _coordinator:
        _coordinator.stop()
        _coordinator = None
    if _worker:
        _worker.disconnect()
        _worker = None
    
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
