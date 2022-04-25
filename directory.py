import os
import random
import shutil

if __name__ == "__main__":
    import shlex
    import socket
    import sys
    import threading
    from sys import executable
    from subprocess import Popen, CREATE_NEW_CONSOLE

    service_sockets = {}
    word_list = {"Waffle", "average"}
    server_dict = {}
    distport=50012
    distnum=1
    registered_ports=[]
    clientlist=[]




    def command_spawn(args: list) -> None:
        service_name = args[0]

        if service_name in service_sockets:
            print("Service already exists:", service_name)

        else:
            service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_port = int(args[1])

            try:
                service_socket.connect_ex(("127.0.0.1", target_port))

            except OSError:
                service_socket.close()
                print("Failed to start service:", service_name)

                return

            service_sockets[service_name] = service_socket


    def command_send(args: list) -> None:
        service_name = args[0]

        if service_name in service_sockets:
            service_socket = service_sockets[service_name]
            destinations = []
            messages = args[1:]

            if messages[1]=="auth":
                pass
            if ">" in messages:
                pipe_index = messages.index(">")
                destination_index = (pipe_index + 1)

                if destination_index < len(messages):
                    destinations = messages[destination_index:]

                messages = messages[0:pipe_index]

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

    def get_auth():
        server_name = ""
        for service in server_dict:
            if (server_dict[service][2]) == "authorization":
                    server_name = service
            else:
                server_name="Auth not found"
            return server_name


    def loadbalancer2():
        server_name=""
        num=3
        for service in server_dict:
            if(server_dict[service][2]) == "distribuition":
                servicenum = int(server_dict[service][3])
                if servicenum <num:
                    num=servicenum
                    server_name=service+" Nofull"
                else:
                    server_name=service+ " Full"

        return server_name

    def loadbalancer():
        server_name=""
        num=3
        for service in server_dict:
            if(server_dict[service][2]) == "distribuition":
                servicenum = int(server_dict[service][3])
                if servicenum <=num:
                    num=servicenum
                    server_name=service+" Nofull"
                else:
                    server_name=service+ " Full"
                    command = ["python", "distribution.py",str(distport+1),str(distnum+1)]
                    Popen(command, creationflags=CREATE_NEW_CONSOLE)
                    import time
                    time.sleep(0.5)

        return server_name




    def handle(peer_socket: socket.socket) -> None:
        received_data = peer_socket.recv(4096)

        while received_data:
            received_command = shlex.split(received_data.decode("utf-8").lower())

            if len(received_command) > 0:
                operation = received_command[1]

                if operation == "portcheck":
                    requested_port=int(received_command[2])
                    if requested_port in registered_ports:
                        message="True"
                    else:
                        message="false"
                    peer_socket.send(message.encode())


                elif operation == "loadservice":
                    server_stat = " "
                    name=received_command[2]
                    num=received_command[3]
                    for server in server_dict:
                        if server == name:
                            newnum=int(server_dict[name][3])
                            newnum=newnum+int(num)
                            if newnum<=3:
                                server_dict[name][3]=str(newnum)
                                print(name+" has "+server_dict[name][3] + " active services")
                                message= server_dict[name][3] + " active services"
                                peer_socket.send(message.encode())
                            else:
                                server_stat="Full"
                                break
                    if server_stat=="Full":
                        server_status = loadbalancer2()
                        service_name, status = server_status.split(" ")
                        sname, snum = service_name.split(".")
                        if status == "Full":
                            command = ["python", "distribution.py", str(distport + int(snum)), str(distnum + int(snum))]
                            Popen(command, creationflags=CREATE_NEW_CONSOLE)
                            import time
                            time.sleep(0.5)
                            name, num = service_name.split(".")
                            nextnum=int(num)+1
                            service_name = str(name)+"."+str(nextnum)

                        value = server_dict.get(service_name)
                        if value != None:
                            ip = value[0]
                            port = value[1]
                            type = value[2]
                            num = value[3]
                            message = "Server Full , USE " + type + " server ip:" + str(ip) + " port:" + str(port) + " Initial active services: " + num
                        else:
                            message = "Server Full , USE distribution server port:" + str(distport + int(snum)) + " Initial active services: " + "0"
                        peer_socket.send(message.encode())


                elif operation == "register":
                    name=received_command[2]
                    ip=received_command[3]
                    port=received_command[4]
                    registered_ports.append(int(port))
                    num=0
                    #todo add type
                    type = received_command[5]
                    server_dict[name] = [ip,port,type,str(num)]
                    message = "You are registered " + ip + ":" + str(port)
                    print("Successfully registered "+type+" server "+name+" with port:"+port)
                    peer_socket.send(message.encode())
                elif operation=="getclient":
                    clientcont=len(clientlist)+1
                    client="client"+str(clientcont)+ " register"
                    clientlist.append(clientcont)
                    peer_socket.send(client.encode())



                elif operation == "request":
                    auth=received_command[2]
                    if auth=="authorization":
                        service_name=get_auth()
                        if service_name=="Auth not found":
                            peer_socket.send("Auth server not connected".encode("utf-8"))
                        else:
                             value = server_dict.get(service_name)
                             if value != None:
                                 ip = value[0]
                                 port = value[1]
                                 type = value[2]

                             else:
                                 ip = ""
                                 port = 0
                                 type = "error"
                             message = type + " server ip:" + str(ip) + " port: " + str( port)
                             peer_socket.send(message.encode())

                    else:
                        service_status=loadbalancer()
                        service_name, status = service_status.split(" ")
                        value = server_dict.get(service_name)
                        if value != None:
                            ip=value[0]
                            port=value[1]
                            type= value[2]
                            num = value[3]

                        else:
                            ip = ""
                            port = 0
                            type = "error"
                            num = "None"
                        if status=="Full":
                            message = type + " server ip:" + str(ip) + " port:" + str(port) + " IS FULL with " + num + " active services, Choose another server"
                        else:
                            message = type + " server ip:" + str(ip) + " port:" + str(port) + " Initial active services: "+num
                        peer_socket.send(message.encode())


                else:
                    peer_socket.send(f"invalid dict operation: {operation}".encode("utf-8"))

            else:
                peer_socket.send(f"invalid dict command format".encode("utf-8"))

            received_data = peer_socket.recv(4096)


    def listen() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_port = 50005

            # Avoid "bind() exception: OSError: [Errno 48] Address already in use" error
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("127.0.0.1", server_port))
            server_socket.listen()

            while True:
                peer_socket, address = server_socket.accept()

                threading.Thread(target=handle, args=[peer_socket]).start()


    threading.Thread(target=listen).start()

    command_actions = {
        "spawn": command_spawn,
        "send": command_send,
    }





    Popen([executable, 'auth.py'], creationflags=CREATE_NEW_CONSOLE)
    import time

    time.sleep(0.5)
    Popen([executable, 'distribution.py'], creationflags=CREATE_NEW_CONSOLE)

    #Popen([executable, 'client.py'], creationflags=CREATE_NEW_CONSOLE)
    #command = ["python", "distribution.py"]
    #Popen(command, creationflags=CREATE_NEW_CONSOLE)

    cont=1
    dir="client"+str(cont)
    while cont<10:
        if os.path.exists(dir):
            shutil.rmtree(dir)
        cont=cont+1
        dir = "client" + str(cont)




    while True:
        command = input().lower()
        command_components = shlex.split(command)
        command_name = command_components[0]

        if command_name in command_actions:
            command_actions[command_name](command_components[1:])

        else:
            print("No such command:", command_name)
