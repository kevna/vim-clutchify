#!/usr/bin/env python
import sys
from argparse import ArgumentParser, Namespace

from evdev import ecodes

from vim_clutchify.device import DeviceContext, DeviceError


def parse_args(args: list) -> Namespace:
    """Generate an ArgumentParser for commandline arguments."""
    parser = ArgumentParser(description='Convert down and up keystrokes to two separate taps.')
    parser.add_argument('--device', default='FootSwitch', dest='device_name')
    parser.add_argument('--down', default='F11')
    parser.add_argument('--up', default='F12')
    return parser.parse_args(args)


def core_loop(config: Namespace) -> None:
    """Caputure and input device and replace it's keydown/keyup events with
    separate keypresses.
    """
    with DeviceContext(config.device_name) as device:
        for event in device.event_loop():
            if event.type == ecodes.EV_KEY:  # pylint: disable=no-member
                if event.value == 1:
                    device.tap(config.down)
                elif event.value == 0:
                    device.tap(config.up)


def main() -> None:
    """CLI entrypoint."""
    config = parse_args(sys.argv[1:])
    try:
        core_loop(config)
    except DeviceError as error:
        print(error)
        sys.exit(126)


if __name__ == '__main__':
    main()
