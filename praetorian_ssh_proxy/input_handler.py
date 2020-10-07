class InputHandler(object):
    def __init__(self, client, channel):
        self._client = client
        self._channel = channel
        self._buffer = ''

    @staticmethod
    def create_from_channel(client, channel) -> 'InputHandler':
        return InputHandler(client, channel)

    def prepare_input(self):
        while True:
            data = self._channel.recv(1024)

            if not data:
                continue

            # BACKSPACE
            if data == b'\x7f':
                self._buffer = self._buffer[:-1]
                self._channel.send('\b \b')

            # EXIT (CTRL+C)
            elif data == b'\x03':
                self._client.close()

            # ENTER
            elif data == b'\r':
                return self._buffer
            else:
                self._channel.send(data)
                self._buffer += data.decode()

    def check_input(self):
        pass
