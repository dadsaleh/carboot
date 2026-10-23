# A general set of functions and constants that provide information and system control
import sys

LINUX = 0
ESP32 = 1
CPYTHON = 2
MICROPYTHON = 3
UNKOWN = -1

"""
    Returns a integer value of the current platform, because enums are not possible on micropython/esp32 boards, the mappings is *currently* as follows:
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
        return UNKOWN


"""
    Returns a integer value of the current implementation, mapping:
    -1 = Unknown
    2 = cpython
    3 = micropython
"""
def get_impl() -> int:
    impl = sys.implementation.name
    if impl == "cpython":
        return CPYTHON
    elif impl == "micropython"
        return MICROPYTHON
    else:
        return UNKOWN

"""
    Reset and deepsleep for a very long time, this should be used in cases where no function code shall run
"""
# TODO: Wire in a atomic file lock marker, so on reset we can read the sleep value stored here, and abide by it
def panic_esp32():
    pass

def _write_panic_marker_esp32():
    


