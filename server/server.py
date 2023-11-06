import socket
import threading
import time
from config import args
import re

class Server:     
    def __init__(self, host='192.168.1.8', port=50004) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(args.MAX_CLIENTS)
        print(f"Listening on {host} {port}")

        self.listening_thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.cmd_thread = threading.Thread(target=self.cmd_forever, daemon=True)

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

        self.cmd_forever()

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
            
            # later connection to server from client
            if data != 'NONE':
                data = data.split()
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
                    client_info.listening_thread.start()
            
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


    def remove_client(self, client_address):
        self.client_infos[client_address].get_identifying_sock().send('OK'.encode())
        self.client_infos.pop(client_address)

    def respond_update(self, client_address, file_names):
        if client_address in self.client_infos.keys():
            self.client_infos[client_address].files = file_names


    def respond_fetch(self, client_address, file_names):
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
        return_addressess = ''
        total_client_list = {}
        for file_name in file_names:
            avail_list = []
            for addr in self.client_infos.keys():
                if file_name in self.client_infos[addr].get_files() and addr != client_address:
                    avail_list.append(addr)
            
            total_client_list.update({file_name: avail_list})
            
        if total_client_list:
            for file_name in total_client_list.keys():
                if total_client_list[file_name]:
                    # find address with minimum number of files in repo directory
                    found_address = min(total_client_list[file_name], key=lambda addr: len(self.client_infos[addr].get_files()))
                else:
                    found_address = None

                print("Address to download: ", found_address)
                if found_address:
                    return_addressess += self.client_infos[found_address].get_upload_addr()[0] + ' ' + str(self.client_infos[found_address].get_upload_addr()[1]) + ' '
                else:
                    return_addressess += 'null null '
        
        return return_addressess.strip()
        

    def respond_publish(self, client_address, repo_file_name):
        """
            @ Description: This process the client's 'publish' command and send a response to acknowledge the client
            @ Input: None
            @ Return: the response in string data type
            @ Output: Update the files data structure of the corresponding ClientInfo object
        """
        if repo_file_name not in self.client_infos[client_address].get_files():
            self.client_infos[client_address].get_files().append(repo_file_name)
        return 'success'

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
            client_info: ClientInfo = self.client_infos[address]
            # send ping to sending_socket
            client_info.get_socket().send('ping'.encode())
            Time1 = time.time()
            data = ""
            while not data:
                # get latency time
                latency = time.time() - Time1
                if latency > 5:
                    print('Request timed out')
                    self.client_infos.pop(address)
                    return
            
                data = client_info.get_socket().recv(1024).decode()
            print("Response latency: " + str(int(round(latency * 1000))))
            print(data)
            # wait for response
            
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
            client_info: ClientInfo = self.client_infos[address]
            # send ping to sending_socket
            client_info.get_socket().send('discover'.encode())
            # wait for response
            response = client_info.get_socket().recv(1024).decode().split()
            for file in response:
                print(file)
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

    def get_socket(self) -> socket.socket:
        return self.sending_sock
    
    def get_identifying_sock(self) -> socket.socket:
        return self.identifying_sock
    
    def get_files(self):
        return self.files
    
    def get_upload_addr(self):
        return self.upload_address

def main():
    server = Server()
    try:
        server.start()
    except Exception as e:
        server.close()
        print(f"[Exception] Caught exception in the process: {e}")
    except KeyboardInterrupt as k:
        print(k)
        server.close()

if __name__ == '__main__':
    main()