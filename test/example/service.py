import typing
from .types import Service


def start(service: Service) -> typing.NoReturn:
    print(f"Service listening on {service.address}:{service.port}")


def _secret(secret: typing.Optional[str] = None):
    print(f"Psshh ... {secret if secret else ''}")
