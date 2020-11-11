import os
import typing


def get_config() -> typing.Dict[str, str]:
    return dict(os.environ)
