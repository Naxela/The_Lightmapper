"""
Copyright (C) 2024 Alexander "Naxela" Kleemann.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

# file: network/protocol.py
# brief: TCP message protocol for distributed lightmap baking
# author: Alexander "Naxela" Kleemann

import struct
import json
import socket
import time

# ──────────────────────────────────────────────
# Protocol Constants
# ──────────────────────────────────────────────

PROTOCOL_VERSION = 1
HEADER_SIZE = 4  # 4-byte big-endian length prefix

# Message types
MSG_HANDSHAKE       = "handshake"
MSG_HANDSHAKE_ACK   = "handshake_ack"
MSG_HEARTBEAT       = "heartbeat"
MSG_JOB_ASSIGN      = "job_assign"
MSG_JOB_ACCEPT      = "job_accept"
MSG_JOB_PROGRESS    = "job_progress"
MSG_JOB_COMPLETE    = "job_complete"
MSG_JOB_ERROR       = "job_error"
MSG_JOB_CANCEL      = "job_cancel"
MSG_DISCONNECT      = "disconnect"

# Worker states
STATE_IDLE          = "idle"
STATE_BUSY          = "busy"
STATE_ERROR         = "error"
STATE_DISCONNECTED  = "disconnected"

# Timing
HEARTBEAT_INTERVAL  = 5.0    # seconds between heartbeats
HEARTBEAT_TIMEOUT   = 15.0   # seconds before considering worker dead
RECV_TIMEOUT        = 1.0    # socket recv timeout for non-blocking checks

# ──────────────────────────────────────────────
# Message Framing
# ──────────────────────────────────────────────

def _recv_exactly(sock, num_bytes):
    """Receive exactly num_bytes from socket, raising on disconnect."""
    chunks = []
    received = 0
    while received < num_bytes:
        chunk = sock.recv(num_bytes - received)
        if not chunk:
            raise ConnectionError("Connection closed while receiving data")
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def send_message(sock, msg_type, data=None):
    """
    Send a length-prefixed JSON message over a TCP socket.
    
    Args:
        sock: TCP socket
        msg_type: One of the MSG_* constants
        data: Optional dict of additional fields
    """
    message = {"type": msg_type, "timestamp": time.time()}
    if data:
        message.update(data)
    
    payload = json.dumps(message).encode("utf-8")
    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


def recv_message(sock):
    """
    Receive a length-prefixed JSON message from a TCP socket.
    
    Returns:
        dict: The parsed message
        
    Raises:
        ConnectionError: If the connection is closed
        socket.timeout: If the socket times out
    """
    raw_header = _recv_exactly(sock, HEADER_SIZE)
    payload_len = struct.unpack("!I", raw_header)[0]
    
    if payload_len > 10 * 1024 * 1024:  # 10MB safety limit
        raise ValueError(f"Message too large: {payload_len} bytes")
    
    raw_payload = _recv_exactly(sock, payload_len)
    return json.loads(raw_payload.decode("utf-8"))


def try_recv_message(sock, timeout=RECV_TIMEOUT):
    """
    Non-blocking attempt to receive a message.
    
    Returns:
        dict or None: The message if one was available, None on timeout
    """
    old_timeout = sock.gettimeout()
    sock.settimeout(timeout)
    try:
        return recv_message(sock)
    except socket.timeout:
        return None
    except (ConnectionError, OSError):
        return None
    finally:
        sock.settimeout(old_timeout)


# ──────────────────────────────────────────────
# Message Builders
# ──────────────────────────────────────────────

def make_handshake(hostname, blender_version, addon_version, platform_info=""):
    """Build a handshake message from a worker to the coordinator."""
    return {
        "hostname": hostname,
        "blender_version": blender_version,
        "addon_version": addon_version,
        "platform": platform_info,
        "protocol_version": PROTOCOL_VERSION,
    }


def make_handshake_ack(accepted, reason=""):
    """Build a handshake acknowledgement from coordinator to worker."""
    return {
        "accepted": accepted,
        "reason": reason,
    }


def make_job_assign(job_id, blend_path, object_names, output_dir, settings):
    """
    Build a job assignment message.
    
    Args:
        job_id: Unique identifier for this job batch
        blend_path: Absolute path to .blend file on the shared network drive
        object_names: List of object names this worker should bake
        output_dir: Absolute path to the output lightmap directory
        settings: Dict of bake settings (quality, renderer, scale, format, etc.)
    """
    return {
        "job_id": job_id,
        "blend_path": blend_path,
        "object_names": object_names,
        "output_dir": output_dir,
        "settings": settings,
    }


def make_job_progress(job_id, object_name, status, progress=0.0):
    """
    Build a progress report from worker.
    
    Args:
        job_id: The job this progress belongs to
        object_name: Which object is being/was processed
        status: "baking", "saving", "done"
        progress: 0.0 to 1.0 for this worker's total progress
    """
    return {
        "job_id": job_id,
        "object_name": object_name,
        "status": status,
        "progress": progress,
    }


def make_job_complete(job_id, baked_objects):
    """
    Build a job completion message.
    
    Args:
        job_id: The completed job
        baked_objects: List of object names that were successfully baked
    """
    return {
        "job_id": job_id,
        "baked_objects": baked_objects,
    }


def make_job_error(job_id, object_name, error_message):
    """Build an error report from worker."""
    return {
        "job_id": job_id,
        "object_name": object_name,
        "error": error_message,
    }
