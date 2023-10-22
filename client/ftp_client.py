from ftplib import FTP

# Connect to the FTP server
ftp = FTP()
ftp.connect("127.0.0.1", 21)
ftp.login("username", "password")

# List the contents of the remote directory
ftp.retrlines("LIST")

# Upload a file to the FTP server
with open("local_file.txt", "rb") as f:
    ftp.storbinary("STOR remote_file.txt", f)

# Download a file from the FTP server
with open("downloaded_file.txt", "wb") as f:
    ftp.retrbinary("RETR remote_file.txt", f.write)

# Close the FTP connection
ftp.quit()
