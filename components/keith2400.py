import asyncio
from asyncio import sleep
from datetime import datetime
import nidaqmx
from nidaqmx.constants import SampleTimingType
from nidaqmx import stream_readers
from scipy.io import savemat
from hardware.laser_tsl_550 import TSL550
from common.relative_path import get_relative_path
import UeiDaq
import numpy as np
import time
from components.laser import add_laser
from components.laser import laser_sweep
from components.live_info import add_live_info_class
# from hardware.KEITH2400 import KEITH2400_A, KEITH2400_B
from server.requests.add_action import add_action, add_action_by_name

# keith2400_a: KEITH2400_A = None
# keith2400_b: KEITH2400_B = None
laser_tsl_550 = add_laser()

# @add_action
# def add_keith():
#     global keith2400_a, keith2400_b
#     keith2400_a = KEITH2400_A()
#     keith2400_b = KEITH2400_B()
#
#     add_action_by_name("keith2400_a", keith2400_a)
#     add_live_info_class("keith2400_a", keith2400_a)
#
#     add_action_by_name("keith2400_b", keith2400_b)
#     add_live_info_class("keith2400_b", keith2400_b)
#
#     return keith2400_a, keith2400_b

# @add_action
# async def keith_sweep(
#         input_channels, trigger_channel,
#         start_wavelength, stop_wavelength,
#         number_of_samples, speed, power,
#         responsivity, gain_knob, gain, attn,
#         name="",
#         start_a=0, stop_a=3, num_a=16,
#         start_b=0, stop_b=3, num_b=16,
#         ws_send=None
# ):
#     if (num_a != num_b) and (num_a * num_b != 0):
#         raise Exception("num_a and num_b should be equal or zero")
#     elif (num_a != num_b) and (num_a * num_b == 0):
#         if (num_a == 0):
#             current_a = []
#             voltage_a = list(np.ones(num_b)*start_a)
#             resistance_a = []
#
#             current_b = []
#             voltage_b = list(np.linspace(start=start_b, stop=stop_b, num=num_b))
#             resistance_b = []
#
#         elif (num_b == 0):
#             current_b = []
#             voltage_b = list(np.ones(num_a)*start_b)
#             resistance_b = []
#
#             current_a = []
#             voltage_a = list(np.linspace(start=start_b, stop=stop_b, num=num_a))
#             resistance_a = []
#     else:
#         current_a = []
#         voltage_a = list(np.linspace(start=start_a, stop=stop_a, num=num_a))
#         resistance_a = []
#
#         current_b = []
#         voltage_b = list(np.linspace(start=start_b, stop=stop_b, num=num_b))
#         resistance_b = []
#
#     sweep_parameters = {
#         "input_channels": input_channels,
#         "trigger_channel": trigger_channel,
#         "start_wavelength": start_wavelength,
#         "stop_wavelength": stop_wavelength,
#         "number_of_samples": number_of_samples,
#         "speed": speed,
#         "power": power,
#         "responsivity": responsivity,
#         "gain_knob": gain_knob,
#         "gain": gain,
#         "attn": attn,
#         "name": name
#     }
#
#     keith_a = KEITH2400_A()
#     keith_a.write(':SENS:FUNC "CURR"')
#     keith_a.write(':SENS:CURR:RANG:AUTO 1')
#     keith_a.write(':SENS:CURR:PROT 100e-3')
#     keith_a.write(':SOUR:FUNC VOLT')
#     keith_a.write(':FORM:ELEM CURR')
#
#     keith_b = KEITH2400_B()
#     keith_b.write(':SENS:FUNC "CURR"')
#     keith_b.write(':SENS:CURR:RANG:AUTO 1')
#     keith_b.write(':SENS:CURR:PROT 100e-3')
#     keith_b.write(':SOUR:FUNC VOLT')
#     keith_b.write(':FORM:ELEM CURR')
#
#     for i in range(len(voltage_a)):
#         current_v_a = float(voltage_a[i])
#         string_a = f":SOUR:VOLT {current_v_a}"
#         print(f"{string_a=}")
#         keith_a.write('%s' %string_a)
#         keith_a.write(':OUTP ON')
#
#         current_v_b = float(voltage_b[i])
#         string_b = f":SOUR:VOLT {current_v_b}"
#         print(f"{string_b=}")
#         keith_b.write('%s' %string_b)
#         keith_b.write(':OUTP ON')
#
#         current_i_a = float(keith_a.query(':READ?'))
#         print(f"{current_i_a=}")
#         current_a.append(current_i_a)
#         resistance_a.append(current_v_a/current_i_a)
#
#         current_i_b = float(keith_b.query(':READ?'))
#         print(f"{current_i_b=}")
#         current_b.append(current_i_b)
#         resistance_b.append(current_v_b/current_i_b)
#
#         await sleep(0.1)
#
#         sweep_parameters["name"] = f"{name}_{current_v_a}_{current_v_b}"
#         results = await laser_sweep(**sweep_parameters)
#         if ws_send is not None:
#             await ws_send({"uuid": "grid_laser_sweep_sweep", "data": results})
#
#         await sleep(0.1)
#
#         keith_a.write(':OUTP OFF')
#         keith_b.write(':OUTP OFF')
#
#     print("keithley #1 voltage = {0}".format(voltage_a))
#     print("keithley #1 current = {1}".format(current_a))
#     print("keithley #1 resistance = {2}".format(resistance_a))
#
#     print("keithley #2 voltage = {3}".format(voltage_b))
#     print("keithley #2 current = {4}".format(current_b))
#     print("keithley #2 resistance = {5}".format(resistance_b))
#
#     return {
#         "V_1": voltage_a,
#         "I_1": current_a,
#         "R_1": resistance_a,
#         "V_2": voltage_b,
#         "I_2": current_b,
#         "R_2": resistance_b,
#     }

