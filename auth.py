if __name__ == "__main__":
    import shlex
    import socket
    import threading
    import random


    service_sockets = {}
    auth_keys = []
    registered_services=[]

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


    def command_send(args: list) -> None:
        """
        "Send" command used by the user interface to transmit data from a service worker to a remote peer.
        :param args: Command arguments. The first ">" found, if any, is interpreted as a forwarding operator and any
                     remote data received will be forwarded to that service as a new send command.
        """

        service_name = args[0]

        if service_name in service_sockets:
            service_socket = service_sockets[service_name]
            destinations = []
            messages = args[0:]


            service_socket.send(" ".join(messages).encode("utf-8"))

            received_data = service_socket.recv(4096)

            if received_data:
                if destinations:
                    for destination in destinations:
                        command_send([destination, received_data.decode("utf-8")])

                else:
                    print(received_data.decode("utf-8"))

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
                service_name=received_command[0]
                operation=received_command[1]
                if operation=="auth":
                    if service_name in registered_services:
                        sendkey="Already logged in"
                        peer_socket.send(sendkey.encode("utf-8"))
                    else:
                        key = random.getrandbits(128)
                        key=str(key)
                        auth_keys.append(key)
                        registered_services.append(service_name)
                        sendkey=key
                        print(service_name +" hash value: ",key)
                        peer_socket.send(sendkey.encode("utf-8"))


                    #TODO authenticate user, send back "key"

                elif operation=="check":
                    check_key=received_command[2]
                    if check_key in auth_keys:
                        print("\n"+service_name + " is logged in with key "+ check_key)
                        peer_socket.send(f"Logged In".encode("utf-8"))
                    else:
                        print("\n"+service_name + " is not logged")
                        peer_socket.send(f"Not logged In".encode("utf-8"))


                else:
                    peer_socket.send(f"invalid distribution operation: {operation}".encode("utf-8"))

            else:
                peer_socket.send(f"invalid distribution command format".encode("utf-8"))

            received_data=peer_socket.recv(4096)


    def listen() -> None:
        """
        Handles the incoming connection requests from peer services, delegating them to a handler thread.
        """

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_port = 50010

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("127.0.0.1", server_port))
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

    reg = 0
    while True:
        if reg == 0:
            command = "spawn authorization 50005"
            reg = reg + 1
        elif reg == 1:
            command = "send authorization register authserver 127.0.0.1 50010 authorization"
            reg = reg + 1
        else:
            command = input(" ")
        command_components = shlex.split(command)
        command_name = command_components[0]

        if command_name in command_actions:
            command_actions[command_name](command_components[1:])

        else:
            print("No such command:", command_name)