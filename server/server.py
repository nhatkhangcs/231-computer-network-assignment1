import socket
import threading
import time
from config import args
import re
import select
from typing import Dict
import time

class Server:     
    def __init__(self, host='localhost', port=50004) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(args.MAX_CLIENTS)
        print(f"Listening on {host} {port}")

        self.listening_thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.cmd_thread = threading.Thread(target=self.cmd_forever, daemon=True)

        # key: The address that client send requests ((IP, port))
        # value: ClientInfo object
        self.client_infos: Dict[str, ClientInfo]  = {}
        self.clients_buffer = {}

    def start(self) -> None:
        """
            @ Description: This function starts all the threads parallelly and wait for joining
            @ Input: None
            @ Return: None
            @ Output: None
        """

        self.listening_thread.start()
        self.cmd_forever()

    def serve_forever(self) -> None:
        """
            @ Description: This function listens for all incoming connection request from clients and start serving clients
                after having enough information
            @ Input: None
            @ Return: None
            @ Output: After having enought information, start a thread to listen to that client immediately
        """

        while True:
            try:
                client_socket, client_address = self.sock.accept()
            except Exception as e:
                return

            data = ''
            while True:
                data = client_socket.recv(8000).decode()
                if data != '':
                    break
            
            # later connection to server from client
            if data != 'first':
                data = data.split()

                if data[0] == 'keepalive':
                    original_IP = data[1]
                    original_port = int(data[2])
                    if self.client_infos[(original_IP, original_port)].listen_keep_alive_sock == None:
                        client_info: ClientInfo = self.client_infos[(original_IP, original_port)]
                        client_info.listen_keep_alive_sock = client_socket
                        client_info.listen_keep_alive_thread = threading.Thread(target=self.listen_keep_alive, args=[client_socket, (original_IP, original_port)], daemon=True)
                        client_info.listening_thread.start()
                        client_info.listen_keep_alive_thread.start()
                        continue

                original_IP = data[0]
                original_port = int(data[1])

                upload_IP = data[2]
                upload_port = int(data[3])

                repoFiles = data[4:]

                if (original_IP, original_port) not in self.client_infos:
                    self.clients_buffer[(original_IP, original_port)] = ClientInfo(
                        identifying_address=(original_IP, original_port),
                        sending_address=client_address,
                        sending_sock=client_socket,
                        upload_address=(upload_IP, upload_port),
                        files=repoFiles
                    )

                else:
                    client_info: ClientInfo = self.client_infos[(original_IP, original_port)]
                    client_info.sending_address=client_address
                    client_info.sending_sock=client_socket
                    client_info.upload_address=(upload_IP, upload_port)
                    client_info.listening_thread=threading.Thread(target=self.serve_client, args=[client_info.identifying_sock, client_info.identifying_address], daemon=True)
                    client_info.files=repoFiles
            
            # First connection to server from client
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


    def listen_keep_alive(self, client_socket: socket.socket, client_address: str) -> None:
        """
            @ Description: This function listens for keep alive messages from client and respond to them
            @ Input:
                1) client_socket: the socket that the server uses to communicate with the client
                2) client_address: the address of the client
            @ Return: None
            @ Output: None
        """
        client_socket.settimeout(3)
        try:
            while True:
                time.sleep(60)
                # print('listening')
                data = None
                try:
                    data = recv_timeout(client_socket, 1024, 20)
                except Exception as e:
                    self.remove_client(client_address, send_response=False)
                    break

                if data == None or data.decode() == '' or data.decode() != 'keepalive':
                    self.remove_client(client_address, send_response=False)
                    break

                if send_timeout(client_socket, 'keepalive'.encode(), 20) == False:
                    self.remove_client(client_address, send_response=False)
                    break

        except Exception as e:
            if client_address in self.client_infos.keys():
                self.remove_client(client_address, send_response=False)


    def serve_client(self, client_socket: socket.socket, client_address: str):
        """
            @ Description: This function listen for clients requests and respond to them
            @ Input:
                1) client_socket: the socket that the server uses to communicate with the client
                2) client_address: the address of the client
            @ Return: None
            @ Output: None
        """
        while True:
            try:
                data = client_socket.recv(1024).decode()
            except Exception as e:
                break
            if data == '':
                continue
            data = data.split(' ')
            command = data[0]
            arguments = data[1:]
            if command == 'fetch':
                response = self.respond_fetch(client_address, arguments)
                client_socket.send(response.encode())
            elif command == 'publish':
                response = self.respond_publish(client_address, arguments)
                client_socket.send(response.encode())
            elif command == 'update':
                self.respond_update(client_address, arguments)
            elif command == 'close':
                self.remove_client(client_address)


    def remove_client(self, client_address: str, send_response=True) -> None:
        """
            @ Description: This function removes the client from the list of clients
            @ Input:
                1) client_address: the address of the client
                2) send_response: whether or not to send a response to the client
            @ Return: None
            @ Output: None
        """
        if send_response:
            self.client_infos[client_address].get_identifying_sock().send('done'.encode())
        self.client_infos[client_address].get_identifying_sock().close()
        self.client_infos[client_address].get_sending_sock().close()
        self.client_infos[client_address].get_listen_keep_alive_sock().close()
        self.client_infos.pop(client_address)


    def respond_update(self, client_address: str, file_names: list[str]) -> None:
        """
            @ Description: This function updates the list of files of the client
            @ Input:
                1) client_address: the address of the client
                2) file_names: the list of files of the client
            @ Return: None
            @ Output: None
        """
        if client_address in self.client_infos.keys():
            self.client_infos[client_address].files = file_names


    def respond_fetch(self, client_address: str, file_names: list[str]) -> str:
        """
            @ Description: This function returns the list of peers' address that the client can connect to download 
            @ Input:
                1) client_address: the address of the client
                2) file_names: the list of files that the client wants to download
            @ Return: the list of peers for downloading, in the form
                <upload peer 1 IP> <upload peer 1 port> <upload peer 2 IP> <upload peer 2 port> ...
                with  <upload peer i IP> <upload peer i port> correspond to the file. If the file doesn't exist, return "null null"
            @ Output: None
        """
        file_name = file_names[0]
        avail_list = []
        for addr in self.client_infos.keys():
            if file_name in self.client_infos[addr].get_files() and addr != client_address:
                avail_list.append(addr)

        return_addressess = ''
        if avail_list:
            for addr in avail_list:
                return_addressess += self.client_infos[addr].get_upload_addr()[0] + ' ' + str(self.client_infos[addr].get_upload_addr()[1]) + ' '
        else:
            return_addressess += 'null null '

        return return_addressess.strip()    
        
    def respond_publish(self, client_address: str, repo_file_name: str) -> str:
        """
            @ Description: This process the client's 'publish' command and send a response to acknowledge the client
            @ Input:
                1) client_address: the address of the client
                2) repo_file_name: the file that the client wants to publish
            @ Return: the response in string data type
            @ Output: Update the files data structure of the corresponding ClientInfo object
        """
        repo_file_name = repo_file_name[0]
        if repo_file_name not in self.client_infos[client_address].get_files():
            self.client_infos[client_address].get_files().append(repo_file_name)
        return 'success'

    def close(self) -> None:
        """
            @ Description: This function close all sockets
            @ Input: None
            @ Return: None
            @ Output: None
        """
        
        self.sock.close()
        for address in self.client_infos.keys():
            self.client_infos[address].get_sending_sock().close()
            self.client_infos[address].get_identifying_sock().close()
        
        # terminate all threads
        # self.listening_thread.join()

    def cmd_forever(self) -> None:
        """
            @ Description: This function listens forever for the user input
            @ Input: None
            @ Return: None
            @ Output: Execute the all the valid incoming inputs
        """

        while True:
            input_str = input('>> ')
            # if user entered nothing, continue
            if input_str == '': continue
            
            pattern = r'^\s*\b(?:discover|ping|list)\b'
            matched = re.search(pattern, input_str)

            if not matched:
                print('Invalid command (please use <discover> or <ping>)!')
                continue
            
            # remove spaces at the beginning or end
            input_str = re.sub(r'^\s+|\s+$', '', input_str)
            # remove redundant spaces
            input_str = re.sub(r'\s\s+', ' ', input_str)

            splited_command = input_str.split()
            if splited_command[0] == 'list':
                self.list_out()
                print()
                continue

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

            print()

    def list_out(self) -> None:
        """
            @ Description: This function list out all the current clients
            @ Input: None
            @ Return: None
            @ Output: print the response to the screen
        """
        # list out all the current clients
        for client_address in self.client_infos.keys():
            print(str(client_address))
    
    def ping(self, IP: str, port: int) -> None:
        """
            @ Description: This function pings the client, with timeout
            @ Input:
                1) IP: the IP address of the client
                2) port: the port number of the client
            @ Return: None
            @ Output: print the response to the screen
        """

        address = (IP, port)
        if address in self.client_infos.keys():
            # retrieve the client info
            client_info: ClientInfo = self.client_infos[address]
            # send ping to sending_socket
            try:
                client_info.get_sending_sock().send('ping'.encode())
            except Exception as e:
                print('Client is offline')
                return
            start = time.time()
            data = recv_timeout(client_info.get_sending_sock(), 1024, 5)
            end = time.time()

            if len(data) == 0 or data == None:
                print('Request timed out')
                self.client_infos.pop(address)
                return
            
            latency = end - start
            data = data.decode()

            print(f"Response latency: {latency*1000:0.3f} ms")
            print(data)

        else:
            print('Client is offline')

    def discover(self, IP: str, port: int) -> None:
        """
            @ Description: This function discover the client
            @ Input:
                1) IP: the IP address of the client
                2) port: the port number of the client
            @ Return: None
            @ Output: print the response to the screen
        """
        address = (IP, port)
        if address in self.client_infos.keys():
            # retrieve the client info
            client_info: ClientInfo = self.client_infos[address]
            # send ping to sending_socket
            try:
                client_info.get_sending_sock().send('discover'.encode())
            except Exception as e:
                print('Client is offline')
                self.client_infos.pop(address)
                return
            # wait for response
            response = recv_timeout(client_info.get_sending_sock(), 8000, 10)
            if len(response) == 0 or response == None:
                print('Request timed out')
                self.client_infos.pop(address)
                return
            response = response.decode().split()
            print('----------------------------------')
            for file in response:
                print(file)
            print('----------------------------------')

        else:
            print('Client is offline')
        
