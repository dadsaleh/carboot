import unittest

from devices import *


class TestDevices(unittest.TestCase):
    def test_base_device_valid_creation(self):
        dev1_state = _base_state()
        mock_driver = _mock_driver()
        dev = BaseDevice(_mock_driver(), dev1_state, name="SS", id=42, pin=4)
        self.assertEqual(dev.driver_object.compute(), 2)

    def test_base_device_create_device_with_null_pin(self):
        dev1_state = _base_state()
        dev = BaseDevice(_mock_driver(), dev1_state, name="SS", id=42, pin=None)
        self.assertEqual(dev.pin, None)

    def test_base_device_create_device_with_weight_16_id(self):
        dev1_state = _base_state()
        # 2^16 = 65,536 - 1
        dev = BaseDevice(_mock_driver(), dev1_state, name="SS", id=65535, pin=None)
        self.assertEqual(dev.id, 65535)

    def test_base_device_reject_bad_pin_invalid_range(self):
        dev1_state = _base_state()
        try:
            _ = BaseDevice(_mock_driver(), dev1_state, name="SS", id=42, pin=999)
        except BaseDeviceError as err:
            if err.errno == EBADDEVICEPIN:
                return
        self.fail("EBADDEVICEPIN was not raised")

    def test_base_device_reject_bad_id_too_large(self):
        dev1_state = _base_state()
        try:
            # 2^16 = 65,536 -> starting from 1 should fail this (pass)
            _ = BaseDevice(_mock_driver(), dev1_state, name="SS", id=65536, pin=None)
        except BaseDeviceError as err:
            if err.errno == EBADDEVICEID:
                return
        self.fail("EBADDEVICEID was not raised")

    def test_base_device_reject_name_too_large(self):
        dev1_state = _base_state()
        try:
            # SS = 16, SSS = 24
            _ = BaseDevice(_mock_driver(), dev1_state, name="SSS", id=42, pin=None)
        except BaseDeviceError as err:
            if err.errno == EBADDEVICENAME:
                return
        self.fail()

    def test_base_device_reject_not_ok_device_state(self):
        dev1_state = _base_state(is_ok=False)
        try:
            _ = BaseDevice(_mock_driver(), dev1_state, name="SS", id=42, pin=None)
        except BaseDeviceError as err:
            if err.errno == EDEVICENOTOK:
                return
        self.fail()

    def test_base_device_reject_panic_device_state(self):
        dev1_state = _base_state(is_panicking=True)
        try:
            _ = BaseDevice(_mock_driver(), dev1_state, name="SS", id=42, pin=None)
        except BaseDeviceError as err:
            if err.errno == EDEVICEPANICKING:
                return
        self.fail()

    def test_base_device_reject_io_mode_contradiction(self):
        dev1_state = _base_state(read=False, write=True, noio=True)
        seq_1 = False
        seq_2 = False
        seq_3 = False
        try:
            _ = BaseDevice(_mock_driver(), dev1_state, name="SS", id=42, pin=None)
        except BaseDeviceError as err:
            if err.errno == EBADDEVICEIOMODE:
                seq_1 = True
        dev1_state = _base_state(read=True, write=False, noio=True)
        try:
            _ = BaseDevice(_mock_driver(), dev1_state, name="SS", id=42, pin=None)
        except BaseDeviceError as err:
            if err.errno == EBADDEVICEIOMODE:
                seq_2 = True
        dev1_state = _base_state(read=True, write=True, noio=True)
        try:
            _ = BaseDevice(_mock_driver(), dev1_state, name="SS", id=42, pin=None)
        except BaseDeviceError as err:
            if err.errno == EBADDEVICEIOMODE:
                seq_3 = True
        if seq_1 and seq_2 and seq_3:
            return
        self.fail()


class MockDriver:
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.sum = b + a

    def compute(self) -> int:
        return self.a + self.b


def _mock_driver(a=1, b=1) -> MockDriver:
    driver = MockDriver(a, b)
    return driver


def _base_state(
    *, is_ok=True, is_ready=False, is_panicking=False, read=True, write=True, noio=False
) -> BaseDeviceStatus:
    return (
        _ := BaseDeviceStatus(
            is_ok=is_ok,
            is_ready=is_ready,
            is_panicking=is_panicking,
            read=read,
            write=write,
            noio=noio,
        )
    )


if __name__ == "__main__":
    unittest.main()
