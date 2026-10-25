"""Device Class HLA"""

from micropython import const

from lib.ic2.ic2_device_identification import I2CDeviceIdentifier

EBADNAME = const(1)
EBADDEVICEID = const(2)
EDEVICENOTOK = const(3)
EBADIOMODE = const(4)


class BaseDeviceStatusError(Exception):
    def __init__(self, errno, msg):
        super().__init__(self, errno, msg)
        self.errno = errno


"""
    Base Device statuses hold device status. Initnal state matters, if its not ready, or if its in a panicking state, we cannot create
    a base device for this.
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

        if self.noio or (
            self.read or self.write
        ):  # Must have no mode or at least one mode
            self.read = read
            self.write = write
        else:
            raise BaseDeviceStatusError(
                EBADIOMODE,
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
    Inital implementation of a basic device
"""


class BaseDeviceError(Exception):
    def __init__(self, errno, msg):
        super().__init__(msg)
        self.errno = errno


class BaseDevice:
    def __init__(
        self,
        name: str,
        id: str,
        driver: object,
        inital_state: BaseDeviceStatus,
    ):  # Must be at most 32 bits
        if (t := len(name.encode()) * 8) > 32:
            raise BaseDeviceError(
                EBADNAME, f"error=device name greater than 32 bytes, value={t}"
            )
        elif (t := len(id.encode()) * 8) > 32:
            raise BaseDeviceError(
                EBADDEVICEID, f"error=device id greater than 32 bytes, value{t}"
            )
        elif (not inital_state.is_ok) or inital_state.is_panicking:
            raise BaseDeviceError(
                EDEVICENOTOK,
                f"error=device is in a bad state, is_panicking={inital_state.is_panicking}, is_ok={inital_state.is_ok}",
            )
        self.name = name
        self.id = id
        self.state = BaseDeviceStatus
        self.driver_object = driver  # NOTE: we cannot confirm that driver is in fact valid and working, unless specific handlers exist


"""
    I2CDevice is a usable I2C device: wraps around some address and adds to a global list of devices
"""


class I2CDevice:
    def __init__(self, device: BaseDevice, ident: I2CDeviceIdentifier):
        self.addr_range = ident.addr_range
