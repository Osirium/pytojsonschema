import json
import typing


def get_config() -> typing.Dict[str, str]:
    with open("config.json") as f:
        return json.loads(f.read())
