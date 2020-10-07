import os
import sys
import threading
import logging

import paramiko
from paramiko import AutoAddPolicy

from praetorian_ssh_proxy.input_handler import InputHandler
from praetorian_ssh_proxy.output_handler import OutputHandler
from praetorian_ssh_proxy.server import Server


class ConnectionHandler(threading.Thread):
    def __init__(self, application, client, keyfile):
        threading.Thread.__init__(self)
        self._application = application
        self._client = client
        self._keyfile = keyfile

    def _create_ssh_client(self, channel):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            ssh_client.connect(
                hostname=self._application.SSH_SERVER_URL,
                username=self._application.SSH_SERVER_USERNAME,
                password=self._application.SSH_SERVER_PASSWORD
            )
        except Exception as e:
            channel.send(str(e))
            self._client.close()
            sys.exit()
        return ssh_client

    def _create_channel(self):
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

        return channel

    def run(self):
        channel = self._create_channel()
        ssh_client = self._create_ssh_client(channel)

        while True:
            client_data = InputHandler.create_from_channel(self._client, channel).prepare_input()

            if client_data:
                OutputHandler.create_from_channel(self._client, ssh_client, channel, client_data).send_output()
