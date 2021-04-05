from unittest.mock import patch, call
from types import SimpleNamespace

import pytest
from evdev import ecodes, InputEvent

from vim_clutchify.__main__ import core_loop


def config_ns(**kwargs):
    kwargs = {
        'device_name': 'FootSwitch',
        'down': 'F11',
        'up': 'F12',
        **kwargs,
    }
    return SimpleNamespace(**kwargs)
def input_event(typ=ecodes.EV_KEY, code=ecodes.KEY_F11, value='down'):
    value = {
        'down': 1,
        'hold': 2,
        'up': 0,
    }[value]
    return InputEvent(1617662278, 0.93205, typ, code, value)


@pytest.mark.parametrize('config, events, exp_taps', (
    (config_ns(), [], []),
    (
        config_ns(),
        [
            # Relative event used for eg. cursor movement/scroll is ignored
            input_event(typ=ecodes.EV_REL, code=8),
            # Absolute event used for eg. tablet or touchscreen interfaces
            input_event(typ=ecodes.EV_ABS),
            # Repeat event for key held continuously
            input_event(value='hold'),
        ],
        [],  # All events in this test are kinds we ignore
    ),
    (
        config_ns(device_name='HID 1a86:e026 Keyboard', down='MicMute', up='micMute'),
        [input_event(value='down'), input_event(value='up')],
        [call('MicMute'), call('micMute')],
    ),
    (
        config_ns(),
        [
            input_event(value='hold'),  # hold event is ignored
            input_event(value='up'),
            input_event(value='down'),
            input_event(value='up'),
            # An up event without the down can happen in the rate case that
            # the footswitch is pressed for a shorter period than it scans
            input_event(value='up'),
            input_event(value='down'),
            input_event(value='hold'),
            input_event(value='hold'),
        ],
        [call('F12'), call('F11'), call('F12'), call('F12'), call('F11')],
    ),
))
def test_core_loop(config, events, exp_taps):
    with patch('vim_clutchify.__main__.DeviceContext') as context:
        instance = context.return_value.__enter__.return_value = context.return_value
        instance.event_loop.return_value = iter(events)
        core_loop(config)
        assert context.call_args == call(config.device_name)
        assert instance.event_loop.called
        assert instance.tap.call_args_list == exp_taps
