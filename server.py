import socket

# create a simple server
# create a socket object
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# get local machine name
serversocket.bind((socket.gethostname(), 9999))

# queue up to 5 requests
serversocket.listen(5)

print(serversocket.getsockname())

print("Server is listening...")

while True:
    # establish a connection
    clientsocket, addr = serversocket.accept()

    #print(addr)
    
    print("Got a connection from %s" % str(addr))

    # print received message
    msg = clientsocket.recv(1024)
    print(msg.decode('ascii'))

    # send a message to the client
    msg = 'Thank you for connecting' + "\r\n"
    clientsocket.sendall(bytes(msg, encoding="utf-8"))
    clientsocket.close()
