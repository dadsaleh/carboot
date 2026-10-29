# carboot

A phone controlled remote start module for a 2000 to 2004 Honda Odyssey, built on an ESP32 running MicroPython.

## Concept

An ESP32 lives in the car, powered from the car battery through a buck converter. A phone sends commands to it, and it drives the relays that start the engine.

Planned features:

- Remote start and stop from a phone
- Status display on an LCD
- I2C devices such as a real time clock and battery monitor
- Safety first: relays off by default, a crank time limit, shutdown when the brake or hood is touched, and a panic lock that halts the board on a fatal error

## Status

Early development. Not ready for use in a real vehicle.

## Disclaimer

Wiring into a vehicle's ignition system can damage the vehicle or cause injury. Use this project at your own risk.

## AI Assistance

The project logic is written by hand. I use AI (Claude) as a tutor to answer questions, and it wrote or edited only the following:

- `test/mock_pin/machine.py`: the fake `Pin` used to run tests on desktop
- `unit_test.sh` and `pyproject.toml`: the test runner and editor config
- `test/test_config.py` and `test/test_devices.py`: the unit tests
- Small bug fixes in `config.py`, `devices.py`, `main.py`, and `ic2_device_identification.py`
- `src/devices.py`: `I2CDevice.register()` and the `BaseDevice` id type check
- `src/lib/ic2/ic2_device_identification.py`: the I2C address table
- Spelling and comment cleanup across the project, and the text of this README (partly)
- Documentation of modules where need be

## License

MIT, see [LICENSE](LICENSE).
