import logging
import threading
import time

import paramiko

from praetorian_api_client.api_client import ApiClient
from praetorian_api_client.errors import ApiException

from praetorian_ssh_proxy.checkers.remote_checker import RemoteChecker


class Server(paramiko.ServerInterface):
    def __init__(self, application, session):
        self.event = threading.Event()
        self._application = application
        self._session = session
        self._is_authenticated = False

    @property
    def is_authenticated(self):
        return self._is_authenticated

    def wait_to_auth(self):
        while True:
            if self._is_authenticated:
                break

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return "password,publickey"

    def check_auth_password(self, username, password):
        result = paramiko.AUTH_SUCCESSFUL
        remote_name = None
        user = None

        if '+' in username:
            username, remote_name = username.split('+')

        try:
            self._application.api_client = ApiClient.create_from_auth(
                configuration=self._application.configuration,
                username=username,
                password=password
            )
        except ApiException as e:
            logging.getLogger('paramiko').error(e.message)
            result = paramiko.AUTH_FAILED
        try:
            user = self._application.api_client.user.get_me()
        except ApiException as e:
            logging.getLogger('paramiko').error(e.message)
            result = paramiko.AUTH_FAILED

        remote_checker = RemoteChecker(self._application.api_client)

        try:
            remote_checker.get_user_remote(user, remote_name)
        except paramiko.AuthenticationException as e:
            logging.getLogger('paramiko').error(e)
            result = paramiko.AUTH_FAILED

        self._application.remote_checker = remote_checker
        self._application.logged_user = user

        if result == paramiko.AUTH_SUCCESSFUL:
            self._is_authenticated = True
        return result

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        time.sleep(1)
        ssh_stdin, ssh_stdout, ssh_stderr = self._application.ssh_client.exec_command(command)

        channel_stdin = channel.makefile_stdin('wb')
        channel_stderr = channel.makefile_stderr('wb')

        channel_stdin.write(ssh_stdout.read())
        channel_stderr.write(ssh_stderr.read())

        channel.event.set()
        channel.send_exit_status(0)
        return True

    def check_channel_env_request(self, channel, name, value):
        return True
