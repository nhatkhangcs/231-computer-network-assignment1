
from threading import Thread
from icmplib import ping
from _thread import *
import socket

import tqdm


class bigServer:
    def __init__(self):
        self.clients = {}
        self.myServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def initServer(self):
           # establish a connection
        while True:
            clientsocket, addr = self.myServer.accept()
            print("Got a connection from %s" % str(addr))
            self.clients[addr] = clientsocket

    def receive_file(self):
        client, addr = self.clients[addr].accept()
        print(f"Connection from {addr} has been established")
        filename = client.recv(1024).decode()
        filesize = client.recv(1024).decode()
        filesize = int(filesize)

        bytes_read = b""
        file = open(filename, "wb")

        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            while True:
                bytes_read = client.recv(1024)
                if not bytes_read:
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))

        file.write(bytes_read)

        file.close()

    def ping_client_by_hostname(self, client_hostname):
        try:
            ping(client_hostname, count=1)
            return True
        except:
            return False
        
    def command(self):
        while True:
            cmd = input('>>> ')
            if cmd.startswith('ping'):
                client_hostname = cmd.split(' ')[1]
                if client_hostname.lower() == 'exit':
                    break
                result = self.ping_client_by_hostname(client_hostname)
                if result:
                    print(f"{client_hostname} is up")
                else:
                    print(f"{client_hostname} is down")
        
            elif cmd.startswith('fetch'):
                pass

        

if __name__ == "__main__":
    myServer = bigServer()
    
    myServer.myServer.bind((socket.gethostname(), 1233))
    myServer.myServer.listen(5)
    print("Server is listening")

    # while True:
    #     establish a connection
    #     clientsocket, addr = myServer.myServer.accept()
    #     print("Got a connection from %s" % str(addr))
    #     myServer.clients[socket.gethostname()] = clientsocket
    
    # create a socket object
    thread1 = Thread(target=myServer.initServer)
    thread2 = Thread(target=myServer.command)
    thread3 = Thread(target=myServer.receive_file)

    threads = [thread1, thread2, thread3]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
        




