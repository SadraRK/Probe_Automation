from typing import Union, List
import time

import nidaqmx
import nidaqmx.system
import numpy as np
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.stream_writers import AnalogMultiChannelWriter

from common.async_warp import async_wrap


@async_wrap
def run_task_async(task: nidaqmx.Task, *args, **kwargs):
    return task.read(*args, **kwargs)


class DAQDevices:
    def __init__(self):
        self.active_read_channel = []
        self.device: nidaqmx.system.device.Device = None
        self.ai_voltage_channels = []
        self.ao_voltage_channels = []
        self.calibrations = {}

        self.ai_voltage_channel_reader: AnalogMultiChannelReader = AnalogMultiChannelReader(nidaqmx.Task().in_stream)
        self.ao_voltage_channel_writer: AnalogMultiChannelWriter = AnalogMultiChannelWriter(nidaqmx.Task().in_stream)

    def device_name(self, name: str):
        if name is None:
            return self.device.name if self.device is not None else None
        else:
            system = nidaqmx.system.System.local()
            if name in system.devices:
                self.device = system.devices[name]
            else:
                raise Exception(f'"{name}" is not found.')

    @staticmethod
    def list_all_devices():
        system = nidaqmx.system.System.local()
        return list(system.devices)

    def list_channels(self, channel_type: str):
        if hasattr(self.device, channel_type):
            return [i.name for i in getattr(self.device, channel_type)]

    @staticmethod
    def daq_one_read(ai_voltage_channels: Union[str, List[str]]):
        result = {}
        if not isinstance(ai_voltage_channels, list):
            ai_voltage_channels = [ai_voltage_channels]

        with nidaqmx.Task() as read_task:
            for channel in ai_voltage_channels:
                read_task.ai_channels.add_ai_voltage_chan(channel)

            data = read_task.read()

            if not isinstance(data, list):
                data = [data]

            for i, channel in enumerate(ai_voltage_channels):
                result[channel] = data[i]

        return result

    def calibrate(self, channel):
        with nidaqmx.Task() as trig_task:
            trig_task.ai_channels.add_ai_voltage_chan(channel)
            data = trig_task.read(number_of_samples_per_channel=1000)

        average_value = float(np.array(data).mean())
        self.calibrations[channel] = average_value
        return average_value

    def add_ai_voltage_channel(self, channel):
        if channel not in self.ai_voltage_channels and channel in self.list_channels("ai_physical_chans"):
            self.ai_voltage_channels.append(channel)
            self.create_new_read_stream()

    def remove_ai_voltage_channel(self, channel):
        if channel in self.ai_voltage_channels:
            self.ai_voltage_channels.remove(channel)
            if len(self.ai_voltage_channels) > 0:
                self.create_new_read_stream()

    def add_ao_voltage_channel(self, channel):
        if channel not in self.ao_voltage_channels and channel in self.list_channels("ao_physical_chans"):
            self.ao_voltage_channels.append(channel)
            self.create_new_write_stream()

    def remove_ao_voltage_channel(self, channel):
        if channel in self.ao_voltage_channels:
            self.ao_voltage_channels.remove(channel)
            if len(self.ao_voltage_channels) > 0:
                self.create_new_write_stream()

    def create_new_read_stream(self):
        self.close()
        read_task = nidaqmx.Task()
        for channel in self.ai_voltage_channels:
            read_task.ai_channels.add_ai_voltage_chan(channel)

        self.ai_voltage_channel_reader = AnalogMultiChannelReader(read_task.in_stream)

    def create_new_write_stream(self):
        self.close()
        write_task = nidaqmx.Task()
        for channel in self.ao_voltage_channels:
            write_task.ao_channels.add_ao_voltage_chan(channel)

        self.ao_voltage_channel_writer = AnalogMultiChannelWriter(write_task.in_stream)

    def read_one(self):
        values_to_test = np.zeros(len(self.ai_voltage_channels), dtype=np.float64)
        self.ai_voltage_channel_reader.read_one_sample(values_to_test)
        return values_to_test.tolist()

    def write_one(self, write_Value, channel_ID):
        values_to_test = np.zeros(len(self.ao_voltage_channels), dtype=np.float64)
        for i in range(len(channel_ID)):
            values_to_test[channel_ID[i]] = np.float64(write_Value[i])
        self.ao_voltage_channel_writer.write_one_sample(values_to_test)
        return values_to_test.tolist()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        # self.ai_voltage_channel_reader._task.close()
        self.ai_voltage_channel_reader._task.__exit__(None, None, None)
        self.ao_voltage_channel_writer._task.__exit__(None, None, None)

if __name__ == '__main__':
    daq_devices = DAQDevices()
    daq_devices.device_name("Dev1")
    print(daq_devices.list_channels("ai_physical_chans"))
    daq_devices.add_ai_voltage_channel('Dev1/ai0')
    print(daq_devices.read_one())
    print(daq_devices.read_one())
    daq_devices.add_ai_voltage_channel('Dev1/ai1')
    print(daq_devices.read_one())
    print(daq_devices.read_one())
    daq_devices.remove_ai_voltage_channel('Dev1/ai1')
    print(daq_devices.read_one())
    print(daq_devices.read_one())

    print(daq_devices.list_channels("ao_physical_chans"))
    daq_devices.add_ao_voltage_channel('Dev1/ao0')
    daq_devices.add_ao_voltage_channel('Dev1/ao1')
    daq_devices.add_ao_voltage_channel('Dev1/ao2')
    daq_devices.add_ao_voltage_channel('Dev1/ao3')

    list_value = [0.1, 2, 3.5, 6]
    for i in range(4):
        print(daq_devices.write_one([list_value[i]], [0]))
        time.sleep(5)

    daq_devices.device.reset_device()
    daq_devices.close()