import socket
import threading

from config import args
from typing import List
import re

class Client():
    def __init__(self, host='localhost', port=50005) -> None:
        # the socket to listen to server messages
        self.server_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # the socket to send messages to the server
        self.server_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # The upload address (listen forever for upload requests)
        self.upload_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.upload_sock.bind(('localhost', 0))
        self.upload_sock.listen(15)

        # server info
        self.host = host
        self.port = port

        # the thread to listen to server messages
        self.server_listen_thread = threading.Thread(target=self.listen_server, daemon=True)
        # the thread to listen to download requests from other peers
        self.upload_thread = threading.Thread(target=self.listen_upload, daemon=True)
        # the thread to send messages to the server
        self.server_send_thread = threading.Thread(target=self.cmd_forever, daemon=True)

        self.setup()

    def start(self):
        """
            @ Description: This function starts all the threads parallelly and wait for joining
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.server_send_thread.start()
        self.server_listen_thread.start()
        self.upload_thread.start()

        self.server_send_thread.join()
        self.server_listen_thread.join()
        self.upload_thread.join()

    def setup(self):
        """
            @ Description: This function sets up the connection between this client and server
            @ Input: None
            @ Return: None
            @ Output: 
                1) Sucessfully connect to both the listening side of the server as well as the receiving side of the server
                2) Transfer the information about the connection the server (both the first connect address and the upload address)
        """
        # first connect to server
        self.server_send_sock.connect((self.host, self.port))
        self.server_send_sock.send('NONE'.encode())

        # second connect to server
        self.server_listen_sock.connect((self.host, self.port))

        # tell the server which original connection this connection belongs to
        # tell the server the downloading address that other clients can reach out to
        send_data = self.server_send_sock.getsockname()[0] + ' ' + str(self.server_send_sock.getsockname()[1]) + \
                            ' ' + self.upload_sock.getsockname()[0] + ' ' + str(self.upload_sock.getsockname()[1])
        self.server_listen_sock.send(send_data.encode())
        print('Sending address: ' + self.server_send_sock.getsockname()[0] + ' ' + str(self.server_send_sock.getsockname()[1]))
        print('Listening address: ' + self.server_listen_sock.getsockname()[0] + ' ' + str(self.server_listen_sock.getsockname()[1]))
        print('Upload address: ' + self.upload_sock.getsockname()[0] + ' ' + str(self.upload_sock.getsockname()[1]))
    
    def listen_server(self):
        """
            @ Description: This function listens forever for the messages from server and responds them
            @ Input: None
            @ Return: None
            @ Output: Responds all the incoming messages
        """
        while True:
            data = self.server_listen_sock.recv(1024).decode()
            print('Received:', data)
            if data == '':
                continue
            elif data == 'ping':
                send_data = self.respond_ping()
            elif data == 'discover':
                send_data = self.respond_discover()
            else:
                raise RuntimeError('[Error] WTF was that command: ' + data)
            
            # self.server_listen_sock.send(send_data.encode())

    def listen_upload(self):
        """
            @ Description: This function listens forever for the download requests from other peer (multithreaded)
            @ Input: None
            @ Return: None
            @ Output: Create many threads to handle the upload parallelly
            @ Additional notes: the request message comes in the form:
                <file name 1> <file name 2> ... <file name n>
                seperated by a space
        """
        # TODO: forever listen for incoming upload requests, there can be multiple upload requests from a client as the same time
        while True:
            download_socket, download_address = self.upload_sock.accept()
            # <file name 1> <file name 2> ... <file name n>
            request_files = download_socket.recv(1024).decode()
            # TODO: create threads and handle download requests

    def cmd_forever(self):
        """
            @ Description: This function listens forever for the user input
            @ Input: None
            @ Return: None
            @ Output: Execute the all the valid incoming inputs
        """
        while True:
            input_str = input('>> ')
            pattern = r'^\s*\b(?:publish|fetch)\b'
            matched = re.search(pattern, input_str)

            if not matched:
                print('Invalid command (please use <publish> or <fetch>)!')
                continue

            # remove spaces at the beginning or end
            input_str = re.sub(r'^\s+|\s+$', '', input_str)
            # remove redundant spaces
            input_str = re.sub(r'\s\s+', ' ', input_str)

            splited_command = input_str.split()
            if len(splited_command) <= 1:
                print('Please enter the arguments for the command!')
                continue

            command = splited_command[0]
            arguments = splited_command[1:]

            if command == 'publish':
                if len(arguments) != 2:
                    print('Invalid number of arguments for <publish>, required is 2!')
                    continue

                self.publish(arguments)
            elif command == 'fetch':
                self.fetch(arguments)

                

    def publish(self, arguments):
        """
            @ Description: This function execute the 'publish' command
            @ Input: arguments - the list of 2 elements, the first is <lname>, second is <fname> (check the Assignment)  
            @ Return: None
            @ Output: Execute the 'publish' command and receive respond from the server
        """
        # TODO: below are just mock codes for it to work, please modify them
        self.server_send_sock.send('publish'.encode())
        response = self.server_send_sock.recv(1024).decode()
        print(response)

    def fetch(self, arguments):
        """
            @ Description: This function execute the 'fetch' command (multithreaded)
            @ Input: arguments - the list of file names to download, comes in the form
                <file name 1> <file name 2> ... <file name n>
            @ Return: None
            @ Output: Execute the 'fetch' command and download the files sucessfully
            @ Additional notes: 
                1) If the number of files > 1, open threads to handle download parralelly
                2) After sending fetch requests to the server, the server will response in the form
                <upload peer 1 IP> <upload peer 1 port> <upload peer 2 IP> <upload peer 2 port> ...
                with  <upload peer i IP> <upload peer i port> correspond to the file i
        """
        # TODO: below are just mock codes for it to work, please modify them
        self.server_send_sock.send('fetch'.encode())
        response = self.server_send_sock.recv(1024).decode()


    def respond_ping(self) -> str:
        """
            @ Description: This function responds to the 'ping' message from server
            @ Input: None
            @ Return: The reponse with string datatype
            @ Output: None
        """
        # TODO: respond to server <ping> message here
        self.server_listen_sock.sendall('pong'.encode())

    def respond_discover(self) -> str:
        """
            @ Description: This function responds to the 'discover' message from server
            @ Input: None
            @ Return: The reponse with string datatype
            @ Output: None
        """
        # TODO: respond to server <discover> message here
        # retrieve all files in client/repo
        
        pass

    def close(self):
        """
            @ Description: This function close all sockets
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.server_listen_sock.close()
        self.server_send_sock.close()
        self.upload_sock.close()

class File():
    def __init__(self, file_name, size_in_bytes, owner_address) -> None:
        self.file_name = file_name
        self.size_in_bytes = size_in_bytes
        self.owner_address = owner_address

def main():
    client = Client()
    try:
        client.start()
    except Exception as e:
        client.close()
        print(f'[Exception] Caught exception in the process: {e}')
    except KeyboardInterrupt as k:
        client.close()

if __name__ == '__main__':
    main()