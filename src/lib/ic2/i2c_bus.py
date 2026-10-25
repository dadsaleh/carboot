from machine import I2C, Pin

# dont touch these
_BUS_CREATED = False
_HARDWARE_CONTROLLER = 0
_FREQ = 400000

"""
    I2CBus Object, to be created on boot, else, we cant do nothing
"""


class I2CBus:
    def __init__(self, *, scl: Pin, sda: Pin):
        global _BUS_CREATED
        if not _BUS_CREATED:
            self.inner = I2C(_HARDWARE_CONTROLLER, scl=scl, sda=sda, freq=_FREQ)
            _BUS_CREATED = True
