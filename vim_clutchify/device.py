import re
from typing import Optional, Type, Iterable
from types import TracebackType

from xinput import operate_xinput_device, MODE_ENABLE, MODE_DISABLE
from evdev import list_devices, InputDevice, InputEvent, UInput, ecodes


class DeviceError(Exception):
    """General error class for the device library."""


class DeviceConfigurationError(DeviceError):
    """Subclass of DeviceError for configuration problems."""


def _get_device(device_name: str) -> InputDevice:
    """Helper to get a device using a regex to match names.
    :param device_name: string to use for matching the device name
    :return: device object form the first match
    :raises:
        DeviceConfigurationError: if no matching devices were found
    """
    for device in list_devices():
        device = InputDevice(device)
        if re.search(device_name, device.name):
            return device
    raise DeviceConfigurationError(f'No device found to match "{device_name}"')


class DeviceContext:
    """Context Handler to provide UInput functionality.
    This wraps UInput context handler to disable the xinput device while in use.
    It also provides some uinput helper methods to expose uinput functionality.
    :param device_name: string to use for matching the device name
    """

    def __init__(self, device_name: str):
        self.device = _get_device(device_name)
        self.uinput = UInput()

    def __enter__(self) -> 'DeviceContext':
        """Context Handler entry.
        Disable the selected device with xinput and call the wrapped entry.
        :return: this object with helpers to expose uinput functionality
        """
        operate_xinput_device(MODE_DISABLE, self.device.name)
        self.uinput.__enter__()
        return self

    def event_loop(self) -> Iterable[InputEvent]:
        """Expose the selected device's event read loop.
        :return: iterate InputEvents from the underlying device functionality
        """
        yield from self.device.read_loop()

    def tap(self, key: str) -> None:
        """Tap a key by sending instantaneous keydown, keyup and syncing.
        :param key: String key name to tap (from evdev.ecodes.KEY_*)
        """
        key = ecodes.ecodes[f'KEY_{key.upper()}']
        # Pylint claims evdev.ecodes.EV_KEY doesn't exists so needs disabling
        self.uinput.write(ecodes.EV_KEY, key, 1)  # pylint: disable=no-member
        self.uinput.write(ecodes.EV_KEY, key, 0)  # pylint: disable=no-member
        self.uinput.syn()

    def __exit__(self, typ: Optional[Type[BaseException]],
                 value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        """Context Handler exit.
        Re-enable the selected device with xinput and call the wrapped exit.
        """
        self.uinput.__exit__(typ, value, traceback)
        operate_xinput_device(MODE_ENABLE, self.device.name)
