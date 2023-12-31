import re
import select
import sys
import time


class InteractiveHandler(object):
    def __init__(self, client, ssh_client, channel, logged_user, api_client, remote, logger):
        self._client = client
        self._ssh_client = ssh_client
        self._channel = channel
        self._logged_user = logged_user
        self._api_client = api_client
        self._remote = remote
        self._logger = logger
        self._recorded_data = []  # To store the recorded session data

    @staticmethod
    def create_from_channel(client, ssh_client, channel, logged_user, api_client, remote, logger) -> 'InteractiveHandler':
        return InteractiveHandler(client, ssh_client, channel, logged_user, api_client, remote, logger)

    @staticmethod
    def strip_ansi_codes(s):
        return s  # re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', s)

    def serve_session(self):
        command_buffer = ''
        response_buffer = ''
        expecting_echoed_command = False

        # Create an interactive shell.
        channel = self._ssh_client.invoke_shell()
        prompt_format = self._logged_user.email + ' ~]$'

        while True:
            rl, wl, xl = select.select([self._channel, channel], [], [], 0.0)

            if self._channel in rl:
                data_input = self._channel.recv(1024)

                if not data_input:
                    continue

                cleaned_data_input = self.strip_ansi_codes(data_input.decode())
                self._recorded_data.append(
                    {
                        'timestamp': time.time(),
                        'data': cleaned_data_input,
                        'type': 'input',
                        'prompt': prompt_format
                    }
                )

                self._logger.info(f"Sent command-1: {command_buffer.strip()}")
                if cleaned_data_input == '\x7f' or cleaned_data_input == '\x08':
                    command_buffer = command_buffer[:-1]
                elif cleaned_data_input not in ['\r', '\n']:
                    command_buffer += cleaned_data_input
                else:
                    command_buffer = ''
                    expecting_echoed_command = True

                channel.send(data_input)

            if channel in rl:
                response = channel.recv(4096)
                cleaned_response = self.strip_ansi_codes(response.decode())
                self._recorded_data.append(
                    {
                        'timestamp': time.time(),
                        'data': cleaned_response,
                        'type': 'output'
                    }
                )

                # Extract prompt format if possible
                match = re.search(r'\[.*@.*]\$ ', cleaned_response)
                if match:
                    prompt_format = self._get_prompt_format(cleaned_response, match)

                if expecting_echoed_command:
                    lines = cleaned_response.splitlines()
                    if lines:
                        cleaned_response = "\n".join(lines[1:])
                    expecting_echoed_command = False

                response_buffer += cleaned_response

                self._logger.info(f"Received response-1: {response_buffer.strip()}")
                if (
                    response_buffer.endswith('\r\n')
                    or response_buffer.endswith('~]$ ')
                    or response_buffer.endswith('~]$')
                ):
                    response_buffer = ''

                if not response:
                    self._channel.send(f'\n\rExiting ...\r\n')
                    self._client.close()
                    self.save_session_data()
                    sys.exit(0)

                self._channel.send(response)

    @staticmethod
    def _get_prompt_format(cleaned_response, match):
        return cleaned_response[match.start():match.end() + 2]

    def save_session_data(self):
        self._api_client.log.create(
            remote_id=self._remote.id,
            base_log=self._recorded_data
        )
