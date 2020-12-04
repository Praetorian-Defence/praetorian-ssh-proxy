import sys


class MenuHandler(object):
    def __init__(self, client, client_channel):
        self._client = client
        self._client_channel = client_channel
        self._buffer = ''

    @staticmethod
    def create_from_channel(client, client_channel) -> 'MenuHandler':
        return MenuHandler(client, client_channel)

    def serve_remote_menu(self, remotes):
        if isinstance(remotes, list):
            self._client_channel.send('------------------------------------\r\n')
            self._client_channel.send('| Welcome to Praetorian SSH proxy  |\r\n')
            self._client_channel.send('------------------------------------\r\n')
            for counter, remote in enumerate(remotes, 1):
                self._client_channel.send('| {:30} {} |\r\n'.format(remote.name, counter))

            self._client_channel.send('------------------------------------\r\n')
            self._client_channel.send('| {:30} {} |\r\n'.format('exit', len(remotes) + 1))
            self._client_channel.send('------------------------------------\r\n')
            self._client_channel.send('Choose your remote: ')

            while True:
                data = self._client_channel.recv(1024)

                if not data:
                    continue

                # BACKSPACE
                if data == b'\x7f':
                    self._buffer = self._buffer[:-1]
                    self._client_channel.send('\b \b')

                # EXIT (CTRL+C)
                elif data == b'\x03':
                    self._client_channel.send(f'\n\rExiting ...\r\n')
                    self._client.close()
                    sys.exit(0)

                # ENTER
                elif data == b'\r':
                    if self._buffer in map(str, range(1, len(remotes) + 1)):
                        remote = remotes[int(self._buffer) - 1]
                        self._client_channel.send(f'\n\rChosen remote {remote.name}.\r\n')
                        return remote

                    elif self._buffer == str(len(remotes) + 1):
                        self._client_channel.send(f'\n\rExiting ...\r\n')
                        self._client.close()
                        sys.exit(0)
                    else:
                        self._client_channel.send('\n\rWrong option.\r\n')
                        self._client_channel.send('Choose your option: ')
                    self._buffer = ''
                else:
                    self._client_channel.send(data)
                    self._buffer += data.decode()
