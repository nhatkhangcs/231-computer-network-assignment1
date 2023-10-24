import os, time


from pyngrok.conf import PyngrokConfig
from pyngrok import ngrok, conf

conf.get_default().config_path = r'''C:\Users\HP\AppData\Local\ngrok\ngrok.yml'''
conf.get_default().auth_token = "2UpNO9VBCWx88NTAaEyrbIJ0G1T_5ybEHpnGEf5JW6ueWARBZ"

ssh_tunnel = ngrok.connect(22, "tcp")
# <NgrokTunnel: "tcp://0.tcp.ngrok.io:12345" -> "localhost:22"> 

ngrok_process = ngrok.get_ngrok_process()

try:
    # Block until CTRL-C or some other terminating event
    ngrok_process.proc.wait()
except KeyboardInterrupt:
    print(" Shutting down server.")
    ngrok.kill()