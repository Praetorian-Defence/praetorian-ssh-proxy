import socket
import subprocess
import sys
import threading

import paramiko

from log import error, info, success

HOST_KEY = paramiko.RSAKey(filename='test_rsa.key')
USERNAME = 'test'
PASSWORD = 'test'


class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if (username == USERNAME) and (password == PASSWORD):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED


def main():
    if not len(sys.argv[1:]):
        error('Usage: ssh_server.py <SERVER>  <PORT>')
        sys.exit()

    # Create a socket object.
    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
    except ValueError:
        error('Specified port must be number.')
        sys.exit()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(100)
        info('Listening for connection ...')
        client, addr = sock.accept()
    except Exception as e:
        error(f'Connection Failed: {str(e)}')
        sys.exit()
    success('Connection Established!')

    # Creating a paramiko object.
    try:
        session = paramiko.Transport(client)
        session.add_server_key(HOST_KEY)
        paramiko.util.log_to_file('filename.log')
        server = Server()

        try:
            session.start_server(server=server)
        except paramiko.SSHException:
            error('SSH negotiation failed.')
            sys.exit()

        channel = session.accept(10)
        success('Authenticated!')
        channel.send("Welcome to Praetorian SSH proxy.")

        while 1:
            command = channel.recv(1024).decode()

            try:
                cmd_output = subprocess.check_output(command, shell=True)
                channel.send(cmd_output)
            except Exception as e:
                channel.send(error(str(e)))
                client.close()

    except Exception as e:
        error(f'Caught exception: {str(e)}')
        sys.exit()


if __name__ == '__main__':
    main()
