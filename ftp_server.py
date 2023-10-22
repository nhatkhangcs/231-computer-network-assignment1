from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

# Create an authorizer for user authentication
authorizer = DummyAuthorizer()
authorizer.add_user("username", "password", "client/files", perm="elradfmw")

# Create an FTP handler and configure the server
handler = FTPHandler
handler.authorizer = authorizer

# Create and start the FTP server
server = FTPServer(("127.0.0.1", 21), handler)
server.serve_forever()
