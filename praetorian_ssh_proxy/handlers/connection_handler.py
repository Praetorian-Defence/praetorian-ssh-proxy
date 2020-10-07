import os
import sys
import threading
import logging

import paramiko
from paramiko import AutoAddPolicy, SSHException

from praetorian_ssh_proxy.interfaces.server_interface import Server


class ConnectionHandler(threading.Thread):
    def __init__(self, application, client, keyfile):
        threading.Thread.__init__(self)
        self._application = application
        self._client = client
        self._keyfile = keyfile

    def run(self):
        try:
            session = paramiko.Transport(self._client)
            session.add_server_key(self._keyfile)
            paramiko.util.log_to_file(os.path.join(self._application.LOG_DIR, 'filename.log'))
            server = Server(self._application)
        except Exception as e:
            logging.getLogger('paramiko').error(f'Caught exception: {str(e)}')
            sys.exit()

        try:
            session.start_server(server=server)
        except paramiko.SSHException:
            logging.getLogger('paramiko').error('SSH negotiation failed.')
            sys.exit()

        channel = session.accept(10)

        channel.send('Welcome to Praetorian SSH proxy.\r\n\r\n')
        channel.send('> ')
        buffer = ''

        while True:
            data = channel.recv(1024)

            if not data:
                continue

            # BACKSPACE
            if data == b'\x7f':
                buffer = buffer[:-1]
                channel.send('\b \b')

            # EXIT (CTRL+C)
            elif data == b'\x03':
                self._client.close()

            # ENTER
            elif data == b'\r':
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(AutoAddPolicy())
                    ssh.connect(
                        hostname=self._application.SSH_SERVER_URL,
                        username=self._application.SSH_SERVER_USERNAME,
                        password=self._application.SSH_SERVER_PASSWORD
                    )
                    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(buffer)
                    stdout_value = ssh_stdout.read() + ssh_stderr.read()
                    channel.send(stdout_value)
                    channel.send('> ')
                    buffer = ''
                except SSHException as e:
                    channel.send(str(e))
                    self._client.close()
                    sys.exit()
                except Exception as e:
                    channel.send(str(e))
                    self._client.close()
                    buffer = ''
            else:
                channel.send(data)
                buffer += data.decode()
