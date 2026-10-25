"""ESP32 BOOT SEQUENCE, THIS RUNS AT BOOT"""

from machine import Pin

from ic2.i2c_bus import I2CBus

# DO NOT CHANGE THESE
SCL = Pin(22)
SDA = Pin(21)


def boot():
    pass
