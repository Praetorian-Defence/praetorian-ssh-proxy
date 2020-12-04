import os
import threading

import paramiko
from paramiko import AutoAddPolicy
from praetorian_api_client.errors import ApiException

from praetorian_ssh_proxy.errors import SshException
from praetorian_ssh_proxy.hanlers.interactive_handler import InteractiveHandler
from praetorian_ssh_proxy.hanlers.menu_handler import MenuHandler
from praetorian_ssh_proxy.server import Server


class ConnectionHandler(threading.Thread):
    def __init__(self, application):
        threading.Thread.__init__(self)
        self._application = application

    def _create_ssh_session(self):
        try:
            session = paramiko.Transport(self._application.user_client)
            session.add_server_key(self._application.keyfile)
            paramiko.util.log_to_file(os.path.join(self._application.LOG_DIR, 'filename.log'))
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
            ssh_service = self._application.api_client.service.list(
                remote_id=remote.id, service_type='ssh'
            )[0]
        except ApiException as e:
            raise SshException(client=self._application.user_client, message=e.message)

        try:
            self._application.ssh_client = paramiko.SSHClient()
            self._application.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            self._application.ssh_client.connect(
                hostname=ssh_service.variables.get('host'),
                port=ssh_service.variables.get('port'),
                username=ssh_service.variables.get('user'),
                password=ssh_service.variables.get('password')
            )
        except Exception as e:
            raise SshException(client=self._application.user_client, message=str(e))

    def run(self):
        session = self._create_ssh_session()
        server = self._create_ssh_server(session)
        server.wait_to_auth()

        if server.logged_user.is_temporary:
            self._connect_to_remote(self._application.remote)
            self._application.channel = session.accept(timeout=3000)

        else:
            self._application.channel = session.accept(timeout=3000)

            remote = MenuHandler.create_from_channel(
                client=self._application.user_client,
                client_channel=self._application.channel
            ).serve_remote_menu(self._application.remote)

            self._connect_to_remote(remote)
            self._application.channel.send('Successfully connected to Praetorian SSH Proxy Server.\r\n\r\n')

            InteractiveHandler.create_from_channel(
                client=self._application.user_client,
                ssh_client=self._application.ssh_client,
                channel=self._application.channel
            ).serve_session()