@add_action
async def DAQ_sweep(
        input_channels, trigger_channel,
        start_wavelength, stop_wavelength,
        number_of_samples, speed, power,
        responsivity, gain_knob, gain, attn,
        name="",
        save=True,
        start_0="0", stop_0="20", num_0="0",
        start_1="0", stop_1="20", num_1="0",
        start_2="0", stop_2="20", num_2="0",
        start_3="0", stop_3="20", num_3="0",
        start_4="0", stop_4="20", num_4="0",
        start_5="0", stop_5="20", num_5="0",
        start_6="0", stop_6="20", num_6="0",
        start_7="0", stop_7="20", num_7="0",
        ws_send=None
):
    size_l = max([num_0, num_1, num_2, num_3, num_4, num_5, num_6, num_7])
    Input = np.zeros((8))
    if num_0 == 0:
        i0 = np.around(np.linspace(start=start_0, stop=start_0, num=size_l) * 0.001, 4)
    else:
        i0 = np.around(np.linspace(start = start_0, stop = stop_0, num = num_0) * 0.001, 4)

    if num_1 == 0:
        i1 = np.around(np.linspace(start=start_1, stop=start_1, num=size_l) * 0.001, 4)
    else:
        i1 = np.around(np.linspace(start = start_1, stop = stop_1, num = num_1) * 0.001, 4)

    if num_2 == 0:
        i2 = np.around(np.linspace(start=start_2, stop=start_2, num=size_l) * 0.001, 4)
    else:
        i2 = np.around(np.linspace(start = start_2, stop = stop_2, num = num_2) * 0.001, 4)

    if num_3 == 0:
        i3 = np.around(np.linspace(start=start_3, stop=start_3, num=size_l) * 0.001, 4)
    else:
        i3 = np.around(np.linspace(start = start_3, stop = stop_3, num = num_3) * 0.001, 4)

    if num_4 == 0:
        i4 = np.around(np.linspace(start=start_4, stop=start_4, num=size_l) * 0.001, 4)
    else:
        i4 = np.around(np.linspace(start = start_4, stop = stop_4, num = num_4) * 0.001, 4)

    if num_5 == 0:
        i5 = np.around(np.linspace(start=start_5, stop=start_5, num=size_l) * 0.001, 4)
    else:
        i5 = np.around(np.linspace(start = start_5, stop = stop_5, num = num_5) * 0.001, 4)

    if num_6 == 0:
        i6 = np.around(np.linspace(start=start_6, stop=start_6, num=size_l) * 0.001, 4)
    else:
        i6 = np.around(np.linspace(start = start_6, stop = stop_6, num = num_6) * 0.001, 4)

    if num_7 == 0:
        i7 = np.around(np.linspace(start=start_7, stop=start_7, num=size_l) * 0.001, 4)
    else:
        i7 = np.around(np.linspace(start = start_7, stop = stop_7, num = num_7) * 0.001, 4)

    print("Turning on laser...")
    # Laser Wavelength
    laser_tsl_550.laser.wavelength(1550)
    laser_tsl_550.power.power(TSL550.Power.Unit.mW, power)
    laser_tsl_550.power.on()
    laser_tsl_550.power.shutter(True)
    laser_tsl_550.output_trigger.output(TSL550.OutputTrigger.Status.START)

    try:
        session = UeiDaq.CUeiSession()
        session.CreateAOCurrentChannel("pdna://172.28.2.4/Dev1/AO0:7", 0, 20.0)

        session.ConfigureTimingForSimpleIO()
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()

        data_final = np.zeros((size_l, len(input_channels)))
        print("Starting Sweep")
        for i in range(0, size_l):
            Input[0] = i0[i]
            Input[1] = i1[i]
            Input[2] = i2[i]
            Input[3] = i3[i]
            Input[4] = i4[i]
            Input[5] = i5[i]
            Input[6] = i6[i]
            Input[7] = i7[i]
            with nidaqmx.Task() as trig_task:
                for channel in input_channels:
                    trig_task.ai_channels.add_ai_voltage_chan(channel)
                trig_task.timing.samp_timing_type = SampleTimingType.SAMPLE_CLOCK
                trig_task.timing.samp_clk_rate = 1000
                await asyncio.sleep(0.01)
                writer.WriteSingleScan(Input)
                await asyncio.sleep(0.01)
                daq_data = trig_task.read(number_of_samples_per_channel= 1000, timeout=10)
                if len(np.array(daq_data).shape) == 1:
                    daq_data = [daq_data]
                data_final[i] = np.mean(np.transpose(daq_data), 0)

            time.sleep(0.1)
            print("Loop #" + str(i))
            writer.WriteSingleScan(np.zeros((8)))
        session.Stop()
        print(data_final)

        Index = list(range(len(data_final)))
        results = {"Index": Index}

        for i in range(len(input_channels)):
            channel_name = input_channels[i].replace("/", "_")
            results[channel_name + "_raw"] = data_final[:, i]
        name = f"{name}" if len(name) > 0 else ""
        filename = f"../data/{name}"
        if save:
            savemat(get_relative_path(__file__, f"{filename}.mat"), results)

    except UException as e:
        print(e)
    return Input, data_final