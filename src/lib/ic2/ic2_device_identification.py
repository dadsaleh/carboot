from micropython import const

ENOADDR = const(1)


class I2CDeviceIdentifierError(Exception):
    def __init__(self, errno, msg):
        self.errno = errno
        super().__init__(self, errno, msg)
        self.errno = errno


class I2CDeviceIdentifier:
    def __init__(self, *, module_id: str):
        self.addr_range = get_addr(module_id)
        if self.addr_range == None:
            raise I2CDeviceIdentifierError(
                ENOADDR, f"error=could not find an address range for {module_id}"
            )
        self.module_id = module_id


ADDR = {
    "DS1307": 0x68,
    "AT24C32": (0x50, 0x57),
    "DS3231": 0x68,
    "PCF8574T": (0x20, 0x27),
    "PCF8574AT": (0x38, 0x3F),
    "SSD1306": (0x3C, 0x3D),
    "INA219": (0x40, 0x4F),
    "ADS1115": (0x48, 0x4B),
    "MPU6050": (0x68, 0x69),
    "BME280": (0x76, 0x77),
    "MCP23017": (0x20, 0x27),
}


"""
    Returns the range of addresses for a given device id, or None if no device is found
"""


def get_addr(device_id: str) -> list | None:
    addresses = ADDR[device_id]
    if addresses == None:
        return None
    if type(addresses) == tuple:  # Address pair: 0 is start, 1 is end
        return list(range(addresses[0], addresses[1] + 1))
    return [addresses]


if __name__ == "__main__":
    import unittest

    class TestAddr(unittest.TestCase):
        def test_get_one_addr(self):
            addr = get_addr("DS1307")
            if addr == None:
                self.fail()
            self.assertEqual(addr[0], 0x68)

        def test_get_range(self):
            addresses = get_addr("MCP23017")
            if addresses == None:
                self.fail()
            count = 0
            for address in addresses:
                count += 1
                print(hex(address))
            if count != 8:
                self.fail()

    unittest.main()
