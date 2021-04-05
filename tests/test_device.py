from unittest.mock import MagicMock, patch, call
from types import SimpleNamespace, GeneratorType

import pytest
from xinput import MODE_ENABLE, MODE_DISABLE
from evdev import UInput, InputDevice, InputEvent, ecodes

from vim_clutchify.device import _get_device, DeviceContext, DeviceConfigurationError


@pytest.fixture
def uinput():
    return MagicMock(spec=UInput)


@pytest.fixture
def input_device():
    device = MagicMock(spec=InputDevice)
    device.name = 'FootSwitch'
    return device


@pytest.fixture
def context(uinput, input_device):
    with patch('vim_clutchify.device.UInput', return_value=uinput), \
            patch('vim_clutchify.device._get_device', return_value=input_device):
        yield DeviceContext('Foot')


@pytest.mark.parametrize('device_name, expected', (
    ('', SimpleNamespace(name='PC Speaker')),
    ('.*', SimpleNamespace(name='PC Speaker')),
    ('FootSwitch', SimpleNamespace(name='FootSwitch')),
    ('1a86:e026', SimpleNamespace(name='HID 1a86:e026 Keyboard')),
    (r'\w+:\w+', SimpleNamespace(name='HID 1a86:e026 Keyboard')),
    ('^HID', SimpleNamespace(name='HID 1a86:e026 Keyboard')),
))
@patch('vim_clutchify.device.InputDevice', side_effect=lambda name: SimpleNamespace(name=name))
@patch('vim_clutchify.device.list_devices', return_value=['PC Speaker', 'HID 1a86:e026 Keyboard', 'FootSwitch'])
def test_get_device(mock_list, mock_id, device_name, expected):
    actual = _get_device(device_name)
    assert actual == expected


@pytest.mark.parametrize('device_name', (
    'not_a_real_device',
    '^$',
    'HID$',
))
@patch('vim_clutchify.device.InputDevice', side_effect=lambda name: SimpleNamespace(name=name))
@patch('vim_clutchify.device.list_devices', return_value=['PC Speaker', 'HID 1a86:e026 Keyboard', 'FootSwitch'])
def test_get_device_error(mock_list, mock_id, device_name):
    with pytest.raises(DeviceConfigurationError):
        _get_device(device_name)


class TestDeviceContext:
    @patch('vim_clutchify.device.operate_xinput_device')
    def test_enter(self, mock_oxd, context, uinput, input_device):
        context.__enter__()
        assert uinput.__enter__.called
        assert mock_oxd.call_args == call(MODE_DISABLE, input_device.name)

    def test_event_loop(self, context, input_device):
        read_loop = [1, 2, 3]
        input_device.read_loop.return_value = iter(read_loop)
        actual = context.event_loop()
        assert isinstance(actual, GeneratorType)
        assert not input_device.read_loop.called  # Because the function is a generator this isn't called until it's consumed.
        assert list(actual) == read_loop
        assert input_device.read_loop.called

    @pytest.mark.parametrize('key, exp_key', (
        ('f11', ecodes.KEY_F11),
        ('f12', ecodes.KEY_F12),
        ('micMute', ecodes.KEY_MICMUTE),
    ))
    def test_tap(self, key, exp_key, context, uinput):
        context.tap(key)
        assert uinput.write.call_args_list == [
            call(ecodes.EV_KEY, exp_key, 1),
            call(ecodes.EV_KEY, exp_key, 0),
        ]
        assert uinput.syn.called

    @patch('vim_clutchify.device.operate_xinput_device')
    def test_exit(self, mock_oxd, context, uinput, input_device):
        context.__exit__(None, None, None)
        assert uinput.__exit__.called
        assert mock_oxd.call_args == call(MODE_ENABLE, input_device.name)
