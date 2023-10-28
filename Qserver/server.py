import socket
import threading

from config import args
from typing import List
import re

class Server:
    def __init__(self, host='localhost', port=50000) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(args.MAX_CLIENTS)

        self.listening_thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.cmd_thread = threading.Thread(target=self.cmd_forever, daemon=True)
        self.handling_threads: List[threading.Thread] = [None] * args.MAX_CLIENTS

        self.num_current_clients = 0
        self.client_infos = []

    def start(self):
        self.listening_thread.start()
        self.cmd_thread.start()

        self.cmd_thread.join()
        self.listening_thread.join()

    def serve_forever(self):
        while True:
            client_socket, client_address = self.sock.accept()

            self.handling_threads[self.num_current_clients] = threading.Thread(target=self.serve_client, args=(client_socket, client_address))
            self.handling_threads[self.num_current_clients].daemon = True
            self.handling_threads[self.num_current_clients].start()
            self.num_current_clients += 1

            if self.num_current_clients >= args.MAX_CLIENTS:
                for thread in self.handling_threads:
                    thread.join()
                self.num_current_clients = 0
        
            

    def serve_client(self, client_socket: socket.socket, client_address):
        while True:
            data = client_socket.recv(1024).decode()
            

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