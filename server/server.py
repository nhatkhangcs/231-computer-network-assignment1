import socket
import threading

from config import args
from typing import List, Dict
import re

class Server:     
    def __init__(self, host='localhost', port=50005) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(args.MAX_CLIENTS)

        self.listening_thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.cmd_thread = threading.Thread(target=self.cmd_forever, daemon=True)
        self.handling_threads: List[threading.Thread] = [None] * args.MAX_CLIENTS

        self.num_current_clients = 0
        # key: The address that client send requests ((IP, port))
        # value: ClientInfo object
        self.client_infos  = {}
        self.clients_buffer = {}

    def start(self):
        """
            @ Description: This function starts all the threads parallelly and wait for joining
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.listening_thread.start()
        self.cmd_thread.start()

        self.cmd_thread.join()
        self.listening_thread.join()

    def serve_forever(self):
        """
            @ Description: This function listens for all incoming connection request from clients and start serving clients
                after having enough information
            @ Input: None
            @ Return: None
            @ Output: After having enought information, start a thread to listen to that client immediately
        """
        while True:
            client_socket, client_address = self.sock.accept()

            data = ''
            while True:
                data = client_socket.recv(1024).decode()
                if data != '':
                    break

            if data != 'NONE':
                data = data.split()
                original_IP = data[0]
                original_port = int(data[1])

                upload_IP = data[2]
                upload_port = int(data[3])

                if (original_IP, original_port) not in self.client_infos:
                    self.clients_buffer[(original_IP, original_port)] = ClientInfo(
                        identifying_address=(original_IP, original_port),
                        sending_address=client_address,
                        sending_sock=client_socket,
                        upload_address=(upload_IP, upload_port),
                    )
                else:
                    client_info: ClientInfo = self.client_infos[(original_IP, original_port)]
                    client_info.sending_address=client_address
                    client_info.sending_sock=client_socket
                    client_info.upload_address=(upload_IP, upload_port)
                    client_info.listening_thread=threading.Thread(target=self.serve_client, args=[client_info.identifying_sock, client_info.identifying_address], daemon=True)

                    client_info.listening_thread.start()
            else:
                if client_address not in self.clients_buffer:
                    self.client_infos[client_address] = ClientInfo(
                        identifying_address=client_address,
                        identifying_sock=client_socket,
                        listening_thread=threading.Thread(target=self.serve_client, args=[client_socket, client_address], daemon=True)
                    )
                else:
                    client_info = self.clients_buffer[client_address]
                    client_info.identifying_sock=client_socket
                    client_info.listening_thread=threading.Thread(target=self.serve_client, args=[client_info.identifying_sock, client_info.identifying_address], daemon=True)
                    self.client_infos[client_address] = client_info
                    self.clients_buffer.pop(client_address)
                    client_info.listening_thread.start()



    def serve_client(self, client_socket: socket.socket, client_address):
        """
            @ Description: This function listen for clients requests and respond to them
            @ Input: None
            @ Return: None
            @ Output: None
        """
        # TODO: below are just mock codes for it to work, please modify them
        while True:
            data = client_socket.recv(1024).decode()
            if data == '':
                continue
            if data == 'fetch':
                response = self.respond_fetch(client_address, [])
            elif data == 'publish':
                response = self.respond_publish(client_address, [])

            client_socket.send(response.encode())


    def respond_fetch(self, client_address, arguments):
        """
            @ Description: This function returns the list of peers' address that the client can connect to download 
            @ Input: None
            @ Return: the list of peers for downloading, in the form
                <upload peer 1 IP> <upload peer 1 port> <upload peer 2 IP> <upload peer 2 port> ...
                with  <upload peer i IP> <upload peer i port> correspond to the file i. IF a file doesn't exist, put 'null'
                in <upload peer i IP> and <upload peer i port>
            @ Output: None
        """
        # TODO: below are just mock codes for it to work, please modify them
        found = False
        found_address = None
        for address in self.client_infos.keys():
            if address != client_address:
                found = True
                found_address = address
                break
        
        if not found:
            return 'Server found no one to connect to you'
        else:
            upload_address = self.client_infos[found_address].upload_address
            return upload_address[0] + ' ' + str(upload_address[1])
            

    def respond_publish(self, client_address, arguments):
        """
            @ Description: This process the client's 'publish' command and send a response to acknowledge the client
            @ Input: None
            @ Return: the response in string data type
            @ Output: Update the files data structure of the corresponding ClientInfo object
        """
        # TODO: below are just mock codes for it to work, please modify them
        return 'Server sucessfully recieved your publish request'

    def close(self):
        """
            @ Description: This function close all sockets
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.sock.close()

    def cmd_forever(self):
        """
            @ Description: This function listens forever for the user input
            @ Input: None
            @ Return: None
            @ Output: Execute the all the valid incoming inputs
        """
        while True:
            input_str = input('>> ')
            pattern = r'^\s*\b(?:discover|ping)\b'
            matched = re.search(pattern, input_str)

            if not matched:
                print('Invalid command (please use <discover> or <ping>)!')
                continue
            
            # remove spaces at the beginning or end
            input_str = re.sub(r'^\s+|\s+$', '', input_str)
            # remove redundant spaces
            input_str = re.sub(r'\s\s+', ' ', input_str)

            splited_command = input_str.split()
            if len(splited_command) <= 1:
                print('Please enter the arguments for the command!')
                continue

            if len(splited_command) != 3:
                print('Invalid number of arguments, 2 is required (IP address, port)')
                continue

            command = splited_command[0]
            arguments = splited_command[1:]

            IP = arguments[0]
            port = arguments[1]

            pattern = r'^(?:\d{1,3}\.){3}\d{1,3}$'
            matched = re.search(pattern, IP)
            if not matched:
                print('Invalid IP address format!')
                continue
        
            ip_fields = list(map(lambda s: int(s), IP.split('.')))
            valid_fields = all(ip_field >= 0 and ip_field <= 255 for ip_field in ip_fields)
            if not valid_fields:
                print('Invalid IP address\'s fields!')
                continue

            pattern = r'^\d+$'
            matched = re.search(pattern, port)
            if not matched:
                print('Invalid port number format!')
                continue

            if command == 'ping':
                self.ping(IP, int(port))
            elif command == 'discover':
                self.discover(IP, int(port))


    
    def ping(self, IP: str, port: int):
        """
            @ Description: This function pings the client, with timeout
            @ Input: None
            @ Return: None
            @ Output: print the response to the screen
        """
        # TODO: ping the client and wait for response with timeout
        address = (IP, port)
        if address in self.client_infos.keys():
            # retrieve the client info
            client_info = self.client_infos[address]
            # send ping to sending_socket
            client_info.get_socket().send('ping'.encode())
            # wait for response
            response = client_info.get_socket().recv(1024).decode()
            print(response)
        else:
            print('Client is offline')

    def discover(self, IP, port):
        """
            @ Description: This function discover the client
            @ Input: None
            @ Return: None
            @ Output: print the response to the screen
        """
        # TODO: discover the client
        address = (IP, port)
        if address in self.client_infos.keys():
            # retrieve the client info
            client_info = self.client_infos[address]
            # send ping to sending_socket
            client_info.get_socket().send('discover'.encode())
            # wait for response
            response = client_info.get_socket().recv(1024).decode()
            print(response)
        else:
            print('Client is offline')
        


class ClientInfo():
    def __init__(self, identifying_address=None, identifying_sock=None, sending_address=None, sending_sock=None, upload_address=None, listening_thread=None, files=None):
        self.identifying_address = identifying_address
        self.identifying_sock = identifying_sock
        self.sending_address = sending_address
        self.sending_sock = sending_sock
        self.upload_address = upload_address
        self.listening_thread = listening_thread
        self.files = files

    def set_info(self, identifying_address, identifying_sock, sending_address, sending_sock, upload_address, listening_thread, files):
        self.identifying_address = identifying_address
        self.identifying_sock = identifying_sock
        self.sending_address = sending_address
        self.sending_sock = sending_sock
        self.upload_address = upload_address
        self.listening_thread = listening_thread
        self.files = files

    def get_socket(self):
        return self.sending_sock

def main():
    server = Server()
    try:
        server.start()
    except Exception as e:
        server.close()
        print(f"[Exception] Caught exception in the process: {e}")
    except KeyboardInterrupt as k:
        server.close()

if __name__ == '__main__':
    main()