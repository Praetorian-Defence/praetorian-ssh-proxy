import logging
import sys


class SshException(Exception):
    def __init__(
        self,
        message: str,
        client=None,
        channel=None,
        previous: Exception = None,
        to_log: bool = True,
    ):
        super().__init__(message)

        self._message = message
        self._previous = previous

        if channel:
            channel.send(message.encode())

        if to_log:
            logging.getLogger('paramiko').error(self.message)

        if client:
            client.close()
        sys.exit(0)

    @property
    def message(self) -> str:
        return self._message

    @property
    def previous(self) -> Exception:
        return self._previous

    @property
    def payload(self) -> dict:
        result = {
            'message': self.message,
        }

        return result
