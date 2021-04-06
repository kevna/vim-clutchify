#!/usr/bin/env python
import sys
from collections import namedtuple
from argparse import ArgumentParser, Namespace, Action
from typing import Dict

from evdev import ecodes

from vim_clutchify.device import DeviceContext, DeviceError


CLUTCHIFY_BUILTINS: Dict[str, tuple] = {
    'legacy': ('i', 'esc'),
    'f-low': ('F11', 'F12'),
    'f-high': ('F23', 'F24'),
    'ptt': ('micmute',),
}


ClutchKeys = namedtuple('ClutchKeys', ['up', 'down'], defaults=CLUTCHIFY_BUILTINS['f-low'])


class ClutchKeyAction(Action):
    def __init__(self, *args, **kwargs):
        super(ClutchKeyAction, self).__init__(*args, nargs='+', **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        assert 1 <= len(values) <=2
        values = CLUTCHIFY_BUILTINS.get(values[0], values)
        if len(values) == 1:
            values = values * 2
        setattr(namespace, self.dest, ClutchKeys(*values))


def parse_args(args = sys.argv[1:]) -> Namespace:
    """Generate an ArgumentParser for commandline arguments."""
    parser = ArgumentParser(description='Convert down and up keystrokes to two separate taps.')
    parser.add_argument('--device', default='FootSwitch', dest='device_name')
    parser.add_argument('--keys', action=ClutchKeyAction, default=ClutchKeys())
    return parser.parse_args(args)


def core_loop(config: Namespace) -> None:
    """Caputure and input device and replace it's keydown/keyup events with
    separate keypresses.
    """
    with DeviceContext(config.device_name) as device:
        for event in device.event_loop():
            if event.type == ecodes.EV_KEY:  # pylint: disable=no-member
                if event.value == 1:
                    device.tap(config.keys.down)
                elif event.value == 0:
                    device.tap(config.keys.up)


def main() -> None:
    """CLI entrypoint."""
    config = parse_args()
    print(config)
    try:
        core_loop(config)
    except DeviceError as error:
        print(error)
        sys.exit(126)


if __name__ == '__main__':
    main()
