#!/usr/bin/env python3

import socket, json, subprocess, os, platform, subprocess

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
#PORT = 9898        # Port to listen on (non-privileged ports are > 1023)

blenderPath = r"C:\Program Files\Blender Foundation\Blender 2.90\blender.exe"

def evalIncoming(inc_socket, connection , inc, args=[blenderPath]):

    if inc["call"] == 0: #Ping
        print("Pinged by: " + str(connection.getsockname()))
        connection.sendall(("Ping callback").encode())
        
    elif inc["call"] == 1: #Command

        print("Command: " + str(inc["command"]))

        if inc["command"] == 0: #Shutdown
            open_socket = False
            try:
                inc_socket.shutdown(socket.SHUT_RDWR)
            except:
                print("Server shutdown")

        if inc["command"] == 1: #Init baking
            blendPath = inc["args"]
            print("Path: " + blendPath)
            pipe = subprocess.Popen([blenderPath, "-b", blendPath, "--python-expr", 'import bpy; import thelightmapper; thelightmapper.addon.utility.build.prepare_build(0, True);'], shell=True, stdout=subprocess.PIPE)
            stdout = pipe.communicate()[0]

            if(stdout.decode().endswith("Saving output\r\n")):
                print("Finished")
                connection.sendall(("Baking finished").encode())

                try:
                    inc_socket.shutdown(socket.SHUT_RDWR)
                except:
                    print("Closed...")
            else:
                print("Error")
                print(stdout.decode())
        
    elif inc["call"] == 2: #Enquiry
        print("C")
        
    else:
        print("Unknown: " + inc)

def startServer(port):

    print("Starting server...")

    TCP_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    TCP_Socket.bind((HOST, port))

    TCP_Socket.listen(1)

    connection, address = TCP_Socket.accept()

    open_socket = True

    print("Server is now started - Waiting for incoming connection on: " + str(TCP_Socket.getsockname))

    while open_socket:

        data = connection.recv(1024)

        if not data:

            break

        evalIncoming(TCP_Socket, connection, json.loads(data.decode()))