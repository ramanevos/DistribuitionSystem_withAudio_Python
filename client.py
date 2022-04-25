import os

if __name__ == "__main__":
    import shlex
    import socket
    import sys
    import threading
    import pyaudio
    import struct
    import pickle
    from playsound import playsound
    from pathlib import Path
    from pydub import AudioSegment
    from pydub.playback import play

    service_sockets = {}
    service_sockets2=[]
    auth_key="not existent"
    audio_folder=[]

    def tryPort(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = False
        try:
            sock.bind(("127.0.0.1", port))
            result = True
        except:
            pass
        sock.close()
        return result


    #x = random.randint(100, 110)
    #own_port = 50000 + x

    ownport=50101
    result=tryPort(ownport)
    while result==False:
        ownport=ownport+1
        result = tryPort(ownport)


    def port_validate(message):
        send_message = message.split(" ")
        service_name = "directoryrequest"

        if service_name in service_sockets:
            service_socket = service_sockets[service_name]
            messages = send_message[1:]

            service_socket.send(" ".join(messages).encode("utf-8"))

            received_data = service_socket.recv(4096)

            return received_data.decode()


        else:
            print("Service does not exist:", service_name)

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
                if target_port != 50005:
                    check_ifport = "send directoryrequest portcheck " + str(target_port)
                    result = port_validate(check_ifport)
                    if result == "True":
                        count = 1
                        service_socket.connect_ex(("127.0.0.1", target_port))
                        service_socket.send(("Numof services " + str(count)).encode("utf-8"))
                        response=service_socket.recv(4096).decode()
                        check_server=response.split(" ")
                        if check_server[:2] != ['Server','Full']:
                            print("service:", service_name+ " created on port:", target_port)
                            service_sockets[service_name] = service_socket
                        else:
                            print("The server on port: " + str(target_port) + " is full")
                            print(response)
                    else:
                        print(str(target_port) + " is not a valid connected distribution port, try again")
                else:
                    service_socket.connect_ex(("127.0.0.1", target_port))
                    print("service:", service_name + " created on port:", target_port)
                    service_sockets[service_name] = service_socket


            except OSError:
                service_socket.close()
                print("Failed to start service:", service_name)
                return









    def register_key(data, service_name):
        data = shlex.split(data.decode("utf-8").lower())
        if data[0] == "key":
            auth_key = data[1]
            service_sockets2.append({"service": service_name, "key": auth_key, })
            print("the key is:", auth_key)


    def get_audio(service_socket):
     pass

    def play_song(args: list) -> None:
        """
        "Send" command used by the user interface to transmit data from a service worker to a remote peer.
        :param args: Command arguments. The first ">" found, if any, is interpreted as a forwarding operator and any
                     remote data received will be forwarded to that service as a new send command.
        """

        service_name = args[0]

        if service_name in service_sockets:
            file=audio_folder[0]+"/"+args[1]+".wav"
            my_file = Path(file)
            if my_file.is_file():
                song = AudioSegment.from_wav(file)
                print('playing sound using  pydub')
                play(song)
            else:
                print("The client has not "+args[1]+".wav")
        else:
            print("service "+service_name + " not existent")


    def get_clientnum(data):
        data = shlex.split(data.decode("utf-8").lower())
        if len(data)>1:
            if data[1] == "register":
                print("YOU ARE: ", data[0])
                os.mkdir(data[0])
                audio_folder.append(data[0])
                return "true"
            else:
                return "false"
        else:
            return "false"



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

                register_key(received_data,service_name)
                value=get_clientnum(received_data)
                if value=="true":
                    pass
                else:
                    print(received_data.decode("utf-8"))

        else:
             print("Service does not exist:", service_name)


    def handle(peer_socket: socket.socket) -> None:
        """
        Handles an individual connection request that has already been received and needs monitoring for new data.
        :param peer_socket: Individual peer connection.
        """

        received_data = peer_socket.recv(4096)

        while received_data:
            commands = received_data.decode()
            commands = commands.split(" ")
            if commands[1] == "clientmusicrequest":
                song_name=commands[2]
                dir=audio_folder[0]
                if os.path.exists(dir+"/"+song_name+".wav"):
                        message="the song is found at "+ str(ownport)
                        peer_socket.send(message.encode())
                        with open(dir+'/' + song_name+".wav", 'rb') as f:
                            path = dir+'/' + song_name+".wav"
                            filesize = str(os.path.getsize(path))
                            message = filesize + " " + song_name+".wav"
                            # print(message)
                            peer_socket.send(message.encode())

                            msg=peer_socket.recv(100)


                            try:
                                f = open(path, 'rb')
                            except:
                                print("File does not exist")
                            print('Sending File: ' + path)
                            l = f.read(4096)
                            total = len(l)
                            while (l):
                                if (str(total) != filesize):
                                    # print('Sending...')
                                    peer_socket.send(l)
                                    l = f.read(4096)
                                    total = total + len(l)
                                else:
                                    break

                            f.close()
                        break

                else:
                    message = "Song is NOT found at " + str(ownport)
                    peer_socket.send(message.encode())
                    break

                # file exists

                #response = "message received from " + str(ownport)
               # peer_socket.send(response.encode())

                #received_data = peer_socket.recv(4096)
            else:
                peer_socket.send(received_data)

                received_data = peer_socket.recv(4096)


    def listen() -> None:
        """
        Handles the incoming connection requests from peer services, delegating them to a handler thread.
        """

        server_port = ownport
        print("Client port is: " + str(server_port))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:



            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("127.0.0.1", server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()

                threading.Thread(target=handle, args=[peer_socket]).start()


    def songclient(socket, sender):
        message = socket.recv(4096)
        msg="Header received"
        socket.send(msg.encode())
        message = message.decode()
        import time
        time.sleep(1)

        filesize, filename = message.split(" ")
        # print(filesize.decode())
        with open(audio_folder[0] + "/" + filename, 'wb') as f:

            # print("Receiving File...")
            l = socket.recv(4096)
            total = len(l)
            while (l):
                # print("Receiving...")

                # print('trying to receive')
                f.write(l)
                total = total + len(l)
                if (int(total) < int(filesize)):
                    l = socket.recv(4096)

                else:
                    break
            f.close()
            print("song received from: " + str(sender))


    def song(socket,sender):
        message=socket.recv(4096)
        message=message.decode()


        filesize, filename = message.split(" ")
        #print(filesize.decode())
        with open(audio_folder[0]+"/"+filename, 'wb') as f:

            #print("Receiving File...")
            l = socket.recv(4096)
            total = len(l)
            while (l):
                #print("Receiving...")

                # print('trying to receive')
                f.write(l)
                total = total + len(l)
                if (int(total) <= int(filesize)):
                    l = socket.recv(4096)

                else:
                    break
            f.close()
            print("song received from: "+ str(sender))


    def getclientmusic(socket,song_name):
        command = "send clientmusicrequest " + str(song_name)
        socket.send(command.encode())
        try:
            response = socket.recv(26)
            response=response.decode()
            if "the song is found at" in response:
                res=response.split(" ")
                sender_port=res[-1]
                print(response)
                songclient(socket,sender_port)


                return "clientfound"
            else:
                print(response)
                return "askclient"

        except:
            print("No response received")


    def spawn_client(port,song_name):
        if port==ownport:
            return "askclient"
        else:
            service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
           # service_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            target_port = int(port)

            try:
                service_socket.connect_ex(("127.0.0.1", target_port))
                print("service created on port:", str(target_port))
                # service_sockets[service_name] = service_socket
                #service_socket.bind(("127.0.0.1", target_port))
                #service_socket.listen()
                response= getclientmusic(service_socket,song_name)
                return response


            except OSError:
                service_socket.close()
                print("The clients don't have this music file...requesting to the server:", target_port)
                return "askserver"

    def get_song(args: list) -> None:
        service_name = args[0]
        song_name= args[1]

        if service_name in service_sockets:
            port = 50101
            result = spawn_client(port,song_name)
            while result == "askclient":
                port = port + 1
                result = spawn_client(port,song_name)

            if result=="askserver":

                service_socket = service_sockets[service_name]
                messages = args[0] + " audio " + args[1]


                service_socket.send(messages.encode("utf-8"))

                received_data=service_socket.recv(21)
                if received_data.decode("utf-8")!="OK. You are logged in":
                    print(received_data.decode("utf-8"))
                else:
                    server="server"
                    song(service_socket,server)
            elif result=="clientfound":
                 print("Client received audio from another client")
            else:
                 print("Service does not exist:", service_name)
        #TODO play song - see streaming example, load from memory last music file, play it


    threading.Thread(target=listen).start()

    command_actions = {
        "spawn": command_spawn,
        "send": command_send,
        "get": get_song,
        "play": play_song,
    }


    reg=0
    while True:
        if reg==0:
            command="spawn directoryrequest 50005"#
            reg=1
        elif reg==1:
            command="send directoryrequest request server"
            reg=2#
        elif reg==2:
            command="send directoryrequest getclient"
            reg=3#
        else:
            print("Enter a command...")  #
            command = input().lower()
        command_components = shlex.split(command)
        command_name = command_components[0]

        if command_name in command_actions:
            command_actions[command_name](command_components[1:])

        else:
            print("No such command:", command_name)
