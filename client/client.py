import os
from threading import Thread
import socket



class client:
    localDir = 'local/'
    remoteDir = 'uploaded/'
    HOME_DIR = "client/"

    def __init__(self, hostname):
        self.hostname = hostname
        self.session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    ### Methods for creating connection to server ###
    def createConnection(self, serverIP, serverPort):
        '''
            Args: serverIP, serverPort
            Returns: A message indicating if the connection was successful
        '''
        try:
            self.session.connect((serverIP, serverPort))
        except Exception as e:
            print("Connection failed:", e)
            return
        #create connection to server
        
        #self.threading()

    def closeConnection(self):
        '''
            Args: None
            Returns: A message if connection was closed successfully
        '''

        self.session.close()
        return "Connection closed successfully"

    def threading(self):
        '''
            Args: None
            Returns: None
        '''

    def sendFile(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully sent
        '''
        try:
            if fileName not in os.listdir(self.HOME_DIR):
                return "File not found"
            with open(fileName) as f:
                self.session.sendall(f.read())
            return "File sent successfully"
        except Exception as e:
            print(e)
            return "File not sent"

    ### Methods for client to interact with server and other clients ###
    def repoInfo(self):
        '''
            Args: None
            Returns: list of files in local repo
        '''
        return os.listdir(self.localDir)
        

    def uploadFile(self, fileName, uploadName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully uploaded
        '''
        
        try:
            # from local to remote
            with open(self.localDir + fileName, 'rb') as f:
                # copy file to remote
                with open(self.remoteDir + uploadName, 'wb') as f2:
                    f2.write(f.read())
            return "File uploaded successfully"
        except Exception as e:
            print(e)
            return "File not uploaded"


    def deleteFileLocal(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully deleted
        '''
        
        return "File deleted successfully"

    def deleteFileRemote(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully deleted
        '''
        

    def fetchFile(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully downloaded
            Description: Client query to server for file. Server query other clients
                to see if any other client is keeping the file. If yes, server will
                choose the client with smallest responding time, and request that
                client to create a peer-to-peer connection with the client that
                requested the file. The client that requested the file will then
                download the file from the other client.
        '''
        #print(self.repoInfo())
        
        if fileName in self.repoInfo():
            print("File already exists")

        else:
            file = open(self.remoteDir + fileName, 'rb')
            # copy file to remote
            filesize = os.path.getsize(self.remoteDir + fileName)
            self.session.send(fileName.encode())

            print(fileName, filesize)
            self.session.send(str(filesize).encode())
            data = file.read()
            self.session.sendall(data)
            self.session.sendall(b"<END>")
            file.close()
            return "File downloaded successfully"


    def commandLoop(self):
        '''
            Args: None
            Returns: None
            Description:
                The client has a simple command-shell interpreter that is used to accept two kinds of commands.
                – publish lname fname: a local file (which is stored in the client’s file system at lname) is added to the
                client’s repository as a file named fname and this information is conveyed to the server.
                – fetch fname: fetch some copy of the target file and add it to the local repository
        '''
        while True:
            command = input(">>> ")
            command = command.split()

            # 2 main commands: publish and fetch
            if command[0] == 'publish':
                if (len(command) != 3):
                    print("Invalid command")
                    break
                self.uploadFile(command[1], command[2])
            elif command[0] == 'fetch':
                if (len(command) != 2):
                    print("Invalid command")
                    continue
                self.fetchFile(command[1])


if __name__ == "__main__":
    myclient = client('Khang')
    
    ping_thread2 = Thread(target=myclient.createConnection("192.168.1.5", 1233))
    ping_thread1 = Thread(target=myclient.commandLoop())

    threads = [ping_thread1, ping_thread2]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
    myclient.closeConnection()
    