class ClientInfo():
    def __init__(self, identifying_address=None, identifying_sock=None, 
                 sending_address=None, sending_sock=None, upload_address=None, 
                 listening_thread=None, files=None, listen_keep_alive_sock=None,
                 listen_keep_alive_thread=None) -> None:
        self.identifying_address = identifying_address
        self.identifying_sock = identifying_sock
        self.sending_address = sending_address
        self.sending_sock = sending_sock
        self.upload_address = upload_address
        self.listening_thread = listening_thread
        self.files = files
        self.listen_keep_alive_sock = listen_keep_alive_sock
        self.listen_keep_alive_thread = listen_keep_alive_thread

    def get_sending_sock(self) -> socket.socket:
        return self.sending_sock
    
    def get_identifying_sock(self) -> socket.socket:
        return self.identifying_sock
    
    def get_listen_keep_alive_sock(self) -> socket.socket:
        return self.listen_keep_alive_sock
    
    def get_upload_addr(self) -> str:
        return self.upload_address
    
    def get_files(self) -> list[str]:
        return self.files
    
def recv_timeout(socket: socket.socket, recv_size_byte, timeout=2) -> bytearray:
    socket.setblocking(False)
    ready = select.select([socket], [], [], timeout)
    if ready[0]:
        data = socket.recv(recv_size_byte)
        socket.setblocking(True)
        return data
    else:
        socket.setblocking(True)
        return None
    
def send_timeout(socket: socket.socket, data: bytearray, timeout=2) -> bool:
    socket.setblocking(False)
    ready = select.select([], [socket], [], timeout)
    if ready[1]:
        socket.send(data)
        socket.setblocking(True)
        return True
    else:
        socket.setblocking(True)
        return False

def main():
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt as k:
        print("Program interrupted")
        server.close()
    except Exception as e:
        server.close()
        print(f"[Exception] Caught exception in the process: {e}")

if __name__ == '__main__':
    main()