"""Unit tests for devices.py."""

# pyright: reportOptionalContextManager=false

import unittest

from machine import Pin

from devices import (
    ALLOWED_IDENT_SIZE_BITS,
    EBADDEVICEID,
    EBADDEVICEIOMODE,
    EBADDEVICENAME,
    EBADDEVICEPINNOTUSABLE,
    EBADDEVICEPINOUTOFRANGE,
    EBADDEVICEPINTYPE,
    EDEVICENOIOMODE,
    EDEVICENOTOK,
    EDEVICEPANICKING,
    ESP32_RESERVED_FLASH_PINS,
    ESP32_USABLE_GPIO_INPUT_OUTPUT_PINS,
    ESP32_USABLE_GPIO_INPUT_PINS,
    BaseDevice,
    BaseDeviceError,
    BaseDeviceStatus,
    I2CDevice,
    _validate_id,
    _validate_name,
    _validate_pin,
    _validate_state,
)
from lib.ic2.ic2_device_identification import I2CDeviceIdentifier


class MockDriver:
    """Stand-in driver. BaseDevice stores it without checking it."""


def _state(
    *, is_ok=True, is_ready=False, is_panicking=False, read=True, write=True, noio=False
) -> BaseDeviceStatus:
    return BaseDeviceStatus(
        is_ok=is_ok,
        is_ready=is_ready,
        is_panicking=is_panicking,
        read=read,
        write=write,
        noio=noio,
    )


def _device(**fields) -> BaseDevice:
    """Build a valid BaseDevice, with any field replaced by fields."""
    args = {"driver": MockDriver(), "state": _state(), "name": "SS", "id": 42, "pin": 4}
    args.update(fields)
    return BaseDevice(**args)


class DeviceTestCase(unittest.TestCase):
    def assertErrno(self, errno, func, *args, **kwargs):
        with self.assertRaises(BaseDeviceError) as cm:
            func(*args, **kwargs)
        self.assertEqual(cm.exception.errno, errno)


class TestBaseDeviceStatus(unittest.TestCase):
    def test_stores_flags(self):
        state = _state(is_ok=True, is_ready=True, read=True, write=False)
        self.assertTrue(state.is_ok)
        self.assertTrue(state.is_ready)
        self.assertFalse(state.is_panicking)
        self.assertTrue(state.read)
        self.assertFalse(state.write)
        self.assertFalse(state.noio)

    def test_str_lists_flags(self):
        text = str(_state())
        for flag in ("is_ok", "is_ready", "is_panicking", "read", "write", "noio"):
            with self.subTest(flag=flag):
                self.assertIn(flag + "=", text)


class TestValidateState(DeviceTestCase):
    def test_returns_same_state(self):
        state = _state()
        self.assertIs(_validate_state(state), state)

    def test_accepts_each_io_mode(self):
        for read, write, noio in (
            (True, False, False),
            (False, True, False),
            (False, False, True),
        ):
            with self.subTest(read=read, write=write, noio=noio):
                _validate_state(_state(read=read, write=write, noio=noio))

    def test_resets_is_ready(self):
        self.assertFalse(_validate_state(_state(is_ready=True)).is_ready)

    def test_rejects_not_ok(self):
        self.assertErrno(EDEVICENOTOK, _validate_state, _state(is_ok=False))

    def test_rejects_panicking(self):
        self.assertErrno(EDEVICEPANICKING, _validate_state, _state(is_panicking=True))

    def test_panicking_wins_over_not_ok(self):
        state = _state(is_ok=False, is_panicking=True)
        self.assertErrno(EDEVICEPANICKING, _validate_state, state)

    def test_rejects_no_io_mode(self):
        state = _state(read=False, write=False, noio=False)
        self.assertErrno(EDEVICENOIOMODE, _validate_state, state)

    def test_rejects_noio_with_io(self):
        for read, write in ((True, False), (False, True), (True, True)):
            with self.subTest(read=read, write=write):
                state = _state(read=read, write=write, noio=True)
                self.assertErrno(EBADDEVICEIOMODE, _validate_state, state)


