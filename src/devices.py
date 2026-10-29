"""Device classes for the hardware abstraction layer (HAL)."""

import re

from machine import Pin
from micropython import const

from lib.ic2.ic2_device_identification import I2CDeviceIdentifier

"""
    Error codes, stored in errno on every device error.
"""

EBADDEVICENAME = const(1)
EBADDEVICEID = const(2)
EDEVICENOTOK = const(3)
EBADDEVICEIOMODE = const(4)
EBADDEVICEPINOUTOFRANGE = const(5)
EDEVICEPANICKING = const(6)
EDEVICENOIOMODE = const(7)
EBADDEVICEPINTYPE = const(9)
EBADDEVICEPINNOTUSABLE = const(10)

"""
    ESP32 classic pin. Devices may only use pins from the two usable lists below.
    Flash, strapping, and controller pins are not used for now.
"""


ESP32_MAX_GPIO_PINS = 39
ESP32_MIN_GPIO_PINS = 0
ESP32_USABLE_GPIO_INPUT_PINS = [34, 35, 36, 39]
"""Input only pins. They can be read but not written, and have no internal pull up or pull down."""
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
]
ESP32_RESERVED_FLASH_PINS = [0, 2, 5, 12, 15]
"""Strapping pins, read at boot to decide how the chip starts. Devices cannot use them.

    0: held low enters the bootloader
    2: must be low or floating to flash
    5, 15: output a signal during boot
    12: held high sets the flash to 1.8V and the board will not boot
"""


class BaseDeviceStatusError(Exception):
    def __init__(self, errno, msg):
        super().__init__(msg)
        self.errno = errno


class BaseDeviceStatus:
    """Status flags for a device. The caller sets each one explicitly before creating a BaseDevice."""

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

    def __str__(self) -> str:
        return f" \
        is_ok={self.is_ok}, \
        is_ready={self.is_ready}, \
        is_panicking={self.is_panicking}, \
        read={self.read}, \
        write={self.write}, \
        noio={self.noio} \
        "


class BaseDeviceError(Exception):
    def __init__(self, errno, msg):
        super().__init__(msg)
        self.errno = errno


class BaseDevice:
    """A device that every other device type wraps. Each field is checked by its _validate_* function."""

    def __init__(
        self,
        *,
        driver,
        state: BaseDeviceStatus,
        name,
        id,
        pin,
    ):
        self.driver = driver
        self.state = _validate_state(state)
        self.name = _validate_name(name)
        self.id = _validate_id(id)
        self.pin = _validate_pin(pin)


class I2CDevice:
    """A BaseDevice plus the I2C address range of its module."""

    def __init__(self, device: BaseDevice, ident: I2CDeviceIdentifier):
        self.addr_range = ident.addr_range
        self.device = device
        self.ident = ident


ALLOWED_IDENT_SIZE_BITS = 32
REGEX_NAME = "[^A-Z]"  # Must contain no special chars


def _validate_id(id) -> int:
    """Return id if it is an int that fits in ALLOWED_IDENT_SIZE_BITS."""
    if (t := type(id)) is not int:
        raise BaseDeviceError(EBADDEVICEID, f"error=device id must be a int, id={t}")
    if (l := (len(bin(id))) - 2) > ALLOWED_IDENT_SIZE_BITS:
        raise BaseDeviceError(
            EBADDEVICEID,
            f"error=device id is oversized, id={l}, expected={ALLOWED_IDENT_SIZE_BITS}",
        )
    return id


def _validate_name(name) -> str:
    """Return name as an uppercase string of only A-Z characters."""
    # Try to convert name to string
    if type(name) is not str:
        try:
            name = str(name)
        except Exception as err:  # noqa: BLE001
            raise BaseDeviceError(
                EBADDEVICENAME, f"error=cannot convert name to string {err}"
            )

    # Name must be within bounds of allowed bits, but cannot be less than one
    if (l := len(name.encode()) * 8) > ALLOWED_IDENT_SIZE_BITS or l < 1:
        raise BaseDeviceError(
            EBADDEVICENAME, f"error=invalid device name range len={l}"
        )

    name = name.upper()
    # Regex verify. re.search returns None if nothing is found, which is falsy
    if pattern := re.search(REGEX_NAME, name):
        raise BaseDeviceError(
            EBADDEVICENAME, f"error=found bad pattern for name, pattern={pattern}"
        )

    return name


def _validate_state(state: BaseDeviceStatus):
    """Return state if it can be used to create a device. is_ready is always reset to False."""

    # Device must be in a good state to create
    if not state.is_ok or state.is_panicking:
        raise BaseDeviceError(
            EDEVICEPANICKING if state.is_panicking else EDEVICENOTOK,
            "error=device was initialized in a bad state",
        )

    # Check for contradictions: cannot have no io modes, cannot have noio and any io
    if not (state.read or state.write or state.noio):
        raise BaseDeviceError(
            EDEVICENOIOMODE,
            "error=expected at least one io mode to be selected, got none",
        )
    # Can't have noio enabled and any other io mode enabled
    if state.noio and (state.read or state.write):
        raise BaseDeviceError(
            EBADDEVICEIOMODE, "error=cannot have both noio and io modes enabled"
        )
    # Lastly, a device must be set to ready afterwards. If the state is already ready, it is set to False
    if state.is_ready:
        state.is_ready = False

    return state


def _validate_pin(pin) -> Pin | None:
    """Return a machine.Pin for a usable ESP32 pin, or None if pin is None."""

    # If input is None, return None
    if pin is None:
        return None

    # If pin is not an int, try to convert it
    if (t := type(pin)) is not int:
        try:
            pin = int(pin)
        except ValueError:
            raise BaseDeviceError(
                EBADDEVICEPINTYPE,
                f"error=got invalid value for device pin, pin_type={t}",
            )
        except TypeError as err:
            raise BaseDeviceError(
                EBADDEVICEPINTYPE, f"error=invalid pin type, err={err}"
            )
    # Check if the pin is in a valid range
    if not (ESP32_MAX_GPIO_PINS >= pin >= ESP32_MIN_GPIO_PINS):
        raise BaseDeviceError(
            EBADDEVICEPINOUTOFRANGE, f"error=device pin is out of bounds, pin={pin}"
        )
    # Check if the pin is in the valid usable range
    if (
        pin not in ESP32_USABLE_GPIO_INPUT_PINS
        and pin not in ESP32_USABLE_GPIO_INPUT_OUTPUT_PINS
    ):
        raise BaseDeviceError(
            EBADDEVICEPINNOTUSABLE, "error=device pin is not usable for gpio"
        )

    try:
        return Pin(pin)
    except ValueError as err:
        raise BaseDeviceError(
            EBADDEVICEPINOUTOFRANGE, f"error=pin is not a real gpio, err={err}"
        )
    except TypeError as err:
        raise BaseDeviceError(
            EBADDEVICEPINTYPE, f"error=pin is invalid type, err={err}"
        )
