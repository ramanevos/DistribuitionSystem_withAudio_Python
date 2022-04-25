import os

if __name__ == "__main__":
    import shlex
    import socket
    import sys
    import threading
    import random
    import wave
    import struct
    from array import array
    from os import stat
    import pyaudio, pickle
    from os import listdir
    from os.path import isfile, join

    service_sockets = {}
    service_registered =[]
    auth_keys = []
    listofaudio=""
    if len(sys.argv) > 1:
        port = sys.argv[1]
        server_num = sys.argv[2]
    else:
        port = 50012
        server_num = 1

    def command_spawn(args: list) -> None:
        """
        "Spawn" command used by the user interface to create a new service worker instance for communicating with remote
        peers.
        :param args: New service worker name followed by the port number to listen on for remote data.
        :return:
        """

        service_name = args[0]

        if service_name in service_sockets:
            print("Service already exists:", service_name)

        else:
            service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_port = int(args[1])

            try:
                service_socket.connect_ex(("127.0.0.1", target_port))
                print("service:", service_name + " created on port:", target_port)

            except OSError:
                service_socket.close()
                print("Failed to start service:", service_name)

                return

            service_sockets[service_name] = service_socket

    def check_key(service_name,operation):
        service_name = service_name
        if service_name in service_sockets:
            service_socket = service_sockets[service_name]
            message = service_name + " " + operation
            found_key = False
            for service in service_registered:
                if service["service"] == service_name:
                    message=message+ " "+ service["key"]
                    found_key = True
            if not found_key:
                message=message+ " NoKey"

            service_socket.send(message.encode("utf-8"))

            received_data = service_socket.recv(4096)

            return received_data.decode("utf-8")


    def get_port(command):
        command_components = shlex.split(command)
        service_name = command_components[1]

        if service_name in service_sockets:
            service_socket = service_sockets[service_name]
            messages = command_components[1:]

            service_socket.send(" ".join(messages).encode("utf-8"))

            received_data = service_socket.recv(4096)

            if received_data:
                list = received_data.decode("utf-8").split(" ")
                if list[0] == "authorization":
                    authport = list[-1]
                    return authport




    def getkey(service_name,operation):
        service_name = service_name


        if service_name in service_sockets:
            service_socket = service_sockets[service_name]

            messages = service_name + " " + operation


            service_socket.send(messages.encode("utf-8"))

            received_data = service_socket.recv(4096)

            return received_data.decode("utf-8")


    def command_send(args: list) -> None:
        """
        "Send" command used by the user interface to transmit data from a service worker to a remote peer.
        :param args: Command arguments. The first ">" found, if any, is interpreted as a forwarding operator and any
                     remote data received will be forwarded to that service as a new send command.
        """

        service_name = args[0]

        if service_name in service_sockets:
            service_socket = service_sockets[service_name]
            messages = args[0:]

            service_socket.send(" ".join(messages).encode("utf-8"))

            received_data = service_socket.recv(4096)

            if received_data:

                print(received_data.decode("utf-8"))

        else:
            print("Service does not exist:", service_name)

    def send_spawn(peer_socket,command_list):
        """
        "Send" command used by the user interface to transmit data from a service worker to a remote peer.
        :param args: Command arguments. The first ">" found, if any, is interpreted as a forwarding operator and any
                     remote data received will be forwarded to that service as a new send command.
        """

        service_name = command_list[1]

        if service_name in service_sockets:
            service_socket = service_sockets[service_name]
            messages = command_list[1:]

            service_socket.send(" ".join(messages).encode("utf-8"))

            received_data = service_socket.recv(4096)

            if received_data:
                message=received_data.decode()
                printmessage = message.split()
                if printmessage[:2]!=['Server','Full']:
                    print(received_data.decode("utf-8"))
                    peer_socket.send(message.encode())
                else:
                    peer_socket.send(message.encode())

        else:
            print("Service does not exist:", service_name)


    def handle(peer_socket: socket.socket) -> None:
        """
        Handles an individual connection request that has already been received and needs monitoring for new data.
        :param peer_socket: Individual peer connection.
        """

        received_data=peer_socket.recv(4096)

        while received_data:
            received_command=shlex.split(received_data.decode("utf-8").lower())

            if len(received_command) > 0:
                operation=received_command[1]

                if operation == "services":
                    number=received_command[2]
                    command = ["send", "distribuition", "loadservice", "musicserver."+str(server_num),  number]
                    send_spawn(peer_socket,command)


                elif operation == "auth":
                    for service in service_sockets:
                        if service == "distribuition":
                            command = "send distribuition request authorization"
                            authport = get_port(command)

                    service_name = received_command[0]
                    authservice_name="auth"+service_name
                    if authservice_name not in service_sockets:
                        command = "spawn "+authservice_name+ " "+ str(authport)
                        command_components = shlex.split(command)
                        command_name = command_components[0]
                        command_actions[command_name](command_components[1:])



                    command = "send "+authservice_name+" auth"
                    command_components = shlex.split(command)
                    command_auth = command_components[2]
                    sendkey=getkey(authservice_name,command_auth)
                    if sendkey != "Already logged in":
                            service_registered.append({"service":authservice_name, "key":sendkey})
                    peer_socket.send(sendkey.encode("utf-8"))

                elif operation == "request":
                    for service in service_sockets:
                        if service == "distribuition":
                            command = "send distribuition request authorization"
                            authport = get_port(command)
                    authservice_name="auth"+received_command[0]
                    if authservice_name not in service_sockets:
                        command = "spawn "+authservice_name+" "+str(authport)
                        command_components = shlex.split(command)
                        command_name = command_components[0]
                        command_actions[command_name](command_components[1:])

                    command = "send " + authservice_name + " check"
                    command_components = shlex.split(command)
                    command_check = command_components[2]
                    keycheck=check_key(authservice_name,command_check)
                    if keycheck=="Not logged In":
                        peer_socket.send(("You are not logged in").encode("utf-8"))
                    else:
                        if keycheck=="Logged In":

                            peer_socket.send(("The list of audio is:" +listofaudio).encode("utf-8"))

                elif operation=="audio":
                    for service in service_sockets:
                        if service == "distribuition":
                            command = "send distribuition request authorization"
                            authport = get_port(command)

                    authservice_name = "auth" + received_command[0]
                    if authservice_name not in service_sockets:
                        command = "spawn " + authservice_name + " 50010"
                        command_components = shlex.split(command)
                        command_name = command_components[0]
                        command_actions[command_name](command_components[1:])

                    command = "send " + authservice_name + " check"
                    command_components = shlex.split(command)
                    command_check = command_components[2]
                    keycheck = check_key(authservice_name, command_check)
                    if keycheck == "Not logged In":
                        peer_socket.send(("You are not logged in").encode("utf-8"))
                    else:
                        if keycheck == "Logged In":
                            file = received_command[2]
                            checkfile = received_command[2]+".wav"
                            if checkfile not in onlyfiles:
                                peer_socket.send(("Wrong audio, Req list").encode("utf-8"))
                            else:
                                peer_socket.send(("OK. You are logged in").encode("utf-8"))
                                with open('Audio/'+checkfile, 'rb') as f:
                                    path = "Audio/"+checkfile
                                    filesize = str(os.path.getsize("Audio/"+checkfile))
                                    message = filesize + " " + checkfile
                                    #print(message)
                                    peer_socket.send(message.encode())
                                    import time
                                    time.sleep(0.5)

                                    try:
                                        f = open(path, 'rb')
                                    except:
                                        print("File does not exist")
                                    print('Sending File: ' + path)
                                    l = f.read(4096)
                                    total = len(l)
                                    while (l):
                                        if (str(total) != filesize):
                                            #print('Sending...')
                                            peer_socket.send(l)
                                            l = f.read(4096)
                                            total = total + len(l)
                                        else:
                                            break

                                    f.close()

                else:
                    print("NOPEE")
                    peer_socket.send(f"invalid distribution operation: {operation}".encode("utf-8"))

            else:
                peer_socket.send(f"invalid distribution command format".encode("utf-8"))

            received_data=peer_socket.recv(4096)


    def listen() -> None:
        """
        Handles the incoming connection requests from peer services, delegating them to a handler thread.
        """

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_port = port

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("127.0.0.1", int(server_port)))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()

                threading.Thread(target=handle, args=[peer_socket]).start()


    threading.Thread(target=listen).start()

    # 1 send command to directory that exist

    command_actions = {
        "spawn": command_spawn,
        "send": command_send,
    }

   # print("Enter a command...")

    onlyfiles = [f for f in listdir("Audio") if isfile(join("Audio", f))]
    for file in onlyfiles:
        name,extension = file.split(".")
        listofaudio=listofaudio+ " " + name
    authport=0
    reg=0
    while True:
        if reg==0:
            command = "spawn distribuition 50005"
            reg=reg+1
        elif reg==1:
            command = "send distribuition register musicserver."+str(server_num)+" 127.0.0.1 " + str(port) + " distribuition"
            reg = reg + 1
        elif reg==2:
            command = "send distribuition request authorization"
            reg = reg + 1
        else:
            command = input(" ")
        command_components = shlex.split(command)
        command_name = command_components[0]

        if command_name in command_actions:
            command_actions[command_name](command_components[1:])

        else:
            print("No such command:", command_name)
