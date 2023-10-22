from ftplib import FTP
import threading
import os
from icmplib import ping

class client:
    localDir = 'local\\'
    remoteDir = 'uploaded\\'
    HOME_DIR = "client\\"

    def __init__(self, ip, port):
        self.homeDir = os.getcwd() # get current working directory
        self.port = port
        self.ip = ip
        self.serverIP = None
        self.serverPort = None
        self.session = None
        self.localRepo = set() # set of files in local repo
    
    ### Methods for creating connection to server ###
    def createConnection(self, serverIP, serverPort):
        '''
            Args: serverIP, serverPort
            Returns: A message indicating if the connection was successful
        '''
        self.session =  FTP()
        self.session.connect(serverIP, serverPort) # connect to server
        username = input("Enter username: ")
        password = input("Enter password: ")
        try:
            self.session.login(user=username, passwd=password) # login to server
        except:
            print("Invalid username or password")
            return
        #create connection to server
        
        #self.threading()

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

    def closeConnection(self):
        '''
            Args: None
            Returns: A message if connection was closed successfully
        '''

        self.session.quit()
        return "Connection closed successfully"
        

    ### Methods for client to interact with server and other clients ###
    def repoInfo(self):
        '''
            Args: None
            Returns: list of files in local repo
        '''
        self.session.cwd(client.HOME_DIR + client.remoteDir)
        files = self.session.retrlines("LIST")
        return files

    def uploadFile(self, fileName, uploadName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully uploaded
        '''
        # print current working directory
        # print(self.session.pwd())
        # check path of current working directory
        #print(self.homeDir)
        
        # print files in local directory
        self.session.cwd(client.HOME_DIR + client.localDir)
        #list files in current working directory
        #print(self.session.retrlines('LIST'))   
        file = open(client.localDir + fileName, 'rb')                  # file to send
        self.session.cwd('..\\'  + client.remoteDir)               # change directory to /pub/
        self.session.storbinary(f'STOR {uploadName}', file)     # send the file
        file.close()                                    # close file and FTP
        #self.session.quit()

    def deleteFileLocal(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully deleted
        '''
        self.session.cwd(client.HOME_DIR + client.remoteDir)
        print(self.session.pwd())
        self.session.delete(fileName)

    def downloadFile(self, fileName, saveName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully downloaded
        '''
        self.session.cwd(client.HOME_DIR + client.remoteDir)

        # List files in "uploaded/"
        uploaded_files = []
        self.session.retrlines('NLST', uploaded_files.append)

        # Download files to "localFile/"
        if fileName in uploaded_files:
            #remote_path = f"uploaded/{fileName}"  # Remote path to the file in "uploaded/"
            local_path = f"local/{saveName}"    # Local path to save the file

            with open(local_path, 'wb') as local_file:
                self.session.retrbinary(f"RETR {fileName}", local_file.write)

            

if __name__ == "__main__":
    #create client object
    myclient = client("0.0.0.1", 21)
    myclient.createConnection("127.0.0.1", 21)
    print(myclient.receiveMessage())
    #uploadFileName = input("Upload file name: ")
    #saveFileName = input("Save file name: ")
    #myclient.uploadFile(fileName=uploadFileName, uploadName=saveFileName)
    #myclient.closeConnection()
    #print(client.repoInfo())
    #client.uploadFile("kitten.jpg")
    #client.deleteFile("kitten.jpg")
    myclient.repoInfo()
    #client.closeConnection()
    print(myclient.closeConnection())
    #print(client.ping("localhost"))
    #print(client.ping("google.com"))
    #print(client.ping("
