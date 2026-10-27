"""Fake machine module for running tests on the Unix port, which has no Pin."""

_VALID_PINS = tuple(range(0, 20)) + (21, 22, 23, 25, 26, 27) + tuple(range(32, 40))


class Pin:
    """Stand-in for the ESP32 machine.Pin that stores pin state instead of driving hardware."""

    IN = 1
    OUT = 3
    OPEN_DRAIN = 7
    PULL_DOWN = 1
    PULL_UP = 2
    IRQ_RISING = 1
    IRQ_FALLING = 2
    WAKE_LOW = 4
    WAKE_HIGH = 5
    DRIVE_0 = 0
    DRIVE_1 = 1
    DRIVE_2 = 2
    DRIVE_3 = 3

    def __init__(self, id, mode=-1, pull=-1, *, value=None, drive=None, hold=None):
        if id not in _VALID_PINS:
            raise ValueError("invalid pin")
        self.id = id
        self.mode = None
        self.pull = None
        self.drive = None
        self.hold = None
        self.handler = None
        self.trigger = None
        self._value = 0
        self.init(mode, pull, value=value, drive=drive, hold=hold)

    def init(self, mode=-1, pull=-1, *, value=None, drive=None, hold=None):
        if mode != -1:
            self.mode = mode
        if pull != -1:
            self.pull = pull
        if value is not None:
            self._value = 1 if value else 0
        if drive is not None:
            self.drive = drive
        if hold is not None:
            self.hold = hold

    def value(self, x=None):
        if x is None:
            return self._value
        self._value = 1 if x else 0

    def __call__(self, x=None):
        return self.value(x)

    def on(self):
        self._value = 1

    def off(self):
        self._value = 0

    def toggle(self):
        self._value ^= 1

    def irq(self, handler=None, trigger=IRQ_FALLING | IRQ_RISING, *, wake=None):
        self.handler = handler
        self.trigger = trigger

    def __str__(self):
        return "Pin(" + str(self.id) + ")"
