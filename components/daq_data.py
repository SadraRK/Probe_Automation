from typing import Union, List

from hardware.daq_devices import DAQDevices
from server.requests.add_action import add_action, add_action_by_name
from server.requests.subscription import add_to_subscription_loop, remove_from_subscription_loop

daq_device: DAQDevices = None


def daq_read(ai_voltage_channels: Union[str, List[str]] = None):
    global daq_device
    if ai_voltage_channels is not None:
        result = DAQDevices.daq_one_read(ai_voltage_channels)
        result["uuid"] = "daq_read"
    else:
        result = {"uuid": "daq_read"}
        data = daq_device.read_one()
        for i, channel in enumerate(daq_device.ai_voltage_channels):
            result[channel] = data[i]

    return result


@add_action
def get_daq_calibration_values():
    global daq_device
    return daq_device.calibrations


@add_action
def daq_calibration(channel: str, calibration: float = None):
    global daq_device
    if calibration is None:
        return daq_device.calibrate(channel)
    elif isinstance(calibration, int) or isinstance(calibration, float):
        daq_device.calibrations[channel] = calibration
    else:
        raise Exception("Invalid data type of calibration value")


@add_action
def get_daq_read(channel: str, subscription: bool = None):
    global daq_device
    if subscription is None:
        return daq_read(channel)

    if subscription:
        daq_device.add_ai_voltage_channel(channel)

    if not subscription:
        daq_device.remove_ai_voltage_channel(channel)

    if len(daq_device.ai_voltage_channels) > 0:
        add_to_subscription_loop(daq_read, 0.025)
    else:
        remove_from_subscription_loop(daq_read)


@add_action
def add_daq():
    global daq_device
    daq_device = DAQDevices()
    daq_device.device_name("Dev1")
    add_action_by_name("DAQDevices", daq_device)
    add_action(get_daq_read)
