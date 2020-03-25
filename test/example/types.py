import typing

ServicePort = typing.Union[int, float]
ServiceConfig = typing.Dict[str, typing.Any]


class Service(typing.TypedDict):
    address: str
    port: ServicePort
    config: ServiceConfig
    tags: typing.List[str]
    debug: bool
