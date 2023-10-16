import socket
import threading

class client:
    def __init__(self, ip, port):
        self.port = port
        self.ip = ip
        self.serverIP = None
        self.serverPort = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.localRepo = set() # set of files in local repo
    
    ### Methods for creating connection to server ###
    def createConnection(self, serverIP, serverPort):
        '''
            Args: serverIP, serverPort
            Returns: A message indicating if the connection was successful
        '''

        #self.serverIP = serverIP
        self.serverPort = serverPort
        
        #create connection to server
        self.socket.connect((socket.gethostname(), self.serverPort))
        #self.threading()

    def threading(self):
        '''
            Args: None
            Returns: None
        '''
        self.thread = threading.Thread(target=self.receive)
        self.thread.start()

    def connectionValidation(self):
        '''
            Args: None
            Returns: "True" if server accepted connection
        '''
        pass

    def receiveMessage(self, message):
        '''
            Args: None
            Returns: Message from server
        '''
        pass

    def sendFile(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully sent
        '''
        pass

    def closeConnection(self):
        '''
            Args: None
            Returns: "True" if connection was closed successfully
        '''
        self.socket.close()

    ### Methods for client to interact with server and other clients ###
    def repoInfo(self):
        '''
            Args: None
            Returns: list of files in local repo
        '''
        pass

    def uploadFile(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully uploaded
        '''
        pass

    def deleteFile(self, fileName):
        '''
            Args: fileName
            Returns: A message indicating if the file was successfully deleted
        '''
        pass

    def receiveFile(self):
        '''
            Args: None
            Returns: A message indicating if the file was successfully received
        '''
        pass

    ### Debugging methods ###
    def sendServerMessage(self, message):
        '''
            Args: message
            Returns: A message indicating if the message was successfully sent
        '''
        self.socket.sendall(bytes(message, encoding="utf-8"))

    def receiveServerMessage(self):
        '''
            Args: None
            Returns: A message indicating if the message was successfully received
        '''
        # serversocket, addr = self.socket.recv(9999)
        # print("Got an answer back from %s" % str(addr))
        while True:
            msg = self.socket.recv(1024)
            decoded = msg.decode("ascii")
            print(decoded)
            if decoded == "Thank you for connecting\r\n":
                break
            


if __name__ == "__main__":
    client = client("0.0.0.1", 1000)
    client.createConnection("0.0.0.0", 9999)
    client.sendServerMessage("Hello\r\n")
    client.receiveServerMessage()
    #client.closeConnection()
