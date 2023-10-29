import socket
import threading

from config import args
from typing import List
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
        self.client_infos = {}
        self.clients_buffer = {}

    def start(self):
        self.listening_thread.start()
        self.cmd_thread.start()

        self.cmd_thread.join()
        self.listening_thread.join()

    def serve_forever(self):
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
        # TODO: below are just mock codes for it to work, please modify them
        while True:
            data = client_socket.recv(1024).decode()
            if data == '':
                continue
            if data == 'fetch':
                response = self.fetch(client_address, [])
            elif data == 'publish':
                response = self.publish(client_address, [])

            client_socket.send(response.encode())


    def fetch(self, client_address, arguments):
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
            

    def publish(self, client_address, arguments):
        return 'Server sucessfully recieved your publish request'

    def close(self):
        self.sock.close()

    def cmd_forever(self):
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

            if len(splited_command) != 2:
                print('Invalid number of arguments, 2 is required (IP address, port)')
                continue

            command = splited_command[0]
            arguments = splited_command[1:]

            address = arguments[0]
            port = arguments[1]

            pattern = r'^(?:\d{1,3}\.){3}\d{1,3}$'
            matched = re.search(pattern, address)
            if not matched:
                print('Invalid IP address format!')
                continue
        
            ip_fields = list(map(lambda s: int(s), address.split('.')))
            valid_fields = all(ip_field >= 0 and ip_field <= 255 for ip_field in ip_fields)
            if not valid_fields:
                print('Invalid IP address\'s fields!')
                continue

            pattern = r'^\d+$'
            matched = re.search(pattern, address)
            if not matched:
                print('Invalid port number format!')
                continue

            if command == 'ping':
                self.ping(address, port)
            elif command == 'discover':
                self.discover(address, port)


    
    def ping(self, address, port):
        # TODO: ping the client and wait for response with timeout
        pass

    def discover(self, address, port):
        # TODO: discover the client
        pass

class ClientInfo():
    def __init__(self, identifying_address=None, identifying_sock=None, sending_address=None, sending_sock=None, upload_address=None, listening_thread=None):
        self.identifying_address = identifying_address
        self.identifying_sock = identifying_sock
        self.sending_address = sending_address
        self.sending_sock = sending_sock
        self.upload_address = upload_address
        self.listening_thread = listening_thread

    def set_info(self, identifying_address, identifying_sock, sending_address, sending_sock, upload_address, listening_thread):
        self.identifying_address = identifying_address
        self.identifying_sock = identifying_sock
        self.sending_address = sending_address
        self.sending_sock = sending_sock
        self.upload_address = upload_address
        self.listening_thread = listening_thread

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