import logging

import paramiko
from praetorian_api_client.api_client import ApiClient
from praetorian_api_client.errors import ApiException
from praetorian_api_client.resources.service import ServiceResource
from praetorian_api_client.resources.user import UserResource


class ServiceChecker(object):
    def __init__(self, api_client: ApiClient):
        self._api_client = api_client
        self._service = None
        self._service_set = False

    @property
    def is_service_set(self) -> bool:
        return self._service_set

    @property
    def service(self) -> ServiceResource.Service:
        return self._service

    def set_service(self, service: ServiceResource.Service):
        self._service = service
        self._service_set = True

    def get_user_service(self, user: UserResource.User) -> ServiceResource.Service:
        if user.is_temporary:
            service_id = user.additional_data.get('service_id')

            try:
                self._service = self._api_client.service.get(service_id=service_id)
            except ApiException as e:
                logging.getLogger('paramiko').error(e.message)
                raise paramiko.AuthenticationException
        else:
            self._service = None

        return self._service
