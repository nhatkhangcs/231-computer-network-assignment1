from ftplib import FTP
import threading
import os
from icmplib import ping
import socket


class client:
    localDir = 'local/'
    remoteDir = 'uploaded/'
    HOME_DIR = "client/"

    def __init__(self, hostname):
        self.hostname = hostname
        self.session = None
    
    ### Methods for creating connection to server ###
    def createConnection(self, serverIP, serverPort):
        '''
            Args: serverIP, serverPort
            Returns: A message indicating if the connection was successful
        '''
        self.session =  FTP()
        try:
            self.session.connect(serverIP, serverPort) # connect to server
            username = input("Enter username: ")
            password = input("Enter password: ")
            self.session.login(user=username, passwd=password) # login to server
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

        self.session.quit()
        return "Connection closed successfully"

    def threading(self):
        '''
            Args: None
            Returns: None
        '''

    def receiveMessage(self):
        '''
            Args: None
            Returns: A message indicating if the message was successfully received
        '''
        return(self.session.getwelcome())

    def sendFile(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully sent
        '''
        self.session.transfercmd('RETR ' + fileName)

    
    ### Methods for client to interact with server and other clients ###
    def repoInfo(self):
        '''
            Args: None
            Returns: list of files in local repo
        '''
        self.session.cwd(client.HOME_DIR + client.remoteDir)
        files = self.session.retrlines("LIST")
        self.session.cwd('../..')
        if not files:
            return "No files in remote repo"
        return files

    def uploadFile(self, fileName, uploadName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully uploaded
        '''
        # print current working directory
        # print(self.session.pwd())
        # check path of current working directory
        # print(self.homeDir)
        
        # print files in local directory
        #print(self.session.pwd())
        self.session.cwd(client.HOME_DIR + client.localDir)
        #print(self.session.pwd())
        #list files in current working directory
        #print(self.session.retrlines('LIST'))   
        file = open(client.localDir + fileName, 'rb')                  # file to send
        self.session.cwd('..\\'  + client.remoteDir)               # change directory to /pub/
        self.session.storbinary(f'STOR {uploadName}', file)     # send the file
        file.close()                                    # close file and FTP
        self.session.cwd('../..')
        #self.session.quit()
        return "File uploaded successfully"

    def deleteFileLocal(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully deleted
        '''
        self.session.cwd(client.HOME_DIR + client.localDir)
        #print(self.session.pwd())
        self.session.delete(fileName)
        self.session.cwd('../..')
        return "File deleted successfully"

    def deleteFileRemote(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully deleted
        '''
        self.session.cwd(client.HOME_DIR + client.remoteDir)
        try:
            #print(self.session.pwd())
            self.session.delete(fileName)
            self.session.cwd('../..')
            return "File deleted successfully"
        except:
            self.session.cwd('../..')
            return "File does not exist"

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
        # check if file exists in local repo
        if os.path.isfile(client.localDir + fileName):
            return "File already exists in local repo"
        # check if file exists in remote repo
        self.session.cwd(client.HOME_DIR + client.remoteDir)
        files = self.session.retrlines("LIST")
        self.session.cwd('../..')
        if not files or fileName not in files:
            return "File does not exist in remote repo"
        # check if file exists in other clients' repo
        # if yes, request file from other client

        # 1. Send request to server
        

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
            command = input("Enter a command: ")
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
                    break
                # self.downloadFile(command[1])

            # other commands
            elif command[0] == 'ping':
                print(self.pingServer())
            else:
                print("Invalid command")
                break

    def pingServer(self):
        '''
            Args: None
            Returns: A message indicating if the server is up or down
        '''
        try:
            #print(self.ip)
            self.receiveMessage()
            return "Server is up"
        except:
            return "Server is down"

            

if __name__ == "__main__":
    myclient = client('Khang')
    myclient.createConnection("127.0.0.1", 21)
    print(socket.gethostname())
    myclient.commandLoop()
    myclient.closeConnection()
    