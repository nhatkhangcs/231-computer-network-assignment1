# File Sharing Application README

## Objective
Build a simple file-sharing application using the TCP/IP protocol stack with application protocols defined by each group.

## Application Description

### Centralized Server
- The centralized server keeps track of connected clients and the files they store.
- Clients inform the server about their local files without transmitting file data.

### Client Functionality
- Clients request files not in their repository from the server.
- The server identifies clients storing the requested file and sends their identities to the requesting client.
- The requesting client selects a source node, and the file is directly fetched without server intervention.
- Client code is multithreaded to support multiple simultaneous file downloads.

### Client Command-Shell Interpreter
- Clients have a simple command-shell interpreter with two commands:
  1. `publish lname fname`: Adds a local file (`lname`) to the client's repository with the name `fname`. This information is conveyed to the server.
  2. `fetch fname`: Requests a copy of the target file from other clients and adds it to the local repository.

### Server Command-Shell Interpreter
- The server has a command-shell interpreter with two commands:
  1. `discover hostname`: Discovers the list of local files of the host named `hostname`.
  2. `ping hostname`: Live-checks the host named `hostname`.

## Getting Started

### Prerequisites
- Make sure you have Python installed on your system.

### Running the Application
1. Clone the repository.
   ```bash
   git clone https://github.com/nhatkhangcs/231-computer-network-assignment1.git
   ```

2. Navigate to the project directory.
   ```bash
   cd 231-computer-network-assignment1
   ```

3. Run the server in folder ```server```.
   ```bash
   python server.py
   ```

4. Run the server in folder ```client```
    ```bash
    python client.py
    ```

**NOTE**: If you want to test for multiple clients, navigate to folder ```test_client```. Here you can see list of ```client<x>``` folders with same structure as the ```client``` folder. The operation will be the same as above.

# Contributing
If you'd like to contribute, please fork the repository and create a pull request.

# License
This project is licensed under the HCMUT license.

# Acknowledgments
Special thanks to [Group Name] for their contribution to defining the application protocols.

Feel free to modify this template to suit your project structure and requirements.