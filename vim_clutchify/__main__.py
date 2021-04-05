#!/usr/bin/env python
from evdev import ecodes

from vim_clutchify.device import DeviceContext

def main() -> None:
    """Caputure and input device and replace it's keydown/keyup events with
    separate keypresses.
    """
    with DeviceContext('FootSwitch') as device:
        for event in device.event_loop():
            if event.type == ecodes.EV_KEY:  # pylint: disable=no-member
                if event.value == 1:
                    device.tap('F11')
                elif event.value == 0:
                    device.tap('F12')

if __name__ == '__main__':
    main()
