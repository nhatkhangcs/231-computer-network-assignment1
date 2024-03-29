# File-sharing application

## Objective
Build a simple file-sharing application using the TCP/IP protocol stack with application protocols defined by each group.

## Application description

### Centralized server
- The centralized server keeps track of connected clients and the files they store.
- Clients inform the server about their local files without transmitting file data.

### Client functionality
- Clients request files not in their repository from the server.
- The server identifies clients storing the requested file and sends their identities to the requesting client.
- The requesting client selects a source node, and the file is directly fetched without server intervention.
- Client code is multithreaded to support multiple simultaneous file downloads.

### Client command-shell interpreter
- Clients have a simple command-shell interpreter with two commands:
  1. `publish lname fname`: Adds a local file (`lname`) to the client's repository with the name `fname`. This information is conveyed to the server. For example, `publish test.txt file.txt`
  2. `fetch fname`: Requests a copy of the target file from other clients and adds it to the local repository. For example, `fetch file.txt`

### Server command-shell interpreter
- The server has a command-shell interpreter with two commands:
  1. `discover hostname`: Discovers the list of local files of the host named `hostname`, with `hostname` is the IP and port seperated by a whitespace. For example, `discover 192.168.1.8 50004`
  2. `ping hostname`: Live-checks the host named `hostname`. For example, `ping 192.168.1.8 50004`

## Getting started

### Prerequisites
- Make sure you have Python installed on your system.

### Running the application
1. Clone the repository.
   ```bash
   git clone https://github.com/nhatkhangcs/231-computer-network-assignment1.git
   ```

2. Navigate to the project directory.
   ```bash
   cd 231-computer-network-assignment1
   ```
3. Configure the IP and port that the server bind to and ensure that the IP and port that the client connect to matches that server IP and port, configure also the IP that the client upload socket bind to so that they can be reached from other clients for fetching files

3. Run the server in folder ```server``` in a different terminal.
   ```bash
   python server.py
   ```

4. Run the server in folder ```client``` in a different terminal.
   ```bash
   python client.py
   ```

**NOTE**: If you want to test for multiple clients, navigate to folder ```test_client```. Here you can see list of ```client<x>``` folders with same structure as the ```client``` folder. The operation will be the same as above.

**More description**: On the client terminal, you will see 3 different addresses:

- ```Sending address```: This is the address that is sending the request to the server. Server ```ping``` and ```discover``` to this address.

- ```Listening address```: This is the address that is listening requests from server.

- ```Upload address```: This is the address that is used to upload file to other clients.

If you want to use server to ping client, please ping the sending address of the client.

### Advanced commands in the application

#### Client side
1. `fetch fname1 fname2 fname3...`: Requests copies of the target files from other clients and adds them to the local repository multithreadedly.

2. ```close``` will close the client side. Server side will acknowledge the disconnection of the client.

3. ```list``` will list the client side's repository files.

#### Server side
1. ```list``` will list the currently connecting clients.

# Contributing
If you'd like to contribute, please fork the repository and create a pull request.

# License
This project is licensed under the HCMUT license.

# Acknowledgments
Special thanks to Group 6 for their contribution to defining the application protocols.

Feel free to modify this template to suit your project structure and requirements.