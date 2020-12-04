import sys

from praetorian_ssh_proxy.errors import SshException


class InteractiveHandler(object):
    def __init__(self, client, ssh_client, channel):
        self._client = client
        self._ssh_client = ssh_client
        self._channel = channel

    @staticmethod
    def create_from_channel(client, ssh_client, channel) -> 'InteractiveHandler':
        return InteractiveHandler(client, ssh_client, channel)

    def serve_session(self):
        self._channel.send('> ')

        while True:
            data_input = self._prepare_input()

            if data_input:
                self._send_output(data_input)

    def _prepare_input(self):
        buffer = ''

        while True:
            actual_data = self._channel.recv(1024)

            if not actual_data:
                continue

            # BACKSPACE
            if actual_data == b'\x7f':
                buffer = buffer[:-1]
                self._channel.send('\b \b')

            # EXIT (CTRL+C)
            elif actual_data == b'\x03':
                self._channel.send(f'\n\rExiting ...\r\n')
                self._client.close()
                sys.exit(0)

            # ENTER
            elif actual_data == b'\r':
                if buffer == 'exit':
                    self._channel.send(f'\n\rExiting ...\r\n')
                    self._client.close()
                    sys.exit(0)
                else:
                    return buffer
            else:
                self._channel.send(actual_data)
                buffer += actual_data.decode()

    def _send_output(self, input_data):
        try:
            ssh_stdin, ssh_stdout, ssh_stderr = self._ssh_client.exec_command(input_data)
            stdout_value = (ssh_stdout.read() + ssh_stderr.read()).decode().replace('\n', '\r\n')
            self._channel.send('\r\n' + stdout_value + '\r\n')
            self._channel.send('> ')
        except Exception as e:
            raise SshException(client=self._client, channel=self._channel, message=str(e))
