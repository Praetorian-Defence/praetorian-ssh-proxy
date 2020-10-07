import logging
import os
import socket
import sys
from pathlib import Path

import paramiko
from dotenv import load_dotenv

from praetorian_ssh_proxy.connection_handler import ConnectionHandler


class Application(object):
    __instance__ = None

    def __init__(self):
        if Application.__instance__ is None:
            Application.__instance__ = self
        else:
            raise Exception("You cannot create another SingletonGovt class")

        self.BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
        self.ENV_FILE = os.path.join(self.BASE_DIR, '.env')
        self.LOG_DIR = os.path.join(self.BASE_DIR, 'logs')

        if os.path.exists(self.ENV_FILE):
            load_dotenv(dotenv_path=self.ENV_FILE, verbose=True)

        self.SSH_LOGGING_LEVEL = os.getenv('SSH_LOGGING_LEVEL')
        self.INTERNAL_LOGGING_LEVEL = os.getenv('INTERNAL_LOGGING_LEVEL')

        self.HOST_KEY = paramiko.RSAKey(filename=os.path.join(self.BASE_DIR, 'test_rsa.key'))
        self.LOGGING_LEVEL = 'DEBUG'
        self.BACKLOG = 100

        # TODO: Toto treba brat z Praetorian DB
        self.SSH_SERVER_URL = os.getenv('SSH_SERVER_URL')
        self.SSH_SERVER_USERNAME = os.getenv('SSH_SERVER_USERNAME')
        self.SSH_SERVER_PASSWORD = os.getenv('SSH_SERVER_PASSWORD')

        # TODO: Brať credentials z Praetorian DB
        self.CLIENT_USERNAME = os.getenv('CLIENT_USERNAME')
        self.CLIENT_PASSWORD = os.getenv('CLIENT_PASSWORD')

        paramiko_level = getattr(paramiko.common, self.SSH_LOGGING_LEVEL)
        paramiko.common.logging.basicConfig(level=paramiko_level)

    @staticmethod
    def get_instance():
        if not Application.__instance__:
            Application()
        return Application.__instance__

    def start_server(self, host, port, keyfile):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            sock.bind((host, port))
            sock.listen(self.BACKLOG)
            logging.getLogger('paramiko').info('Listening for connection ...')

            while True:
                client, addr = sock.accept()

                logging.getLogger('paramiko').info('Connection Established!')
                server_thread = ConnectionHandler(self, client, keyfile)
                server_thread.setDaemon(True)
                server_thread.start()

        except Exception as e:
            logging.getLogger('paramiko').error(f'Connection Failed: {str(e)}')
            sys.exit()
