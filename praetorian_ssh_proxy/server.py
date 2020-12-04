import logging
import threading
import paramiko

from praetorian_api_client.api_client import ApiClient
from praetorian_api_client.errors import ApiException


class Server(paramiko.ServerInterface):
    def __init__(self, application, session):
        self.event = threading.Event()
        self._application = application
        self._session = session
        self._is_authenticated = False

        self._logged_user = None
        self._password = None

    @property
    def logged_user(self):
        return self._logged_user

    @property
    def is_authenticated(self):
        return self._is_authenticated

    def wait_to_auth(self):
        while True:
            if self._is_authenticated:
                break

    def _check_user(self, user, password, remote_name: str = None) -> bool:
        self._logged_user = user
        self._password = password
        result = True

        # TEMPORARY USER AUTH
        if user.is_temporary:
            remote_id = user.additional_data.get('remote_id')

            if remote_name:
                logging.getLogger('paramiko').error("Temporary user can't specify remote machine.")
                result = False
            else:
                try:
                    self._application.remote = self._application.api_client.remote.get(remote_id=remote_id)
                except ApiException as e:
                    logging.getLogger('paramiko').error(e.message)
                    result = False

        # BASIC USER AUTH
        else:
            if remote_name:
                try:
                    self._application.remote = self._application.api_client.remote.list(name=remote_name)[0]
                except ApiException as e:
                    logging.getLogger('paramiko').error(e.message)
                    result = False
            else:
                self._application.remote = self._application.api_client.remote.list()

        return result

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return "password,publickey"

    def check_auth_password(self, username, password):
        remote_name = None
        result = paramiko.AUTH_FAILED

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
            return paramiko.AUTH_FAILED
        try:
            user = self._application.api_client.user.get_me()
        except ApiException as e:
            logging.getLogger('paramiko').error(e.message)
            return paramiko.AUTH_FAILED

        if self._check_user(user, password, remote_name):
            result = paramiko.AUTH_SUCCESSFUL
            self._is_authenticated = True

        return result

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        ssh_stdin, ssh_stdout, ssh_stderr = self._application.ssh_client.exec_command(command)

        # TODO: Handle how to return response from exec_request

        stdout_value = (ssh_stdout.read() + ssh_stderr.read()).decode().replace('\n', '\r\n')
        channel.send(stdout_value)
        channel.event.set()
        channel.send_exit_status(0)
        return True

    def check_channel_env_request(self, channel, name, value):
        return True
