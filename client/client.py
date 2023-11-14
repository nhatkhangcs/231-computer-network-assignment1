import socket
import threading
import os
import re
from tqdm import tqdm
from config import args
import sys
import select
from typing import List, Dict

class Client():
    def __init__(self, server_host='localhost', server_port=50004) -> None:
        # the socket to listen to server messages
        self.server_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # the socket to send messages to the server
        self.server_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_send_sock.settimeout(10)
        # The upload address (listen forever for upload requests)
        self.upload_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.upload_sock.bind(('localhost', 0))
        self.upload_sock.listen(args.MAX_PARALLEL_DOWNLOADS)

        # server info
        self.server_host = server_host
        self.server_port = server_port

        # the thread to listen to server messages
        self.server_listen_thread = threading.Thread(target=self.listen_server, daemon=True)
        # the thread to listen to download requests from other peers
        self.upload_thread = threading.Thread(target=self.listen_upload, daemon=True)

        # list of unfinished downloads
        self.unfinished_downloads: Dict[str, File] = {}

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
        self.server_send_sock.connect((self.server_host, self.server_port))
        self.server_send_sock.send('first'.encode())

        # second connect to server
        self.server_listen_sock.connect((self.server_host, self.server_port))

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
            try: 
                data = self.server_listen_sock.recv(1024).decode()
            except Exception as e:
                break
            # print('Received:', data)
            if data == '':
                continue
            elif data == 'ping':
                self.respond_ping()
            elif data == 'discover':
                self.respond_discover()
            else:
                raise RuntimeError('[Error] WTF was that command: ' + data)

    def listen_upload(self):
        """
            @ Description: This function listens forever for the download requests from other peer (multithreaded)
            @ Input: None
            @ Return: None
            @ Output: Create many threads to handle the upload parallelly
            @ Additional notes: the request message comes in the form:
                <file name>
        """
        # TODO: forever listen for incoming upload requests
        while True:
            download_socket, _ = self.upload_sock.accept()
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

        while data != 'ready':
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
            pattern = r'^\s*\b(?:publish|fetch|close)\b'
            matched = re.search(pattern, input_str)

            if not matched:
                print('Invalid command (please use <publish> or <fetch> or <close>)!')
                continue

            # remove spaces at the beginning or end
            input_str = re.sub(r'^\s+|\s+$', '', input_str)
            # remove redundant spaces
            input_str = re.sub(r'\s\s+', ' ', input_str)


            splited_command = input_str.split()
            if splited_command[0] == 'close':
                self.close()
                break
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

    def download(self, file_name: str, upload_address: str, position=0):
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
        sock.settimeout(10)
        try: 
            sock.connect((upload_address[0], int(upload_address[1])))
        except ConnectionRefusedError as e:
            print('Failed to connect to peer ' + upload_address[0] + ' ' + upload_address[1] + ' to download file ' + file_name + ', (peer is offline)')
            return
        except socket.timeout as t:
            print('Failed to connect to peer ' + upload_address[0] + ' ' + upload_address[1] + ' to download file ' + file_name + ', (connection timeout)')
            return
        
        full_download = (self.unfinished_downloads.get(file_name) == None)

        if full_download:
            sock.send((file_name + ' ' + str(0)).encode())
        else:
            sock.send((file_name + ' ' + str(self.unfinished_downloads[file_name].current_size)).encode())
        data = recv_timeout(sock, 1024, 20)
        if data == '' or data == None:
            print('Couldn\'t receive the file size of file ' + file_name + ' from peer ' + upload_address[0] + ' ' + upload_address[1] + ', aborting...')
            return
        file_size = int(data)

        try:
            sock.send('ready'.encode())
        except Exception as e:
            print('Failed to send \'ready\' message to peer ' + upload_address[0] + ' ' + upload_address[1] + ' to download file ' + file_name + ', (connection timeout)')
            return
        
        progess_bar = tqdm(total=file_size, desc=file_name, leave=False, unit_scale=True, unit='B', position=position, file=sys.stdout, colour='green')
        if not full_download:
            progess_bar.update(self.unfinished_downloads[file_name].current_size)

        if full_download:
            received_bytes = 0
        else:
            received_bytes = self.unfinished_downloads[file_name].current_size
        data = b''

        with open('temp/' + file_name, 'wb') as file:
            while received_bytes < file_size:
                data = recv_timeout(sock, 65536, 60)
                if data == None or data == '':
                    print('Connection to peer ' + upload_address[0] + ' ' + upload_address[1] + ' is lost while downloading!')
                    if full_download:
                        self.unfinished_downloads[file_name] = File(file_name, file_size, received_bytes)
                    else:
                        self.unfinished_downloads[file_name].current_size = received_bytes
                    return
                received_bytes += len(data)
                progess_bar.update(len(data))
                file.write(data)
                file.flush()
        
        os.replace('temp/' + file_name, 'repo/' + file_name)
        os.remove('temp/' + file_name)

        sock.close()

        if not full_download:
            self.unfinished_downloads.pop(file_name)

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
        self.server_send_sock.settimeout(5)
        self.server_send_sock.send('close'.encode())
        response = recv_timeout(self.server_send_sock, 1024, 10)
        if response == '' or response == None:
            print('Server is offline at shutdown!')
        elif response == 'done':
            print('Server response: ' + response)
        self.close_sockets()
    
    def close_sockets(self):
        self.server_listen_sock.close()
        self.server_send_sock.close()
        self.upload_sock.close()

class File():
    def __init__(self, file_name, full_size_bytes, current_size_bytes) -> None:
        self.file_name = file_name
        self.full_size = full_size_bytes
        self.current_size = current_size_bytes

def recv_timeout(socket: socket.socket, recv_size_byte, timeout=2):
    socket.setblocking(False)
    ready = select.select([socket], [], [], timeout)
    if ready[0]:
        data = socket.recv(recv_size_byte).decode()
        socket.setblocking(True)
        return data
    else:
        socket.setblocking(True)
        return None

def main():
    client = Client()
    try:
        client.start()
    except KeyboardInterrupt as k:
        print('Program interrupted!')
        client.close()
    except BrokenPipeError as b:
        print('Server disconnected!')
        client.close_sockets()
    except socket.timeout as t:
        print("Connection timeout")
        client.close_sockets()
    except Exception as e:
        client.close()
        print(f'[Exception] Caught exception in the process: {e}')
    
if __name__ == '__main__':
    main()