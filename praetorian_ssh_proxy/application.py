import logging
import os
import socket
from pathlib import Path

import paramiko
from dotenv import load_dotenv
from praetorian_api_client.configuration import Environment, Configuration

from praetorian_ssh_proxy.handlers.connection_handler import ConnectionHandler
from praetorian_ssh_proxy.errors import SshException


class Application(object):
    __instance__ = None

    def __init__(self):
        if Application.__instance__ is None:
            Application.__instance__ = self
        else:
            raise Exception("You cannot create another SingletonGovt class")

        self.logged_user = None

        self.api_client = None
        self.ssh_client_connected = False
        self.ssh_client = None
        self.user_client = None

        self.user_ip_address = None
        self.keyfile = None
        self.channel = None

        self.remote_checker = None

        self.BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
        self.ENV_FILE = os.path.join(self.BASE_DIR, '.env')
        self.LOG_DIR = os.path.join(self.BASE_DIR, 'logs')

        if os.path.exists(self.ENV_FILE):
            load_dotenv(dotenv_path=self.ENV_FILE, verbose=True)

        self.FILE_LOGGING_LEVEL = os.getenv('FILE_LOGGING_LEVEL', 'INFO')
        self.CONSOLE_LOGGING_LEVEL = os.getenv('CONSOLE_LOGGING_LEVEL', 'INFO')

        self.HOST_KEY = paramiko.RSAKey(filename=os.path.join(self.BASE_DIR, 'test_rsa.key'))
        self.BACKLOG = 100

        self.environment = Environment(name='praetorian-api', api_url=os.getenv('PRAETORIAN_API_URL'), read_only=False)
        self.configuration = Configuration(
            environment=self.environment, key=os.getenv('PRAETORIAN_API_KEY'), secret=os.getenv('PRAETORIAN_API_SECRET')
        )

        self._set_logging()

    @staticmethod
    def get_instance():
        if not Application.__instance__:
            Application()
        return Application.__instance__

    def listen(self, host, port, keyfile):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            sock.bind((host, port))
            sock.listen(self.BACKLOG)

            logging.getLogger('paramiko').info('Listening for connection ...')

            while True:
                user_client, addr = sock.accept()
                self.user_client = user_client
                self.keyfile = keyfile
                self.user_ip_address = str(sock.getsockname()[0])

                logging.getLogger('paramiko').info('Connection Established!')

                server_thread = ConnectionHandler(self)
                server_thread.setDaemon(True)
                server_thread.start()

        except Exception as e:
            raise SshException(message=f'Connection Failed: {str(e)}')

    def _set_logging(self):
        paramiko_logger = logging.getLogger("paramiko")
        paramiko_logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.CONSOLE_LOGGING_LEVEL)

        file_handler = logging.FileHandler(self.LOG_DIR + '\\internal.log')
        file_handler.setLevel(self.FILE_LOGGING_LEVEL)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        paramiko_logger.addHandler(console_handler)
        paramiko_logger.addHandler(file_handler)
