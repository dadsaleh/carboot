# A general set of functions and constants that provide information and system control
import binascii
import os
import sys

import esp32

LINUX = 0
ESP32 = 1
CPYTHON = 2
MICROPYTHON = 3
UNKOWN = -1

# Panic Lock for esp32 panic function
PANIC_LOCK_KEY = "locked"

# NVS Namespace
_NVS_NS = "cb_syscntl"


# NVS Error Class
class NVSError(Exception):
    pass


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
    elif impl == "micropython":
        return MICROPYTHON
    else:
        return UNKOWN


"""
    Reset and deepsleep for a very long time, this should be used in cases where no function code shall run
"""


def panic_locking_esp32():
    pass


def _write_panic_marker_esp32_to_nvs() -> bool:
    name = f"{PANIC_LOCK_KEY}_{(b := binascii.hexlify(os.urandom(8)).decode())}"
    try:
        nvs = get_or_init_nvs_ns_esp32()
        nvs.set_i32(PANIC_LOCK_KEY, int(b))  # Set panic lock get here
        return True  # Good if here
    except NVSError:
        try:
            with open(name, "w") as f:
                f.write(PANIC_LOCK_KEY)
                return True  # Good if here
        except Exception:  # noqa
            return False  # Return false if all is lost ):


"""
    Returns nvs for system contol region files
"""


def get_or_init_nvs_ns_esp32():
    try:
        nvs = esp32.NVS(_NVS_NS)
    except OSError as err:
        # Rare Case if this fails for whatever reason, return none let caller handle this
        raise NVSError(err)
    return nvs
