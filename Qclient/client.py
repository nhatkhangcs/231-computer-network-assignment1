import socket
import threading

from config import args
from typing import List
import re

class Client():
    def __init__(self, host='localhost', port=50005) -> None:
        self.server_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.upload_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.upload_sock.bind(('localhost', 0))
        self.upload_sock.listen(15)

        self.host = host
        self.port = port

        self.server_listen_thread = threading.Thread(target=self.listen_server, daemon=True)
        self.upload_thread = threading.Thread(target=self.listen_upload, daemon=True)
        self.server_send_thread = threading.Thread(target=self.cmd_forever, daemon=True)

        self.setup()

    def start(self):
        self.server_send_thread.start()
        self.server_listen_thread.start()
        self.upload_thread.start()

        self.server_send_thread.join()
        self.server_listen_thread.join()
        self.upload_thread.join()

    def setup(self):
        # first connect to server
        self.server_send_sock.connect((self.host, self.port))
        self.server_send_sock.send('NONE'.encode())

        # second connect to server
        self.server_listen_sock.connect((self.host, self.port))
        print('Listening address: ' + self.server_listen_sock.getsockname()[0] + ' ' + str(self.server_listen_sock.getsockname()[1]))

        # tell the server which original connection this connection belongs to
        # tell the server the downloading address that other clients can reach out to
        send_data = self.server_send_sock.getsockname()[0] + ' ' + str(self.server_send_sock.getsockname()[1]) + \
                            ' ' + self.upload_sock.getsockname()[0] + ' ' + str(self.upload_sock.getsockname()[1])
        self.server_listen_sock.send(send_data.encode())
        print('Sending address: ' + self.server_send_sock.getsockname()[0] + ' ' + str(self.server_send_sock.getsockname()[1]))
        print('Upload address: ' + self.upload_sock.getsockname()[0] + ' ' + str(self.upload_sock.getsockname()[1]))
    
    def listen_server(self):
        while True:
            data = self.server_listen_sock.recv(1024).decode()
            if data == '':
                continue
            elif data == 'ping':
                send_data = self.respond_ping()
            elif data == 'discover':
                send_data = self.respond_discover()
            else:
                raise RuntimeError('[Error] WTF was that command: ' + data)
            
            self.server_listen_sock.send(send_data.encode())

    def listen_upload(self):
        # TODO: forever listen for incoming upload requests, there can be multiple upload requests from a client as the same time
        while True:
            download_socket, download_address = self.upload_sock.accept()
            # TODO: create threads and handle download requests

    def cmd_forever(self):
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
        # TODO: publish file from local to repo here
        self.server_send_sock.send('publish'.encode())
        response = self.server_send_sock.recv(1024).decode()
        print(response)

    def fetch(self, arguments):
        # TODO: request fetching files from server and open socket, threads to download here
        self.server_send_sock.send('fetch'.encode())
        response = self.server_send_sock.recv(1024).decode()
        print(response)


    def respond_ping(self) -> str:
        # TODO: respond to server <ping> message here
        pass

    def respond_discover(self) -> str:
        # TODO: respond to server <discover> message here
        pass

    def close(self):
        self.server_listen_sock.close()
        self.server_send_sock.close()
        self.upload_sock.close()

def main():
    client = Client()
    try:
        client.start()
    except Exception as e:
        client.close()
        print(f'Exception] Caught exception in the process: {e}')
    except KeyboardInterrupt as k:
        client.close()

if __name__ == '__main__':
    main()