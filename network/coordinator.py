"""
Copyright (C) 2024 Alexander "Naxela" Kleemann.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

# file: network/coordinator.py
# brief: Coordinator (master) for distributed lightmap baking
# author: Alexander "Naxela" Kleemann

import socket
import threading
import time
import uuid
import json
import os

from . import protocol

# ──────────────────────────────────────────────
# Worker Tracker
# ──────────────────────────────────────────────

class WorkerInfo:
    """Tracks the state of a connected worker."""
    
    def __init__(self, sock, address):
        self.sock = sock
        self.address = address
        self.hostname = ""
        self.blender_version = ""
        self.addon_version = ""
        self.platform = ""
        self.state = protocol.STATE_IDLE
        self.last_heartbeat = time.time()
        self.assigned_objects = []
        self.completed_objects = []
        self.failed_objects = []
        self.progress = 0.0
        self.current_object = ""
    
    @property
    def is_alive(self):
        return (time.time() - self.last_heartbeat) < protocol.HEARTBEAT_TIMEOUT
    
    @property
    def display_name(self):
        return self.hostname or f"{self.address[0]}:{self.address[1]}"


# ──────────────────────────────────────────────
# Coordinator Server
# ──────────────────────────────────────────────

class TLM_Coordinator:
    """
    TCP server that manages distributed lightmap baking.
    
    Runs a listener thread that accepts worker connections and 
    processes their messages. The coordinator distributes object 
    lists to workers and tracks their progress.
    
    All file I/O happens on a shared network path - no files are
    sent over TCP. Workers read the .blend and write lightmaps
    directly to the shared output directory.
    """
    
    def __init__(self, port=9274):
        self.port = port
        self.workers = {}           # address_key -> WorkerInfo
        self.server_sock = None
        self.running = False
        self.lock = threading.Lock()
        
        # Job tracking
        self.current_job_id = None
        self.total_objects = 0
        self.completed_count = 0
        self.failed_count = 0
        self.job_active = False
        
        # Callbacks for UI integration
        self.on_progress = None     # (progress_float, message_str)
        self.on_worker_connect = None
        self.on_worker_disconnect = None
        self.on_job_complete = None
        self.on_error = None
    
    # ──────────── Server Lifecycle ────────────
    
    def start(self):
        """Start the coordinator server and begin accepting connections."""
        if self.running:
            return
        
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.settimeout(1.0)
        
        try:
            self.server_sock.bind(("0.0.0.0", self.port))
            self.server_sock.listen(16)
        except OSError as e:
            print(f"[TLM-Coordinator] Failed to bind on port {self.port}: {e}")
            self.server_sock.close()
            self.server_sock = None
            raise
        
        self.running = True
        
        # Accept thread
        self._accept_thread = threading.Thread(
            target=self._accept_loop, daemon=True
        )
        self._accept_thread.start()
        
        # Housekeeping thread (prune dead workers)
        self._housekeep_thread = threading.Thread(
            target=self._housekeeping_loop, daemon=True
        )
        self._housekeep_thread.start()
        
        print(f"[TLM-Coordinator] Listening on port {self.port}")
    
    def stop(self):
        """Shut down the coordinator and disconnect all workers."""
        self.running = False
        
        with self.lock:
            for key, worker in list(self.workers.items()):
                try:
                    protocol.send_message(worker.sock, protocol.MSG_DISCONNECT)
                    worker.sock.close()
                except Exception:
                    pass
            self.workers.clear()
        
        if self.server_sock:
            self.server_sock.close()
            self.server_sock = None
        
        print("[TLM-Coordinator] Stopped")
    
    # ──────────── Connection Handling ────────────
    
    def _accept_loop(self):
        """Accept incoming worker connections."""
        while self.running:
            try:
                client_sock, address = self.server_sock.accept()
                client_sock.settimeout(protocol.RECV_TIMEOUT)
                
                # Spawn a handler thread per worker
                handler = threading.Thread(
                    target=self._handle_worker,
                    args=(client_sock, address),
                    daemon=True,
                )
                handler.start()
                
            except socket.timeout:
                continue
            except OSError:
                if self.running:
                    print("[TLM-Coordinator] Accept error")
                break
    
    def _handle_worker(self, sock, address):
        """Handle a single worker connection from handshake to disconnect."""
        key = f"{address[0]}:{address[1]}"
        worker = WorkerInfo(sock, address)
        
        # ── Handshake ──
        try:
            sock.settimeout(10.0)
            msg = protocol.recv_message(sock)
            
            if msg.get("type") != protocol.MSG_HANDSHAKE:
                protocol.send_message(sock, protocol.MSG_HANDSHAKE_ACK,
                    protocol.make_handshake_ack(False, "Expected handshake"))
                sock.close()
                return
            
            worker.hostname = msg.get("hostname", "unknown")
            worker.blender_version = msg.get("blender_version", "unknown")
            worker.addon_version = msg.get("addon_version", "unknown")
            worker.platform = msg.get("platform", "unknown")
            
            # Version check — warn but don't reject for now
            protocol.send_message(sock, protocol.MSG_HANDSHAKE_ACK,
                protocol.make_handshake_ack(True))
            
            print(f"[TLM-Coordinator] Worker connected: {worker.display_name} "
                  f"(Blender {worker.blender_version})")
            
        except Exception as e:
            print(f"[TLM-Coordinator] Handshake failed from {key}: {e}")
            sock.close()
            return
        
        # ── Register worker ──
        with self.lock:
            self.workers[key] = worker
        
        if self.on_worker_connect:
            self.on_worker_connect(worker)
        
        # ── Message loop ──
        sock.settimeout(protocol.RECV_TIMEOUT)
        
        while self.running:
            try:
                msg = protocol.recv_message(sock)
                self._process_worker_message(key, worker, msg)
                
            except socket.timeout:
                continue
            except (ConnectionError, OSError):
                break
            except Exception as e:
                print(f"[TLM-Coordinator] Error from {worker.display_name}: {e}")
                break
        
        # ── Cleanup ──
        worker.state = protocol.STATE_DISCONNECTED
        
        with self.lock:
            self.workers.pop(key, None)
        
        if self.on_worker_disconnect:
            self.on_worker_disconnect(worker)
        
        # If worker had assigned objects and died, mark them as failed
        if worker.assigned_objects and self.job_active:
            remaining = [o for o in worker.assigned_objects 
                        if o not in worker.completed_objects]
            if remaining:
                self._handle_worker_failure(worker, remaining)
        
        try:
            sock.close()
        except Exception:
            pass
        
        print(f"[TLM-Coordinator] Worker disconnected: {worker.display_name}")
    
    def _process_worker_message(self, key, worker, msg):
        """Route an incoming worker message to the appropriate handler."""
        msg_type = msg.get("type")
        
        if msg_type == protocol.MSG_HEARTBEAT:
            worker.last_heartbeat = time.time()
        
        elif msg_type == protocol.MSG_JOB_ACCEPT:
            worker.state = protocol.STATE_BUSY
            print(f"[TLM-Coordinator] {worker.display_name} accepted job")
        
        elif msg_type == protocol.MSG_JOB_PROGRESS:
            worker.last_heartbeat = time.time()
            worker.current_object = msg.get("object_name", "")
            worker.progress = msg.get("progress", 0.0)
            status = msg.get("status", "")
            
            if status == "done":
                obj_name = msg.get("object_name", "")
                if obj_name and obj_name not in worker.completed_objects:
                    worker.completed_objects.append(obj_name)
                    with self.lock:
                        self.completed_count += 1
            
            # Report aggregate progress
            if self.on_progress and self.total_objects > 0:
                aggregate = (self.completed_count + self.failed_count) / self.total_objects
                self.on_progress(
                    aggregate,
                    f"Baking {worker.current_object} on {worker.display_name}"
                )
        
        elif msg_type == protocol.MSG_JOB_COMPLETE:
            baked = msg.get("baked_objects", [])
            worker.state = protocol.STATE_IDLE
            print(f"[TLM-Coordinator] {worker.display_name} completed: {baked}")
            
            self._check_job_finished()
        
        elif msg_type == protocol.MSG_JOB_ERROR:
            obj_name = msg.get("object_name", "unknown")
            error = msg.get("error", "unknown error")
            worker.failed_objects.append(obj_name)
            
            with self.lock:
                self.failed_count += 1
            
            print(f"[TLM-Coordinator] Error on {worker.display_name}: "
                  f"{obj_name} - {error}")
            
            if self.on_error:
                self.on_error(worker.display_name, obj_name, error)
        
        elif msg_type == protocol.MSG_DISCONNECT:
            raise ConnectionError("Worker disconnecting")
    
    # ──────────── Job Distribution ────────────
    
    def get_available_workers(self):
        """Return list of idle, alive workers."""
        with self.lock:
            return [w for w in self.workers.values() 
                    if w.state == protocol.STATE_IDLE and w.is_alive]
    
    def get_worker_count(self):
        """Return number of connected, alive workers."""
        with self.lock:
            return sum(1 for w in self.workers.values() if w.is_alive)
    
    def distribute_job(self, blend_path, object_names, output_dir, settings):
        """
        Distribute a bake job across all available workers.
        
        Args:
            blend_path: Absolute path to .blend file on shared storage
            object_names: Full list of objects to bake
            output_dir: Absolute path to lightmap output directory
            settings: Dict with keys: quality, renderer, scale, format, 
                      dilation_margin
        
        Returns:
            bool: True if job was distributed, False if no workers available
        """
        workers = self.get_available_workers()
        if not workers:
            print("[TLM-Coordinator] No workers available")
            return False
        
        self.current_job_id = str(uuid.uuid4())[:8]
        self.total_objects = len(object_names)
        self.completed_count = 0
        self.failed_count = 0
        self.job_active = True
        
        # Round-robin distribution
        chunks = self._split_objects(object_names, len(workers))
        
        print(f"[TLM-Coordinator] Distributing {len(object_names)} objects "
              f"across {len(workers)} workers (job {self.current_job_id})")
        
        for worker, chunk in zip(workers, chunks):
            if not chunk:
                continue
            
            worker.assigned_objects = chunk
            worker.completed_objects = []
            worker.failed_objects = []
            worker.progress = 0.0
            
            job_data = protocol.make_job_assign(
                job_id=self.current_job_id,
                blend_path=blend_path,
                object_names=chunk,
                output_dir=output_dir,
                settings=settings,
            )
            
            try:
                protocol.send_message(worker.sock, protocol.MSG_JOB_ASSIGN, job_data)
                print(f"[TLM-Coordinator] Assigned {len(chunk)} objects to "
                      f"{worker.display_name}: {chunk}")
            except Exception as e:
                print(f"[TLM-Coordinator] Failed to send job to "
                      f"{worker.display_name}: {e}")
                worker.state = protocol.STATE_ERROR
        
        return True
    
    def cancel_job(self):
        """Send cancel to all busy workers."""
        with self.lock:
            for worker in self.workers.values():
                if worker.state == protocol.STATE_BUSY:
                    try:
                        protocol.send_message(
                            worker.sock, protocol.MSG_JOB_CANCEL,
                            {"job_id": self.current_job_id}
                        )
                    except Exception:
                        pass
        
        self.job_active = False
        print("[TLM-Coordinator] Job cancelled")
    
    def is_job_finished(self):
        """Check if all objects have been baked or failed."""
        if not self.job_active:
            return True
        return (self.completed_count + self.failed_count) >= self.total_objects
    
    # ──────────── Internal Helpers ────────────
    
    @staticmethod
    def _split_objects(object_names, num_workers):
        """Split object list into roughly equal chunks for each worker."""
        chunks = [[] for _ in range(num_workers)]
        for i, name in enumerate(object_names):
            chunks[i % num_workers].append(name)
        return chunks
    
    def _check_job_finished(self):
        """Check if the entire job is done and fire callback."""
        if self.is_job_finished():
            self.job_active = False
            
            all_completed = []
            all_failed = []
            with self.lock:
                for w in self.workers.values():
                    all_completed.extend(w.completed_objects)
                    all_failed.extend(w.failed_objects)
            
            print(f"[TLM-Coordinator] Job {self.current_job_id} finished: "
                  f"{len(all_completed)} completed, {len(all_failed)} failed")
            
            if self.on_job_complete:
                self.on_job_complete(all_completed, all_failed)
    
    def _handle_worker_failure(self, worker, remaining_objects):
        """Handle objects that were assigned to a worker that died."""
        print(f"[TLM-Coordinator] Worker {worker.display_name} died with "
              f"unfinished objects: {remaining_objects}")
        
        with self.lock:
            self.failed_count += len(remaining_objects)
        
        for obj_name in remaining_objects:
            if self.on_error:
                self.on_error(
                    worker.display_name, obj_name,
                    "Worker disconnected before completing"
                )
        
        self._check_job_finished()
    
    def _housekeeping_loop(self):
        """Periodically check for dead workers."""
        while self.running:
            time.sleep(protocol.HEARTBEAT_INTERVAL)
            
            dead_keys = []
            with self.lock:
                for key, worker in self.workers.items():
                    if not worker.is_alive and worker.state != protocol.STATE_DISCONNECTED:
                        dead_keys.append(key)
            
            for key in dead_keys:
                with self.lock:
                    worker = self.workers.get(key)
                if worker:
                    print(f"[TLM-Coordinator] Worker timed out: {worker.display_name}")
                    try:
                        worker.sock.close()
                    except Exception:
                        pass
