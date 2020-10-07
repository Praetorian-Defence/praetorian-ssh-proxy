import sys

from paramiko import SSHException


class OutputHandler(object):
    def __init__(self, client, ssh_client, channel, output):
        self._client = client
        self._ssh_client = ssh_client
        self._channel = channel
        self._output = output

    @staticmethod
    def create_from_channel(client, ssh_client, channel, output) -> 'OutputHandler':
        return OutputHandler(client, ssh_client, channel, output)

    def send_output(self):
        try:
            ssh_stdin, ssh_stdout, ssh_stderr = self._ssh_client.exec_command(self._output)
            stdout_value = (ssh_stdout.read() + ssh_stderr.read()).decode().replace('\n', '\r\n')
            self._channel.send('\r\n' + stdout_value + '\r\n')
            self._channel.send('> ')
        except SSHException as e:
            self._channel.send(str(e))
            self._client.close()
            sys.exit()
        except Exception as e:
            self._channel.send(str(e))
            self._client.close()
