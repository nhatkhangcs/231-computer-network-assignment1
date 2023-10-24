# import socket

# # create a simple server
# # create a socket object
# serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# # get local machine name
# serversocket.bind((socket.gethostname(), 9999))

# # queue up to 5 requests
# serversocket.listen(5)

# print(serversocket.getsockname())

# print("Server is listening...")

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


# while True:
#     # establish a connection
#     clientsocket, addr = serversocket.accept()
    
#     #print(addr)
    
#     print("Got a connection from %s" % str(addr))

#     # print received message
#     msg = clientsocket.recv(1024)
#     print(msg.decode('ascii'))

#     # send a message to the client
#     msg = 'Thank you for connecting' + "\r\n"
#     clientsocket.sendall(bytes(msg, encoding="utf-8"))
#     clientsocket.close()

# Python 3 server example
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from threading import Thread
from icmplib import ping
import socket

# FTP server setup
authorizer = DummyAuthorizer()
handler = FTPHandler
handler.authorizer = authorizer
authorizer.add_user("1", "2", homedir='.', perm="elradfmw")

server = FTPServer(("0.0.0.0", 21), handler)  # Listen on all network interfaces

def ping_client_by_hostname(client_hostname):
    try:
        client_ip = socket.gethostbyname(client_hostname)
        response = ping(client_ip, count=1)
        return response.is_alive
    except socket.gaierror:
        return False  # Hostname cannot be resolved
    except Exception as e:
        return str(e)

def ping_thread():
    while True:
        client_hostname = input("Enter client hostname to ping (or 'exit' to stop pinging): ")
        if client_hostname.lower() == 'exit':
            break
        result = ping_client_by_hostname(client_hostname)
        if result:
            print(f"{client_hostname} is up")
        else:
            print(f"{client_hostname} is down")

def receiveQuery(cmd: str):
    if cmd.startswith('fetch'):
        file_name = cmd.split(' ')[1]
        # ping all clients and record responding time of each client
        # choose the client with the lowest responding time
        # download file from that client
        # if no client is responding, print error message
        clients = [client for client in authorizer.user_table.keys() if client != '1']
        response_times = {}
        for client in clients:
            if ping_client_by_hostname(client):
                ping_result = ping(target=client, count=1)
                response_times[client] = ping_client_by_hostname(client)
        print(response_times)
        # find client with lowest responding time
        min_response_time = float('inf')
        min_response_client = None

        for client, response_time in response_times.items():
            if response_time < min_response_time:
                min_response_time = response_time
                min_response_client = client

        if min_response_client is None:
            print("No client is responding")
            return
        
        # redirect to client with lowest responding time
        print(f"Redirecting to {min_response_client}")

        # create a socket object
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        

if __name__ == "__main__":
    clients = {}
    ping_thread2 = Thread(target=ping_thread)
    ping_thread1 = Thread(target=server.serve_forever)
    ping_thread3 = Thread(target=receiveQuery)
    Threads = [ping_thread1, ping_thread2, ping_thread3]

    for thread in Threads:
        thread.start()
    
    for thread in Threads:
        thread.join()

