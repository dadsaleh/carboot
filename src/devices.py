"""Device classes for the hardware abstraction layer (HAL)"""

import re

from machine import Pin
from micropython import const

from lib.ic2.ic2_device_identification import I2CDeviceIdentifier

# General Errors
EBADDEVICENAME = const(1)
EBADDEVICEID = const(2)
EDEVICENOTOK = const(3)
EBADDEVICEIOMODE = const(4)
EBADDEVICEPIN = const(5)
EDEVICEPANICKING = const(6)

ESP32_SUM_GPIO_PINS = 32
ESP32_MIN_GPIO_PINS = 0

"""
    IMPORTANT: ESP32_USABLE_GPIO* list the usable GPIO pins. Selecting a pin outside these lists for any device fails device init.
    - Multiple devices may use the same pin, and devices with no pin (None) are allowed. The caller is expected to know what they are doing.
"""

ESP32_USABLE_GPIO_INPUT_PINS = [34, 35, 36, 39]  # Input only, cannot read
ESP32_USABLE_GPIO_INPUT_OUTPUT_PINS = [
    4,
    13,
    16,
    17,
    18,
    19,
    21,
    22,
    23,
    25,
    26,
    27,
    32,
    33,
]  # General pins you can read and write to

# WARNING: USE WITH CARE. Flash pins are read at boot, which decide how the chip will boot:
# 0 -> Held low puts it in its bootloader mode
# 2 -> must be low for floating to flash
# 12 -> held high sets the flash to 1.8V, and the board WILL NOT boot
# 5, 14, 15 also output a signal during boot
# 1 and 3 are UART0
# Avoid these pins. A device cannot be created on them
ESP32_RESERVED_FLASH_PINS = [0, 2, 5, 12, 15]


"""
    Dict of valid devices that have already been registered, keyed by both id and name.
    Note that these do NOT contain BaseDevices, only GPIODevice or I2CDevice
"""
_UNKNOWN_NAME_MARKER = "[UNKNOWN]"
RESERVED_ID = (1, 0)  # Unused for now, reserved for later

DEVICES_ID = {}
DEVICES_NAME = {}


class Registrable:
    def register(self):
        raise NotImplementedError


class BaseDeviceStatusError(Exception):
    def __init__(self, errno, msg):
        super().__init__(self, errno, msg)
        self.errno = errno


"""
    BaseDeviceStatus holds a device's status. The initial state matters: if the device is not ok, or is panicking, a BaseDevice
    cannot be created for it.
"""


class BaseDeviceStatus:
    def __init__(
        self,
        *,
        is_ok: bool,
        is_ready: bool,
        is_panicking: bool,
        read: bool,
        write: bool,
        noio: bool,
    ):
        self.is_ok = is_ok
        self.is_ready = is_ready
        self.is_panicking = is_panicking
        self.noio = noio
        self.read = read
        self.write = write

        if self.noio or (
            self.read or self.write
        ):  # Must have no mode or at least one mode
            self.read = read
            self.write = write
        else:
            raise BaseDeviceStatusError(
                EBADDEVICEIOMODE,
                "error=expected at least one of: read, write, noio, got none",
            )
        # Add more as required

    def __str__(self) -> str:
        return f" \
        is_ok={self.is_ok}, \
        is_ready={self.is_ready}, \
        is_panicking={self.is_panicking}, \
        read={self.read}, \
        write={self.write}, \
        noio={self.noio} \
        "


"""
    Initial implementation of a basic device
"""


class BaseDeviceError(Exception):
    def __init__(self, errno, msg):
        super().__init__(msg)
        self.errno = errno


# NOTE: IDs and names may be stored in registers or accessed often, so keep them small for best performance
ALLOWED_IDENT_SIZE = 16
REGEX_NAME = """[^A-Z"]"""  # Must contain no special chars


class BaseDevice:
    def __init__(
        self,
        driver,
        initial_state: BaseDeviceStatus,
        *,
        name: str = _UNKNOWN_NAME_MARKER,
        id: int,
        pin: int | None,  # None is allowed for special device cases
    ):  # Name must be at most 16 bits, all caps, and contain no special chars
        name = name.upper()

        if not isinstance(id, int):
            raise BaseDeviceError(
                EBADDEVICEID, f"error=device id must be an int, got {type(id)}"
            )

        if (_ := len(name.encode()) * 8) > ALLOWED_IDENT_SIZE or (
            re.search(REGEX_NAME, name)
        ) != None:
            raise BaseDeviceError(EBADDEVICENAME, "error=bad device name")
        elif (_ := (len(bin(id))) - 2) > ALLOWED_IDENT_SIZE or id == RESERVED_ID:
            raise BaseDeviceError(EBADDEVICEID, "error=bad device id")
        elif (not initial_state.is_ok) or initial_state.is_panicking:
            if initial_state.is_panicking:
                raise BaseDeviceError(
                    EDEVICEPANICKING, "error=device is panicking, cannot init."
                )
            raise BaseDeviceError(
                EDEVICENOTOK,
                "error=device is in a bad state",
            )
        if pin != None and not ESP32_SUM_GPIO_PINS >= pin >= ESP32_MIN_GPIO_PINS:
            raise BaseDeviceError(
                EBADDEVICEPIN, f"error=device pin is out of range pin={pin}"
            )
        elif (
            pin != None
            and pin not in ESP32_USABLE_GPIO_INPUT_OUTPUT_PINS
            or not ESP32_USABLE_GPIO_INPUT_PINS
        ):
            raise BaseDeviceError(
                EBADDEVICEPIN,
                f"error=expected device pin to be in range. usable_io={ESP32_USABLE_GPIO_INPUT_OUTPUT_PINS}, usable_i={ESP32_USABLE_GPIO_INPUT_PINS}, pin={pin}",
            )
        # Statuses for pin: any IO is allowed for any general i/o pin, Read is not allowed for input
        elif initial_state.read and pin in ESP32_USABLE_GPIO_INPUT_PINS:
            raise BaseDeviceError(
                EBADDEVICEIOMODE, "error=cannot have io read on gpio input only pin"
            )
        # Device IO Contradiction, cannot have any other modes if noio
        elif initial_state.noio and (initial_state.read or initial_state.write):
            raise BaseDeviceError(
                EBADDEVICEIOMODE, "error=cannot have no io with other io modes enabled"
            )
        elif not (initial_state.noio or initial_state.read or initial_state.write):
            raise BaseDeviceError(EBADDEVICEIOMODE, "error=need at least one io mode")
        self.name = name
        self.id = id
        self.pin = Pin(pin) if pin != None else None
        if initial_state.is_ready:  # NOTE: Caller must explicitly set a device to ready regardless of its type, so this is always overridden
            initial_state.is_ready = False
        self.state = initial_state
        self.driver_object = driver  # NOTE: we cannot confirm that driver is in fact valid and working, unless specific handlers exist


"""
    I2CDevice is a usable I2C device: it wraps an address range and registers itself in the global device lists.
    Its ID must be unique, and is always the ID its BaseDevice was created with.
"""


class I2CDevice(Registrable):
    def __init__(self, device: BaseDevice, ident: I2CDeviceIdentifier):
        self.addr_range = ident.addr_range
        self.device = device
        self.ident = ident

    def register(self):
        id = self.device.id
        if id in DEVICES_ID:
            raise BaseDeviceError(
                EBADDEVICEID, f"error=device id already registered, id={id}"
            )
        DEVICES_ID[id] = self
        DEVICES_NAME.setdefault(self.ident.module_id, []).append(self)
