"""
Copyright (C) 2024 Alexander "Naxela" Kleemann.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

# file: network/worker.py
# brief: Worker (slave) for distributed lightmap baking
# author: Alexander "Naxela" Kleemann

import socket
import threading
import subprocess
import platform
import time
import os
import sys
import json
import tempfile

from . import protocol


class TLM_Worker:
    """
    Worker node that connects to a coordinator and executes bake jobs.
    
    The worker:
    1. Connects to the coordinator via TCP
    2. Sends periodic heartbeats
    3. Receives job assignments (blend path + object list + settings)
    4. Launches Blender in background mode to bake the assigned objects
    5. Reports progress back to the coordinator
    6. Writes output directly to the shared network directory
    
    No files are transferred over TCP - everything is read/written
    on the shared network storage.
    """
    
    def __init__(self, blender_path=None):
        self.sock = None
        self.connected = False
        self.running = False
        self.lock = threading.Lock()
        
        # Blender executable path
        self.blender_path = blender_path or self._find_blender()
        
        # Current job
        self.current_job_id = None
        self.bake_process = None
        self.cancelled = False
        
        # Callbacks
        self.on_status_change = None  # (status_str, detail_str)
        self.on_connected = None
        self.on_disconnected = None
        self.on_job_started = None
        self.on_job_finished = None
    
    # ──────────── Connection ────────────
    
    def connect(self, host, port=9274):
        """
        Connect to a coordinator and begin the worker loop.
        
        Args:
            host: Coordinator IP address or hostname
            port: Coordinator port
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10.0)
        
        try:
            self.sock.connect((host, port))
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            print(f"[TLM-Worker] Failed to connect to {host}:{port}: {e}")
            self.sock.close()
            self.sock = None
            raise
        
        # Send handshake
        handshake = protocol.make_handshake(
            hostname=platform.node(),
            blender_version=self._get_blender_version(),
            addon_version="1.0.0",
            platform_info=f"{platform.system()} {platform.machine()}",
        )
        protocol.send_message(self.sock, protocol.MSG_HANDSHAKE, handshake)
        
        # Wait for ack
        self.sock.settimeout(10.0)
        ack = protocol.recv_message(self.sock)
        
        if ack.get("type") != protocol.MSG_HANDSHAKE_ACK or not ack.get("accepted"):
            reason = ack.get("reason", "Unknown reason")
            print(f"[TLM-Worker] Connection rejected: {reason}")
            self.sock.close()
            self.sock = None
            raise ConnectionError(f"Handshake rejected: {reason}")
        
        self.connected = True
        self.running = True
        print(f"[TLM-Worker] Connected to coordinator at {host}:{port}")
        
        if self.on_connected:
            self.on_connected()
        
        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()
        
        # Start main message loop
        self._listen_thread = threading.Thread(
            target=self._message_loop, daemon=True
        )
        self._listen_thread.start()
    
    def disconnect(self):
        """Cleanly disconnect from the coordinator."""
        self.running = False
        self.connected = False
        
        if self.bake_process and self.bake_process.poll() is None:
            self.bake_process.terminate()
        
        if self.sock:
            try:
                protocol.send_message(self.sock, protocol.MSG_DISCONNECT)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        
        if self.on_disconnected:
            self.on_disconnected()
        
        print("[TLM-Worker] Disconnected")
    
    def is_connected(self):
        return self.connected and self.running
    
    # ──────────── Message Handling ────────────
    
    def _message_loop(self):
        """Main loop: listen for messages from coordinator."""
        self.sock.settimeout(protocol.RECV_TIMEOUT)
        
        while self.running:
            try:
                msg = protocol.recv_message(self.sock)
                self._handle_message(msg)
            except socket.timeout:
                continue
            except (ConnectionError, OSError):
                if self.running:
                    print("[TLM-Worker] Lost connection to coordinator")
                break
            except Exception as e:
                print(f"[TLM-Worker] Message error: {e}")
                continue
        
        self.connected = False
        if self.on_disconnected:
            self.on_disconnected()
    
    def _handle_message(self, msg):
        """Route incoming coordinator messages."""
        msg_type = msg.get("type")
        
        if msg_type == protocol.MSG_JOB_ASSIGN:
            self._handle_job_assign(msg)
        
        elif msg_type == protocol.MSG_JOB_CANCEL:
            self._handle_job_cancel(msg)
        
        elif msg_type == protocol.MSG_DISCONNECT:
            self.running = False
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to the coordinator."""
        while self.running and self.connected:
            try:
                protocol.send_message(self.sock, protocol.MSG_HEARTBEAT)
            except (ConnectionError, OSError):
                if self.running:
                    print("[TLM-Worker] Failed to send heartbeat")
                    self.connected = False
                break
            
            time.sleep(protocol.HEARTBEAT_INTERVAL)
    
    # ──────────── Job Execution ────────────
    
    def _handle_job_assign(self, msg):
        """Handle an incoming bake job assignment."""
        self.current_job_id = msg.get("job_id", "")
        blend_path = msg.get("blend_path", "")
        object_names = msg.get("object_names", [])
        output_dir = msg.get("output_dir", "")
        settings = msg.get("settings", {})
        
        print(f"[TLM-Worker] Received job {self.current_job_id}: "
              f"{len(object_names)} objects from {blend_path}")
        
        # Acknowledge
        protocol.send_message(self.sock, protocol.MSG_JOB_ACCEPT,
            {"job_id": self.current_job_id})
        
        if self.on_job_started:
            self.on_job_started(self.current_job_id, object_names)
        
        self.cancelled = False
        
        # Run the bake in a thread so we don't block the message loop
        bake_thread = threading.Thread(
            target=self._execute_bake,
            args=(blend_path, object_names, output_dir, settings),
            daemon=True,
        )
        bake_thread.start()
    
    def _handle_job_cancel(self, msg):
        """Handle a cancel request from coordinator."""
        self.cancelled = True
        
        if self.bake_process and self.bake_process.poll() is None:
            print("[TLM-Worker] Cancelling active bake process")
            self.bake_process.terminate()
    
    def _execute_bake(self, blend_path, object_names, output_dir, settings):
        """
        Execute the bake by generating a worker build script and 
        running Blender in background mode.
        """
        job_id = self.current_job_id
        
        # Validate paths exist on the shared storage
        if not os.path.exists(blend_path):
            self._report_error(job_id, "", 
                f"Blend file not found: {blend_path}")
            return
        
        # Make sure output dir exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the worker build script
        script_content = self._generate_build_script(
            object_names, output_dir, settings
        )
        
        # Write script to a temp file next to the blend file
        script_dir = os.path.dirname(blend_path)
        script_path = os.path.join(
            script_dir, f"_tlm_worker_{job_id}.py"
        )
        
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)
        except OSError as e:
            self._report_error(job_id, "", f"Cannot write build script: {e}")
            return
        
        # Launch Blender in background
        cmd = [
            self.blender_path,
            blend_path,
            "--background",
            "--python", script_path,
        ]
        
        print(f"[TLM-Worker] Launching: {' '.join(cmd)}")
        
        try:
            self.bake_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
                encoding="utf-8",
            )
            
            baked_objects = []
            
            # Read stdout for progress messages
            for line in iter(self.bake_process.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                
                if self.cancelled:
                    self.bake_process.terminate()
                    break
                
                # Parse [TLM] protocol messages from the subprocess
                if line.startswith("[TLM]"):
                    self._parse_bake_output(job_id, line, object_names, baked_objects)
                else:
                    # Forward other output for debugging
                    print(f"[TLM-Worker:bake] {line}")
            
            self.bake_process.wait()
            
            if self.cancelled:
                print(f"[TLM-Worker] Job {job_id} was cancelled")
                return
            
            if self.bake_process.returncode != 0:
                stderr = self.bake_process.stderr.read()
                self._report_error(job_id, "", 
                    f"Blender exited with code {self.bake_process.returncode}: {stderr[:500]}")
            else:
                # Report completion
                complete_data = protocol.make_job_complete(job_id, baked_objects)
                protocol.send_message(
                    self.sock, protocol.MSG_JOB_COMPLETE, complete_data
                )
                print(f"[TLM-Worker] Job {job_id} completed: {baked_objects}")
            
        except Exception as e:
            self._report_error(job_id, "", f"Bake process error: {e}")
        
        finally:
            # Clean up temp script
            try:
                if os.path.exists(script_path):
                    os.remove(script_path)
            except Exception:
                pass
            
            self.bake_process = None
            self.current_job_id = None
            
            if self.on_job_finished:
                self.on_job_finished(job_id)
    
    def _parse_bake_output(self, job_id, line, all_objects, baked_objects):
        """Parse a [TLM]:key:value line from the bake subprocess."""
        parts = line.split(":")
        if len(parts) < 3:
            return
        
        key_type = parts[1].strip()
        value = parts[2].strip()
        
        if key_type == "0":
            # Progress update
            try:
                progress = float(value)
                # Figure out which object we're on based on progress
                idx = min(int(progress * len(all_objects)), len(all_objects) - 1)
                current_obj = all_objects[idx] if all_objects else ""
                
                progress_data = protocol.make_job_progress(
                    job_id, current_obj, "baking", progress
                )
                protocol.send_message(
                    self.sock, protocol.MSG_JOB_PROGRESS, progress_data
                )
            except (ValueError, IndexError):
                pass
        
        elif key_type == "1":
            # Info message — check if it mentions finishing an object
            if "Baking object" in value:
                # Extract object name from "Baking object 'Name' with..."
                try:
                    obj_name = value.split("'")[1]
                    baked_objects.append(obj_name)
                    
                    progress_data = protocol.make_job_progress(
                        job_id, obj_name, "done",
                        len(baked_objects) / len(all_objects) if all_objects else 1.0
                    )
                    protocol.send_message(
                        self.sock, protocol.MSG_JOB_PROGRESS, progress_data
                    )
                except (IndexError, ZeroDivisionError):
                    pass
            
            print(f"[TLM-Worker:info] {value}")
        
        elif key_type == "2":
            # Error from bake
            print(f"[TLM-Worker:error] {value}")
            # Try to extract object name from error
            obj_name = ""
            if "Error baking" in value:
                try:
                    obj_name = value.split("Error baking")[1].strip().split(" ")[0]
                except IndexError:
                    pass
            
            self._report_error(job_id, obj_name, value)
    
    def _report_error(self, job_id, object_name, error_message):
        """Send an error report to the coordinator."""
        try:
            error_data = protocol.make_job_error(job_id, object_name, error_message)
            protocol.send_message(self.sock, protocol.MSG_JOB_ERROR, error_data)
        except Exception as e:
            print(f"[TLM-Worker] Could not report error: {e}")
    
    # ──────────── Build Script Generation ────────────
    
    def _generate_build_script(self, object_names, output_dir, settings):
        """
        Generate a Python build script that Blender will execute in 
        background mode. This is a modified version of _build_script.py
        that only bakes the assigned object list.
        """
        obj_list_json = json.dumps(object_names)
        output_dir_escaped = output_dir.replace("\\", "\\\\")
        
        quality = settings.get("quality", "0")
        renderer = settings.get("renderer", "CPU")
        scale = settings.get("scale", "1")
        fmt = settings.get("format", "HDR")
        dilation = settings.get("dilation_margin", 4)
        
        script = f'''import bpy, os, json, math

# ── Worker Build Script (auto-generated) ──
# Only bakes the objects assigned by the coordinator.

class TLMWorkerBuilder:
    
    def __init__(self, obj_list, output_dir):
        self.obj_list = obj_list
        self.abs_dir = output_dir
        if not os.path.exists(self.abs_dir):
            os.makedirs(self.abs_dir)
    
    def configure_engine(self):
        scene = bpy.context.scene
        cycles = scene.cycles
        scene.render.engine = "CYCLES"
        cycles.device = "{renderer}"
        
        if cycles.device == "GPU":
            cycles.tile_size = 256
        else:
            cycles.tile_size = 32
        
        quality_settings = {{
            "0": (32, 1),
            "1": (64, 2),
            "2": (512, 2),
            "3": (1024, 256),
            "4": (2048, 512),
        }}
        
        quality = "{quality}"
        if quality in quality_settings:
            samples, bounces = quality_settings[quality]
            cycles.samples = samples
            cycles.max_bounces = bounces
            cycles.diffuse_bounces = bounces
            cycles.glossy_bounces = bounces
            cycles.transparent_max_bounces = bounces
            cycles.transmission_bounces = bounces
            cycles.volume_bounces = bounces
    
    def create_bake_images(self, obj):
        img_name = "TLM-" + obj.name
        if img_name not in bpy.data.images:
            resolution = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) // {scale}
            image = bpy.data.images.new(
                img_name, resolution, resolution, 
                alpha=True, float_buffer=True
            )
        
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            
            nodes = mat.node_tree.nodes
            if "TLM-Lightmap" in nodes:
                nodes["TLM-Lightmap"].image = bpy.data.images[img_name]
                nodes.active = nodes["TLM-Lightmap"]
            else:
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.name = "TLM-Lightmap"
                img_node.location = (100, 100)
                img_node.image = bpy.data.images[img_name]
                nodes.active = img_node
        
        mesh = obj.data
        if "UVMap-Lightmap" in mesh.uv_layers:
            mesh.uv_layers.active = mesh.uv_layers["UVMap-Lightmap"]
    
    def bake_object(self, obj):
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if len(obj.material_slots) != 0:
            try:
                bake_mode = bpy.context.scene.TLM_SceneProperties.tlm_bake_mode
                if bake_mode == 'AO':
                    bpy.ops.object.bake(type="AO", margin={dilation}, use_clear=True)
                else:
                    bpy.ops.object.bake(type="DIFFUSE", pass_filter={{"DIRECT", "INDIRECT"}}, margin={dilation}, use_clear=True)
                print(f"[TLM]:1:Baking object '{{obj.name}}' ({{bake_mode}})...", flush=True)
            except RuntimeError as e:
                msg = str(e).replace(":", " - ")
                print(f"[TLM]:2:Error baking {{obj.name}} - {{msg}}", flush=True)
    
    def save_lightmaps(self, obj):
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            nodes = mat.node_tree.nodes
            if "TLM-Lightmap" in nodes:
                image = nodes["TLM-Lightmap"].image
                if image:
                    fmt = "{fmt}"
                    if fmt == "EXR" or fmt == "KTX":
                        ext = ".exr"
                        image.file_format = "OPEN_EXR"
                    else:
                        ext = ".hdr"
                        image.file_format = "HDR"
                    
                    filepath = os.path.join(self.abs_dir, image.name + ext)
                    image.filepath_raw = filepath
                    image.save()
                    print(f"[TLM]:1:Saved lightmap: {{filepath}}", flush=True)
    
    def bake_objects_and_report_progress(self):
        print("[TLM]:1:Worker starting bake process...", flush=True)
        print("[TLM]:0:0.0", flush=True)
        
        self.configure_engine()
        
        total = len(self.obj_list)
        for index, obj_name in enumerate(self.obj_list):
            obj = bpy.data.objects.get(obj_name)
            if obj is None:
                print(f"[TLM]:2:Error baking {{obj_name}} - Object not found in scene", flush=True)
                continue
            
            self.create_bake_images(obj)
            self.bake_object(obj)
            self.save_lightmaps(obj)
            print(f"[TLM]:0:{{(index + 1) / total}}", flush=True)
        
        print("[TLM]:1:Worker finished bake process.", flush=True)


# ── Run ──
obj_list = {obj_list_json}
output_dir = r"{output_dir_escaped}"

builder = TLMWorkerBuilder(obj_list, output_dir)
builder.bake_objects_and_report_progress()
'''
        return script
    
    # ──────────── Utility ────────────
    
    @staticmethod
    def _find_blender():
        """Try to find the Blender executable."""
        # Check if we're running inside Blender
        try:
            import bpy
            return bpy.app.binary_path
        except ImportError:
            pass
        
        # Common paths
        system = platform.system()
        candidates = []
        
        if system == "Windows":
            # Check Program Files
            for base in [os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                         os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")]:
                if base:
                    blender_dir = os.path.join(base, "Blender Foundation")
                    if os.path.exists(blender_dir):
                        for sub in sorted(os.listdir(blender_dir), reverse=True):
                            candidates.append(
                                os.path.join(blender_dir, sub, "blender.exe")
                            )
        elif system == "Darwin":
            candidates.append("/Applications/Blender.app/Contents/MacOS/Blender")
        else:  # Linux
            candidates.append("/usr/bin/blender")
            candidates.append("/snap/bin/blender")
        
        for path in candidates:
            if os.path.exists(path):
                return path
        
        # Fall back to PATH
        return "blender"
    
    @staticmethod
    def _get_blender_version():
        """Get the Blender version string."""
        try:
            import bpy
            v = bpy.app.version
            return f"{v[0]}.{v[1]}.{v[2]}"
        except ImportError:
            return "unknown"
