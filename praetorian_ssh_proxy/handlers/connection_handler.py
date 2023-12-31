import logging
import threading

import paramiko
from paramiko import AutoAddPolicy
import paramiko.util
from praetorian_ssh_proxy.errors import SshException
from praetorian_ssh_proxy.handlers.interactive_handler import InteractiveHandler
from praetorian_ssh_proxy.handlers.menu_handler import MenuHandler
from praetorian_ssh_proxy.server import Server

# TODO: Can be remove also from interactive_handler
logging.basicConfig(
    filename='session_logs.log',
    level=logging.INFO,
    format='%(asctime)s:%(name)s:%(levelname)s:%(module)s: %(message)s',
)
logger = logging.getLogger('SSHSession')


class ConnectionHandler(threading.Thread):
    def __init__(self, application):
        threading.Thread.__init__(self)
        self._application = application

    def _create_ssh_session(self):
        try:
            session = paramiko.Transport(self._application.user_client)
            session.add_server_key(self._application.keyfile)
        except Exception as e:
            raise SshException(client=self._application.user_client, message=f'Caught exception: {str(e)}')
        return session

    def _create_ssh_server(self, session):
        server = Server(self._application, session)

        try:
            session.start_server(server=server)
        except paramiko.SSHException:
            raise SshException(client=self._application.user_client, message='SSH negotiation failed.')

        return server

    def _connect_to_remote(self, remote):
        try:
            self._application.ssh_client = paramiko.SSHClient()
            self._application.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            self._application.ssh_client.connect(
                hostname=remote.host,
                port=remote.port,
                username=remote.user,
                password=remote.password
            )
        except Exception as e:
            raise SshException(client=self._application.user_client, message=str(e))
        self._application.ssh_client_connected = True

    def run(self):
        session = self._create_ssh_session()
        server = self._create_ssh_server(session)
        server.wait_to_auth()

        if self._application.logged_user.is_temporary:
            self._connect_to_remote(self._application.remote_checker.remote)
            self._application.channel = session.accept(timeout=3000)

        else:
            self._application.channel = session.accept(timeout=3000)

            MenuHandler.create_from_channel(
                client=self._application.user_client,
                client_channel=self._application.channel,
                remote_checker=self._application.remote_checker
            ).serve_remote_menu()

            self._connect_to_remote(self._application.remote_checker.remote)
            self._application.channel.send(b'Successfully connected to Praetorian SSH Proxy Server.\r\n\r\n')

            InteractiveHandler.create_from_channel(
                client=self._application.user_client,
                ssh_client=self._application.ssh_client,
                channel=self._application.channel,
                logged_user=self._application.logged_user,
                api_client=self._application.api_client,
                remote=self._application.remote_checker.remote,
                logger=logger
            ).serve_session()
