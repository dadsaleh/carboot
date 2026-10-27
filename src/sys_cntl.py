# A general set of functions and constants that provide information and system control
import sys

LINUX = 0
ESP32 = 1
CPYTHON = 2
MICROPYTHON = 3
UNKNOWN = -1


"""
    Returns an integer value for the current platform. MicroPython has no enums, so the mapping is currently:
        -1 = Unknown
        0 = linux
        1 = esp32
"""


def get_platform() -> int:
    platform = sys.platform
    if platform == "linux":
        return LINUX
    elif platform == "esp32":
        return ESP32
    else:
        return UNKNOWN


"""
    Returns an integer value for the current implementation, mapping:
    -1 = Unknown
    2 = cpython
    3 = micropython
"""


def get_impl() -> int:
    impl = sys.implementation.name
    if impl == "cpython":
        return CPYTHON
    elif impl == "micropython":
        return MICROPYTHON
    else:
        return UNKNOWN
