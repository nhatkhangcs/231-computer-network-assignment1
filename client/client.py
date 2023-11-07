import socket
import threading
import os
import re
from tqdm import tqdm
from config import args
import sys

class Client():
    def __init__(self, host='192.168.1.8', port=50004) -> None:
        # the socket to listen to server messages
        self.server_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # the socket to send messages to the server
        self.server_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # The upload address (listen forever for upload requests)
        self.upload_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.upload_sock.bind(('192.168.1.8', 0))
        self.upload_sock.listen(args.MAX_PARALLEL_DOWNLOADS)

        # server info
        self.host = host
        self.port = port

        # the thread to listen to server messages
        self.server_listen_thread = threading.Thread(target=self.listen_server, daemon=True)
        # the thread to listen to download requests from other peers
        self.upload_thread = threading.Thread(target=self.listen_upload, daemon=True)
        # the thread to send messages to the server

        self.setup()

    def start(self):
        """
            @ Description: This function starts all the threads parallelly and wait for joining
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.server_listen_thread.start()
        self.upload_thread.start()
        self.cmd_forever()

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
    
        dir_list = os.listdir("repo")
        send_data = self.server_send_sock.getsockname()[0] + ' ' + str(self.server_send_sock.getsockname()[1]) + \
                            ' ' + self.upload_sock.getsockname()[0] + ' ' + str(self.upload_sock.getsockname()[1]) + \
                            ' ' + ' '.join(dir_list)
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
            # print('Received:', data)
            if data == '':
                continue
            elif data == 'ping':
                self.respond_ping()
            elif data == 'discover':
                self.respond_discover()
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
            download_socket, _ = self.upload_sock.accept()
            # <file name 1> <file name 2> ... <file name n>
            request_file = ''
            while not request_file:
                request_file = download_socket.recv(1024).decode()
            thread = threading.Thread(target=self.upload, args=(request_file, download_socket), daemon=True)
            thread.start()
        
    def upload(self, file_name: str, download_socket: socket.socket):
        """
            @ Description: This function upload the file to other peers
            @ Input: 
                1) file_name - the name of the file to upload
                2) upload_address - the address of the peer to upload to
            @ Return: None
            @ Output: Upload the file sucessfully
        """
        file_size = os.path.getsize('repo/' + file_name)
        download_socket.send(str(file_size).encode())
        data = ''

        while not data:
            data = download_socket.recv(1024).decode()
        with open('repo/' + file_name,'rb') as file:
            data = file.read()
            download_socket.sendall(data)

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
        # send file from client/local to client/repo
        local_file_name = arguments[0]
        repo_file_name = arguments[1]
        if local_file_name not in os.listdir("local"):
            print('File ' + local_file_name + ' does not exist in your local folder!')
            return

        with open("local/" + local_file_name, "rb") as f:
            with open("repo/" + local_file_name, "wb") as f1:
                f1.write(f.read())

        self.server_send_sock.send(('publish ' + repo_file_name).encode())
        data = ''
        while not data:
            data = self.server_send_sock.recv(1024).decode()
        print('Server response: ' + data + '\n')

    def fetch(self, filenames: list[str]):
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
        fetch_cmd = 'fetch ' + ' '.join(filenames)
        self.server_send_sock.send(fetch_cmd.encode())
        data = ''
        while not data:
            data = self.server_send_sock.recv(1024).decode()

        addresses = data.split()
        addresses = [addresses[n:n + 2] for n in range(0, len(addresses), 2)]

        if len(addresses) == 1:
            self.download(filenames[0], addresses[0])
            return
        
        download_threads = []
        for i in range(len(addresses)):
            download_threads.append(threading.Thread(target=self.download, args=[filenames[i], addresses[i], i], daemon=True))
            download_threads[i].start()
        
        for thread in download_threads:
            thread.join()

        sys.stdout.flush()
        print('\n\n')

    def download(self, file_name: str, upload_address: str, position = 0):
        """
            @ Description: This function download the file from other peers
            @ Input: 
                1) file_name - the name of the file to download
                2) upload_address - the address of the peer to download from
            @ Return: None
            @ Output: Download the file sucessfully
        """
        if upload_address[0] == 'null' and upload_address[1] == 'null':
            print('Found no peer to download file ' + file_name)
            return
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: 
            sock.connect((upload_address[0], int(upload_address[1])))
        except ConnectionRefusedError as e:
            print('Failed to connect to peer ' + upload_address[0] + ' ' + upload_address[1] + ' to download file ' + file_name + ', (peer is offline)')
            print(e)
            return
        
        sock.send(file_name.encode())
        data = ''
        while not data:
            data = sock.recv(2048).decode()
        file_size = int(data)
        sock.send('ready'.encode())
        progess_bar = tqdm(total=file_size, desc=file_name, leave=False, unit_scale=True, unit='B', position=position, file=sys.stdout, colour='green')

        received_bytes = 0
        data = b''
        with open('repo/' + file_name, 'wb') as file:
            while received_bytes < file_size:
                data = sock.recv(65536)
                received_bytes += len(data)
                progess_bar.update(len(data))
                file.write(data)
                file.flush()
        
        sock.close()
        # need to make sure that server get updated client repo
        dir_list = os.listdir("repo")
        self.server_send_sock.send(('update ' + ' '.join(dir_list)).encode())

    def respond_ping(self) -> str:
        """
            @ Description: This function responds to the 'ping' message from server
            @ Input: None
            @ Return: The reponse with string datatype
            @ Output: None
        """
        # TODO: respond to server <ping> message here
        self.server_listen_sock.sendall('I\'m online'.encode())

    def respond_discover(self) -> str:
        """
            @ Description: This function responds to the 'discover' message from server
            @ Input: None
            @ Return: The reponse with string datatype
            @ Output: None
        """

        # retrieve all files in client/repo
        dir_list = os.listdir("repo")
        self.server_listen_sock.sendall(' '.join(dir_list).encode())

    def close(self):
        """
            @ Description: This function close all sockets and notify the server
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.server_send_sock.send('close'.encode())
        data = ''
        while not data:
            data = self.server_send_sock.recv(1024).decode()
        self.server_listen_sock.close()
        self.server_send_sock.close()
        self.upload_sock.close()

def main():
    client = Client()
    try:
        client.start()
    except Exception as e:
        client.close()
        print(f'[Exception] Caught exception in the process: {e}')
    except KeyboardInterrupt as k:
        print(k)
        client.close()
    
if __name__ == '__main__':
    main()