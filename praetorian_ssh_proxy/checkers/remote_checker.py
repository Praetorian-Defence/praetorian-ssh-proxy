import logging

import paramiko
from praetorian_api_client.api_client import ApiClient
from praetorian_api_client.errors import ApiException
from praetorian_api_client.resources.remote import RemoteResource
from praetorian_api_client.resources.user import UserResource


class RemoteChecker(object):
    def __init__(self, api_client: ApiClient):
        self._api_client = api_client
        self._remote = None
        self._remote_set = False

    @property
    def is_remote_set(self) -> bool:
        return self._remote_set

    @property
    def remote(self) -> RemoteResource.Remote:
        return self._remote

    def set_remote(self, remote: RemoteResource.Remote):
        self._remote = remote
        self._remote_set = True

    def get_user_remote(self, user: UserResource.User, remote_name: str = None):
        if user.is_temporary:
            remote_id = user.additional_data.get('remote_id')

            self._remote = self._get_temporary_remote(remote_id, remote_name)
        else:
            self._remote = self._get_remote(remote_name)

        if isinstance(self._remote, RemoteResource.Remote):
            self._remote_set = True

    def _get_temporary_remote(self, remote_id: str = None, remote_name: str = None) -> RemoteResource.Remote:
        if remote_name:
            logging.getLogger('paramiko').error("Temporary user can't specify remote machine.")
            raise paramiko.AuthenticationException
        else:
            try:
                remote = self._api_client.remote.get(remote_id=remote_id)
            except ApiException as e:
                logging.getLogger('paramiko').error(e.message)
                raise paramiko.AuthenticationException
        return remote

    def _get_remote(self, remote_name: str = None) -> RemoteResource.Remote:
        if remote_name:
            try:
                remote = self._api_client.remote.list(name=remote_name)[0]
            except ApiException as e:
                logging.getLogger('paramiko').error(e.message)
                raise paramiko.AuthenticationException
        else:
            remote = self._api_client.remote.list()
        return remote
