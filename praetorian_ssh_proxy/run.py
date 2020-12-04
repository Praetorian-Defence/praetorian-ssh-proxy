import logging
import sys

from praetorian_ssh_proxy.application import Application


def main():
    if not len(sys.argv[1:]):
        logging.error('Usage: server.py <SERVER>  <PORT>')
        sys.exit()

    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
    except ValueError:
        logging.error('Specified port must be number.')
        sys.exit()

    application = Application()
    application.listen(host, port, application.HOST_KEY)


if __name__ == '__main__':
    main()
