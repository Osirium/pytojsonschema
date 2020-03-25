import sys


if sys.version_info.major != 3 or sys.version_info.minor < 8:  # pragma: no cover
    raise RuntimeError(
        f"Only Python 3.8 or higher is supported. Python {sys.version_info.major}.{sys.version_info.minor} was detected"
    )
