import paramiko
import sys
import getopt

from paramiko import AuthenticationException, SSHException, BadHostKeyException
from paramiko.ssh_exception import NoValidConnectionsError

from log import info, error


def usage():
    info('Usage: ssh_client.py  <IP> -p <PORT> -u <USER> -a <PASSWORD>')
    info('-p                  specify the port')
    info('-u                  specify the username')
    info('-a                  password authentication\n\n')
    info('Examples:')
    info('client.py localhost -p 22 -u buffy -a kill_vampires')


def ssh_client(host, port, username, passwd):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=passwd)
        ssh_session = client.get_transport().open_session()
    except AuthenticationException as e:
        error(f"Authentication failed, please verify your credentials: {e}")
        sys.exit()
    except BadHostKeyException as e:
        error(f"Unable to verify server's host key: {e}")
        sys.exit()
    except NoValidConnectionsError:
        error(f"Unable to connect to port {port} on {host}")
        sys.exit()
    except SSHException as e:
        error(f"Unable to establish SSH connection: {e}")
        sys.exit()

    if ssh_session.active:
        info(ssh_session.recv(1024).decode())

        while 1:
            try:
                command = input('Enter command: ')
                if command != 'exit':
                    ssh_session.send(command)
                    print(ssh_session.recv(1024).decode())
                else:
                    ssh_session.send('exit')
                    info('Exiting ...')
                    ssh_session.close()
                    sys.exit()
            except KeyboardInterrupt:
                ssh_session.close()
                sys.exit()


def main():
    if not len(sys.argv[1:]):
        usage()
        sys.exit()
    else:
        host = sys.argv[1]
        port = None
        username = None
        password = None

    try:
        arguments = getopt.getopt(sys.argv[2:], "p:u:a:", ['port', 'username', 'password'])[0]
    except getopt.GetoptError as e:
        error(str(e))
        usage()
        sys.exit()

    info(f'Initializing connection to {host}')

    # Handle the options and arguments.
    for argument in arguments:
        if argument[0] in '-p':
            port = int(argument[1])
        elif argument[0] in '-u':
            username = argument[1]
        elif argument[0] in '-a':
            password = argument[1]
        else:
            error('This option does not exist!')
            usage()
            sys.exit()

    if username:
        info(f'User set to {username}')
        if port:
            info(f'The port to be used is {port}')
        if password:
            info(f'Password length {len(password)} was submitted.')
        else:
            info('You need to specify the command to the host.')
            usage()
            sys.exit()

        # Start the client.
        ssh_client(host, port, username, password)


if __name__ == '__main__':
    main()