class TestValidateName(DeviceTestCase):
    def test_accepts_uppercase(self):
        self.assertEqual(_validate_name("SS"), "SS")

    def test_uppercases_lowercase(self):
        self.assertEqual(_validate_name("ss"), "SS")

    def test_accepts_name_at_limit(self):
        name = "A" * (ALLOWED_IDENT_SIZE_BITS // 8)
        self.assertEqual(_validate_name(name), name)

    def test_rejects_empty(self):
        self.assertErrno(EBADDEVICENAME, _validate_name, "")

    def test_rejects_oversized(self):
        name = "A" * (ALLOWED_IDENT_SIZE_BITS // 8 + 1)
        self.assertErrno(EBADDEVICENAME, _validate_name, name)

    def test_rejects_non_letters(self):
        for name in ("S1", "S_", "S S", "S-", 'S"', "S\n"):
            with self.subTest(name=name):
                self.assertErrno(EBADDEVICENAME, _validate_name, name)

    def test_converts_non_string(self):
        class Named:
            def __str__(self):
                return "ABC"

        self.assertEqual(_validate_name(Named()), "ABC")

    def test_rejects_unconvertible(self):
        class Broken:
            def __str__(self):
                raise ValueError("no name")

        self.assertErrno(EBADDEVICENAME, _validate_name, Broken())


class TestValidateId(DeviceTestCase):
    def test_accepts_int(self):
        for id in (0, 1, 42):
            with self.subTest(id=id):
                self.assertEqual(_validate_id(id), id)

    def test_accepts_max(self):
        id = (1 << ALLOWED_IDENT_SIZE_BITS) - 1
        self.assertEqual(_validate_id(id), id)

    def test_rejects_oversized(self):
        self.assertErrno(EBADDEVICEID, _validate_id, 1 << ALLOWED_IDENT_SIZE_BITS)

    def test_rejects_non_int(self):
        for id in ("42", 4.2, None, True, [42]):
            with self.subTest(id=id):
                self.assertErrno(EBADDEVICEID, _validate_id, id)


class TestValidatePin(DeviceTestCase):
    def test_none_returns_none(self):
        self.assertIsNone(_validate_pin(None))

    def test_returns_pin(self):
        pin = _validate_pin(4)
        self.assertIsInstance(pin, Pin)
        self.assertEqual(str(pin), "Pin(4)")

    def test_accepts_input_output_pins(self):
        for pin in ESP32_USABLE_GPIO_INPUT_OUTPUT_PINS:
            with self.subTest(pin=pin):
                self.assertEqual(str(_validate_pin(pin)), f"Pin({pin})")

    def test_accepts_input_only_pins(self):
        for pin in ESP32_USABLE_GPIO_INPUT_PINS:
            with self.subTest(pin=pin):
                self.assertEqual(str(_validate_pin(pin)), f"Pin({pin})")

    def test_rejects_reserved_flash_pins(self):
        for pin in ESP32_RESERVED_FLASH_PINS:
            with self.subTest(pin=pin):
                self.assertErrno(EBADDEVICEPINNOTUSABLE, _validate_pin, pin)

    def test_rejects_unusable_pins(self):
        for pin in (1, 3, 6, 14):
            with self.subTest(pin=pin):
                self.assertErrno(EBADDEVICEPINNOTUSABLE, _validate_pin, pin)

    def test_rejects_out_of_range(self):
        for pin in (-1, 40, 999):
            with self.subTest(pin=pin):
                self.assertErrno(EBADDEVICEPINOUTOFRANGE, _validate_pin, pin)

    def test_converts_numeric_string(self):
        self.assertEqual(str(_validate_pin("4")), "Pin(4)")

    def test_rejects_bad_type(self):
        for pin in ("abc", [4], object()):
            with self.subTest(pin=pin):
                self.assertErrno(EBADDEVICEPINTYPE, _validate_pin, pin)


class TestBaseDevice(DeviceTestCase):
    def test_stores_fields(self):
        driver = MockDriver()
        state = _state()
        dev = _device(driver=driver, state=state)
        self.assertIs(dev.driver, driver)
        self.assertIs(dev.state, state)
        self.assertEqual(dev.name, "SS")
        self.assertEqual(dev.id, 42)
        self.assertEqual(str(dev.pin), "Pin(4)")

    def test_uppercases_name(self):
        self.assertEqual(_device(name="ss").name, "SS")

    def test_none_pin(self):
        self.assertIsNone(_device(pin=None).pin)

    def test_resets_is_ready(self):
        self.assertFalse(_device(state=_state(is_ready=True)).state.is_ready)

    def test_rejects_bad_fields(self):
        cases = (
            ("name", "", EBADDEVICENAME),
            ("id", "42", EBADDEVICEID),
            ("pin", 0, EBADDEVICEPINNOTUSABLE),
            ("state", _state(is_ok=False), EDEVICENOTOK),
        )
        for field, value, errno in cases:
            with self.subTest(field=field):
                self.assertErrno(errno, _device, **{field: value})

    def test_fields_are_keyword_only(self):
        with self.assertRaises(TypeError):
            BaseDevice(MockDriver(), _state(), "SS", 42, 4)  # type: ignore


class TestI2CDevice(unittest.TestCase):
    def _base(self) -> BaseDevice:
        return _device(state=_state(read=False, write=False, noio=True), pin=None)

    def test_single_address(self):
        base = self._base()
        ident = I2CDeviceIdentifier(module_id="DS1307")
        dev = I2CDevice(base, ident)
        self.assertIs(dev.device, base)
        self.assertIs(dev.ident, ident)
        self.assertEqual(dev.addr_range, [0x68])

    def test_address_range(self):
        dev = I2CDevice(self._base(), I2CDeviceIdentifier(module_id="MCP23017"))
        self.assertEqual(dev.addr_range, list(range(0x20, 0x28)))


if __name__ == "__main__":
    unittest.main()
