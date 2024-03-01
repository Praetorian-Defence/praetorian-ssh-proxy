import logging
import re
import threading
import time
from typing import Union

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
        self._recorded_data = []  # To store the recorded session data from noninteractive user
        self._exit_session = False

    @property
    def is_authenticated(self):
        return self._is_authenticated

    def wait_to_auth(self):
        while True:
            if self._is_authenticated:
                break

    def wait_to_shh_connect(self):
        while True:
            if self._application.ssh_client_connected:
                break

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return "password,publickey"

    def check_auth_password(self, username, password):
        result = paramiko.AUTH_SUCCESSFUL
        project_name = None
        remote_name = None
        user = None

        if '+' in username:
            username, remote_project_name = username.split('+')

            if '-' in remote_project_name:
                project_name, remote_name = remote_project_name.split('-')
            else:
                remote_name = remote_project_name

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
            remote_checker.get_user_remote(
                user=user,
                remote_name=remote_name,
                project_name=project_name
            )
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

    def _process_variables(self, command: Union[bytes, str]) -> bytes:
        variable_expression = '\{\{\s*(.*?)\s*\}\}'

        if isinstance(command, bytes):
            decoded_command = command.decode('utf-8')
        else:
            decoded_command = command

        logging.getLogger('paramiko').info(f'DECODED COMMAND: {decoded_command}')

        self._recorded_data.append(
            {
                'timestamp': time.time(),
                'data': decoded_command + '\n',
                'type': 'input',
            }
        )

        if decoded_command == 'exit':
            self._exit_session = True

        variables = re.findall(variable_expression, decoded_command)
        available_variables = self._application.remote_checker.remote.variables

        for variable in variables:
            if '.' in variable:
                nested_variables = variable.split('.')
                temp_variables = available_variables

                for nested_variable in nested_variables:
                    if temp_variables:
                        temp_variables = temp_variables.get(nested_variable)
                    else:
                        break

                value = temp_variables
            else:
                value = available_variables.get(variable)

            if value:
                decoded_command = re.sub(f'{{{{ {variable} }}}}', value, decoded_command)

        logging.getLogger('paramiko').info(f'PROCESSED COMMAND: {decoded_command}')

        if isinstance(decoded_command, str):
            encoded_command = decoded_command.encode()
        else:
            encoded_command = decoded_command

        logging.getLogger('paramiko').info(f'ENCODED COMMAND: {encoded_command}\n')

        return encoded_command

    def check_channel_exec_request(self, channel, command):
        command = self._process_variables(command)
        self.wait_to_shh_connect()

        ssh_stdin, ssh_stdout, ssh_stderr = self._application.ssh_client.exec_command(command)

        channel_stdin = channel.makefile_stdin('wb')
        channel_stderr = channel.makefile_stderr('wb')

        ssh_stdout =  ssh_stdout.read()
        ssh_stderr = ssh_stderr.read()

        channel_stdin.write(ssh_stdout)
        channel_stderr.write(ssh_stderr)

        if len(ssh_stdout) != 0:
            self._recorded_data.append(
                {
                    'timestamp': time.time(),
                    'data': ssh_stdout.decode(),
                    'type': 'output',
                }
            )
        if len(ssh_stderr) != 0:
            self._recorded_data.append(
                {
                    'timestamp': time.time(),
                    'data': ssh_stderr.decode(),
                    'type': 'output',
                }
            )

        channel.event.set()
        channel.send_exit_status(0)

        if self._exit_session:
            self._application.ssh_client.close()
            self._application.api_client.log.create(
                remote_id=self._application.remote_checker.remote.id,
                base_log=self._recorded_data,
            )
            self._application.api_client.user.delete_me()

        return True

    def check_channel_env_request(self, channel, name, value):
        return True
