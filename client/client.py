import socket
import threading
import os
import re
from tqdm import tqdm
from config import args
import sys
import select
from typing import List, Dict
import time

class Client():
    def __init__(self, server_host='localhost', server_port=50004, upload_IP='localhost') -> None:
        # the socket to listen to server messages
        self.server_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # the socket to send messages to the server
        self.server_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_send_sock.settimeout(10)
        # The upload address (listen forever for upload requests)
        self.upload_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.upload_sock.bind((upload_IP, 0))
        self.upload_sock.listen(args.DOWNLOAD_QUEUE_LENGTH)

        # The keep-alive sockets
        self.send_keep_alive_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # server info
        self.server_host = server_host
        self.server_port = server_port

        # the thread to listen to server messages
        self.server_listen_thread = threading.Thread(target=self.listen_server, daemon=True)
        # the thread to listen to download requests from other peers
        self.upload_thread = threading.Thread(target=self.listen_upload, daemon=True)
        # the thread to send keep-alive messages to server
        self.send_keep_alive_thread = threading.Thread(target=self.send_keep_alive, daemon=True)

        # list of unfinished downloads
        self.unfinished_downloads: Dict[str, File] = {}

        # create missing folders
        if not os.path.exists('local'):
            os.makedirs('local')
        if not os.path.exists('repo'):
            os.makedirs('repo')
        if not os.path.exists('temp'):
            os.makedirs('temp')

        # remove all temp files
        for file in os.listdir('temp'):
            os.remove('temp/' + file)

        # file downloading
        self.is_download = False

        # file uploading
        self.num_uploads = 0
        self.num_uploads_lock = threading.Lock()

        self.setup()

    def start(self) -> None:
        """
            @ Description: This function starts all the threads parallelly and wait for joining
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.server_listen_thread.start()
        self.upload_thread.start()
        self.send_keep_alive_thread.start()
        self.cmd_forever()

    def setup(self) -> None:
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

        self.send_keep_alive_sock.connect((self.server_host, self.server_port))
        self.send_keep_alive_sock.send(('keepalive ' + self.server_send_sock.getsockname()[0] + ' ' + str(self.server_send_sock.getsockname()[1])).encode())

        print('Sending address: ' + self.server_send_sock.getsockname()[0] + ' ' + str(self.server_send_sock.getsockname()[1]))
        print('Listening address: ' + self.server_listen_sock.getsockname()[0] + ' ' + str(self.server_listen_sock.getsockname()[1]))
        print('Upload address: ' + self.upload_sock.getsockname()[0] + ' ' + str(self.upload_sock.getsockname()[1]))
    
    def send_keep_alive(self):
        """
            @ Description: This function sends keep-alive messages to server
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.send_keep_alive_sock.settimeout(10)
        while True:
            time.sleep(60)
            # print('sending keep alive')
            if send_timeout(self.send_keep_alive_sock, 'keepalive'.encode(), 20) == False and self.is_download == False:
                self.num_uploads_lock.acquire()
                if self.num_uploads == 0:
                    self.num_uploads_lock.release()
                    self.force_close()
                    break
                self.num_uploads_lock.release()


            data = recv_timeout(self.send_keep_alive_sock, 1024, 20)

            if (len(data) == 0 or data == None) and self.is_download == False:
                self.num_uploads_lock.acquire()
                if self.num_uploads == 0:
                    self.num_uploads_lock.release()
                    self.force_close()
                    break
                self.num_uploads_lock.release()
                break

    def force_close(self):
        """
            @ Description: This function force close the client
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.close_sockets()
        print('Connection to server is lost, shutting down...')
        os._exit(0)

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
            if len(data) == 0:
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
        while True:
            try:
                download_socket, _ = self.upload_sock.accept()
            except Exception as e:
                break
            request_file_and_offset = ''
            while not request_file_and_offset:
                request_file_and_offset = download_socket.recv(1024).decode()
            request_file_and_offset = request_file_and_offset.split()
            request_file = request_file_and_offset[0]
            request_offset = int(request_file_and_offset[1])
            thread = threading.Thread(target=self.upload, args=(request_file, request_offset, download_socket), daemon=True)
            thread.start()
            self.mutate_num_uploads(1)

        
    def upload(self, file_name: str, byte_offset: int, download_socket: socket.socket) -> None:
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
            try:
                data = download_socket.recv(1024).decode()
            except Exception as e:
                print('Something went wrong')
                self.mutate_num_uploads(-1)
                return
        with open('repo/' + file_name,'rb') as file:
            file.seek(byte_offset)
            data = file.read()
            try:
                download_socket.sendall(data)
            except Exception as e:
                self.mutate_num_uploads(-1)
                return
            
        self.mutate_num_uploads(-1)


    def cmd_forever(self):
        """
            @ Description: This function listens forever for the user input
            @ Input: None
            @ Return: None
            @ Output: Execute the all the valid incoming inputs
        """
        while True:
            input_str = input('>> ')
            if input_str == '': continue
            pattern = r'^\s*\b(?:publish|fetch|close|list)\b'
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

            if splited_command[0] == 'list':
                self.list_out()
                continue
            
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
                self.is_download = True
                self.fetch(arguments)
                self.is_download = False

    def list_out(self) -> None:
        """
            @ Description: This function execute the 'list' command
            @ Input: None
            @ Return: None
            @ Output: Execute the 'list' command and receive respond from the server
        """
        dir_list = os.listdir("repo")
        print('----------------------------------')
        for file in dir_list:
            print(file)
        
        print('----------------------------------')
        print()

    def publish(self, arguments) -> None:
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
        
        try:
            self.server_send_sock.sendall(('publish ' + repo_file_name).encode())
        except Exception as e:
            print('Server is offline!')
            return

        data = recv_timeout(self.server_send_sock, 1024, 20)
        if len(data) == 0 or data == None:
            print('Server is offline, no response!')
            return
        
        
        data = data.decode()
        print('Server response: ' + data + '\n')

        with open("local/" + local_file_name, "rb") as f:
            with open("repo/" + repo_file_name, "wb") as f1:
                f1.write(f.read())



    def fetch(self, filenames: list[str]) -> None:
        """
            @ Description: This function execute the 'fetch' command (multithreaded)
            @ Input: arguments - the list of file names to download, comes in the form
                <file name 1> <file name 2> ... <file name n>
            @ Return: None
            @ Output: Execute the 'fetch' command and download the files sucessfully
            @ Additional notes: 
                1) If the number of files > 1, open threads to handle download parralelly
        """

        # filter
        filenames = [filename for filename in filenames if filename not in os.listdir("repo")]
        if len(filenames) == 0:
            print('All files are already in your repository!')
            return

        file_to_addrs: Dict[str, List[str]] = {}
        for filename in filenames:
            fetch_cmd = 'fetch ' + filename
            self.server_send_sock.send(fetch_cmd.encode())
            data = ''
            data = recv_timeout(self.server_send_sock, 8000, 20)
            if len(data) == 0 or data == None:
                print('Server is offline, no response!')
                return
            data = data.decode()
            
            if data != 'null null':
                addresses = data.split()
                addresses = [addresses[n:n + 2] for n in range(0, len(addresses), 2)]
                file_to_addrs[filename] = addresses

        if len(file_to_addrs) == 0:
            print('Found no peer to download!')
            return
        
        for i, (filename, addrs) in enumerate(file_to_addrs.items()):
            print('Available peers for file ' + filename + ':')
            for addr in addrs:
                print('\t' + addr[0] + ' ' + addr[1])

        if len(file_to_addrs.keys()) == 1:
            filename = list(file_to_addrs.keys())[0]
            addrs = file_to_addrs[filename]
            self.handle_download(filename, addrs, 0)
            return
        
        download_threads = []
        for i, (filename, addrs) in enumerate(file_to_addrs.items()):
            download_threads.append(threading.Thread(target=self.handle_download, args=[filename, addrs, i], daemon=True))
            download_threads[i].start()
            
        for thread in download_threads:
            thread.join()

        sys.stdout.flush()
        print()

    def handle_download(self, filename: str, upload_addresses: List[str], position: int) -> None:
        """
            @ Description: This function handle the download of a single file
            @ Input: 
                1) filename - the name of the file to download
                2) upload_addresses - the list of addresses of the peers to download from
                3) position - the position of the progress bar
            @ Return: None
            @ Output: Download the file sucessfully
        """
        download_success = False
        for upload_address in upload_addresses:
            download_success = self.download(filename, upload_address, position)
            if download_success:
                break

        if not download_success:
            print('Failed to download file ' + filename + ' from all available peers!')
            return

    def download(self, file_name: str, upload_address: str, position=0) -> bool:
        """
            @ Description: This function download the file from other peers
            @ Input: 
                1) file_name - the name of the file to download
                2) upload_address - the address of the peer to download from
            @ Return: None
            @ Output: Download the file sucessfully
        """
        if upload_address[0] == 'null' and upload_address[1] == 'null':
            return False
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        try: 
            sock.connect((upload_address[0], int(upload_address[1])))
        except ConnectionRefusedError as e:
            print('Failed to connect to peer ' + upload_address[0] + ' ' + upload_address[1] + ' to download file ' + file_name + ', (peer is offline)')
            return False
        except socket.timeout as t:
            print('Failed to connect to peer ' + upload_address[0] + ' ' + upload_address[1] + ' to download file ' + file_name + ', (connection timeout)')
            return False
        
        full_download = (self.unfinished_downloads.get(file_name) == None)

        if full_download:
            sock.send((file_name + ' ' + str(0)).encode())
        else:
            sock.send((file_name + ' ' + str(self.unfinished_downloads[file_name].current_size)).encode())
        data = recv_timeout(sock, 1024, 20)
        if len(data) == 0 or data == None:
            print('Couldn\'t receive the file size of file ' + file_name + ' from peer ' + upload_address[0] + ' ' + upload_address[1] + ', aborting...')
            return False
        data = data.decode()
        file_size = int(data)

        try:
            sock.send('ready'.encode())
        except Exception as e:
            print('Failed to send \'ready\' message to peer ' + upload_address[0] + ' ' + upload_address[1] + ' to download file ' + file_name + ', (connection timeout)')
            return False
        
        download_description = file_name + ' from ' + '(' + upload_address[0] + ', ' + upload_address[1] + ')'
        progess_bar = tqdm(total=file_size, desc=download_description, leave=True, unit_scale=True, unit='B', position=position, file=sys.stdout, colour='green')


        if full_download:
            received_bytes = 0
        else:
            received_bytes = self.unfinished_downloads[file_name].current_size
        data = b''

        with open('temp/' + file_name, 'wb') as file:
            if not full_download:
                progess_bar.update(self.unfinished_downloads[file_name].current_size)
                file.seek(self.unfinished_downloads[file_name].current_size)
            while received_bytes < file_size:
                data = recv_timeout(sock, 65536, 60)
                if data == None or len(data) == 0:
                    print('Connection to peer ' + upload_address[0] + ' ' + upload_address[1] + ' is lost while downloading!')
                    if full_download:
                        self.unfinished_downloads[file_name] = File(file_name, file_size, received_bytes)
                    else:
                        self.unfinished_downloads[file_name].current_size = received_bytes
                    return False
                received_bytes += len(data)
                progess_bar.update(len(data))
                file.write(data)
                file.flush()
        
        os.replace('temp/' + file_name, 'repo/' + file_name)

        sock.close()

        if not full_download:
            self.unfinished_downloads.pop(file_name)

        # need to make sure that server get updated client repo
        dir_list = os.listdir("repo")
        self.server_send_sock.send(('update ' + ' '.join(dir_list)).encode())

        return True

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

    def close(self) -> None:
        """
            @ Description: This function close all sockets and notify the server
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.server_send_sock.settimeout(5)
        try:
            self.server_send_sock.send('close'.encode())
        except Exception as e:
            print('Server is offline at shutdown!')
            self.close_sockets()
            return
        
        response = recv_timeout(self.server_send_sock, 1024, 10)
        if len(response) == 0 or response == None:
            print('Server is offline at shutdown!')
        elif response.decode() == 'done':
            print('Server response: ' + response.decode())
        self.close_sockets()
    
    def close_sockets(self) -> None:
        """
            @ Description: This function close all sockets
            @ Input: None
            @ Return: None
            @ Output: None
        """
        self.server_listen_sock.close()
        self.server_send_sock.close()
        self.upload_sock.close()
        self.send_keep_alive_sock.close()

    def mutate_num_uploads(self, num: int) -> None:
        """
            @ Description: This function mutate the number of uploads
            @ Input: num - the number to add to the current number of uploads
            @ Return: None
            @ Output: None
        """
        self.num_uploads_lock.acquire()
        self.num_uploads += num
        self.num_uploads_lock.release()

def recv_timeout(socket: socket.socket, recv_size_byte, timeout=2) -> bytearray:
    socket.setblocking(False)
    ready = select.select([socket], [], [], timeout)
    if ready[0]:
        try:
            data = socket.recv(recv_size_byte)
        except Exception as e:
            socket.setblocking(True)
            return None
        socket.setblocking(True)
        return data
    else:
        socket.setblocking(True)
        return None
    
def send_timeout(socket: socket.socket, data: bytearray, timeout=2) -> bool:
    socket.setblocking(False)
    ready = select.select([], [socket], [], timeout)
    if ready[1]:
        try:
            socket.send(data)
        except Exception as e:
            socket.setblocking(True)
            return False
        socket.setblocking(True)
        return True
    else:
        socket.setblocking(True)
        return False
    
class File():
    def __init__(self, file_name, full_size_bytes, current_size_bytes) -> None:
        self.file_name = file_name
        self.full_size = full_size_bytes
        self.current_size = current_size_bytes

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