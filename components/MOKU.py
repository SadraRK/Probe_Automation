from asyncio import sleep

import numpy as np

from components.laser import laser_sweep
from components.live_info import add_live_info_class
from hardware.KEITH2400 import KEITH2400_A, KEITH2400_B
from hardware.Moku import Moku_OSC
from server.requests.add_action import add_action, add_action_by_name

moku_osc = Moku_OSC()
# moku_fg = Moku_FG()
keith2400_a: KEITH2400_A = None
keith2400_b: KEITH2400_B = None

@add_action
def add_moku():
    # add_action_by_name("moku_fg", moku_fg)
    # add_live_info_class("moku_fg", moku_fg)
    add_action_by_name("moku_osc", moku_osc)
    add_live_info_class("moku_osc", moku_osc)
    return moku_osc

# @add_action
# async def moku_sweep(
#     input_channels, trigger_channel,
#     start_wavelength, stop_wavelength,
#     number_of_samples, speed, power,
#     responsivity, gain_knob, gain, attn,
#     name="",
#     start_a=0, stop_a=3, num_a=16,
#     start_b=0, stop_b=3, num_b=16,
#     ws_send=None
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
#             voltage_a = list(np.linspace(start=start_a, stop=stop_a, num=num_a))
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
#     for i in range(len(voltage_a)):
#         current_v_a = float(voltage_a[i])
#         moku_fg.setPWR(1, current_v_a, 0.05)
#
#         current_v_b = float(voltage_b[i])
#         moku_fg.setPWR(2, current_v_b, 0.05)
#
#         # current_a.append(Moku_FG().readPWR(1, False)['actual_current'])
#         # resistance_a.append((Moku_FG().readPWR(1, False)['actual_voltage'])/(Moku_FG().readPWR(1, False)['actual_current']))
#         #
#         # current_b.append(Moku_FG().readPWR(2, False)['actual_current'])
#         # resistance_b.append((Moku_FG().readPWR(2, False)['actual_voltage'])/(Moku_FG().readPWR(2, False)['actual_current']))
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
#     moku_fg.resetPWR(1)
#     moku_fg.resetPWR(2)
#
#     print("Moku Channel #1 voltage = {0}".format(voltage_a))
#     # print("Moku Channel #1 current = {1}".format(current_a))
#     # print("Moku Channel #1 resistance = {2}".format(resistance_a))
#
#     print("Moku Channel #2 voltage = {3}".format(voltage_b))
#     # print("Moku Channel #2 current = {4}".format(current_b))
#     # print("Moku Channel #2 resistance = {5}".format(resistance_b))
#
#     return {
#         "V_1": voltage_a,
#         # "I_1": current_a,
#         # "R_1": resistance_a,
#         "V_2": voltage_b,
#         # "I_2": current_b,
#         # "R_2": resistance_b,
#     }
#
# @add_action
# async def moku_keith_sweep(
#         input_channels, trigger_channel,
#         start_wavelength, stop_wavelength,
#         number_of_samples, speed, power,
#         responsivity, gain_knob, gain, attn,
#         name="",
#         start_a=0, stop_a=3, num_a=16,
#         start_b=0, stop_b=3, num_b=16,
#         start_c=0, stop_c=3, num_c=16,
#         start_d=0, stop_d=3, num_d=16,
#         ws_send=None
# ):
#
#     lst = [num_a, num_b, num_c, num_d]
#
#     if (num_a != num_b != num_c != num_d) and (num_a * num_b * num_c * num_d != 0):
#         raise Exception("num_a, num_b, num_c, and num_d should be equal or zero")
#     elif (num_a != num_b != num_c != num_d) and (num_a * num_b * num_c * num_d == 0):
#         for item in lst:
#             if item == 0:
#                 index = lst.index(item)
#                 if index == 0:
#                     voltage_a = list(np.ones(max(lst)) * start_a)
#                     voltage_b = list(np.linspace(start=start_b, stop=stop_b, num=num_b))
#                     voltage_c = list(np.linspace(start=start_c, stop=stop_c, num=num_c))
#                     voltage_d = list(np.linspace(start=start_d, stop=stop_d, num=num_d))
#
#                 elif index == 1:
#                     voltage_b = list(np.ones(max(lst)) * start_b)
#                     voltage_a = list(np.linspace(start=start_a, stop=stop_a, num=num_a))
#                     voltage_c = list(np.linspace(start=start_c, stop=stop_c, num=num_c))
#                     voltage_d = list(np.linspace(start=start_d, stop=stop_d, num=num_d))
#
#                 elif index == 2:
#                     voltage_c = list(np.ones(max(lst)) * start_c)
#                     voltage_b = list(np.linspace(start=start_b, stop=stop_b, num=num_b))
#                     voltage_a = list(np.linspace(start=start_a, stop=stop_a, num=num_a))
#                     voltage_d = list(np.linspace(start=start_d, stop=stop_d, num=num_d))
#
#                 elif index == 3:
#                     voltage_d = list(np.ones(max(lst)) * start_d)
#                     voltage_b = list(np.linspace(start=start_b, stop=stop_b, num=num_b))
#                     voltage_c = list(np.linspace(start=start_c, stop=stop_c, num=num_c))
#                     voltage_a = list(np.linspace(start=start_a, stop=stop_a, num=num_a))
#     else:
#         voltage_a = list(np.linspace(start=start_a, stop=stop_a, num=num_a))
#
#         voltage_b = list(np.linspace(start=start_b, stop=stop_b, num=num_b))
#
#         voltage_c = list(np.linspace(start=start_c, stop=stop_c, num=num_c))
#
#         voltage_d = list(np.linspace(start=start_d, stop=stop_d, num=num_d))
#
#     current_a = []
#     resistance_a = []
#     current_b = []
#     resistance_b = []
#     current_c = []
#     resistance_c = []
#     current_d = []
#     resistance_d = []
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
#         # current_i_a = float(keith_a.query(':READ?'))
#         # print(f"{current_i_a=}")
#         # current_a.append(current_i_a)
#         # resistance_a.append(current_v_a/current_i_a)
#         #
#         # current_i_b = float(keith_b.query(':READ?'))
#         # print(f"{current_i_b=}")
#         # current_b.append(current_i_b)
#         # resistance_b.append(current_v_b/current_i_b)
#
#         current_v_c = float(voltage_c[i])
#         moku_fg.setPWR(1, current_v_c, 0.05)
#
#         current_v_d = float(voltage_d[i])
#         moku_fg.setPWR(2, current_v_d, 0.05)
#
#         # current_a.append(Moku_FG().readPWR(1, False)['actual_current'])
#         # resistance_a.append((Moku_FG().readPWR(1, False)['actual_voltage'])/(Moku_FG().readPWR(1, False)['actual_current']))
#         #
#         # current_b.append(Moku_FG().readPWR(2, False)['actual_current'])
#         # resistance_b.append((Moku_FG().readPWR(2, False)['actual_voltage'])/(Moku_FG().readPWR(2, False)['actual_current']))
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
#         moku_fg.resetPWR(1)
#         moku_fg.resetPWR(2)
#
#     print("keithley #1 voltage = {0}".format(voltage_a))
#     # print("keithley #1 current = {1}".format(current_a))
#     # print("keithley #1 resistance = {2}".format(resistance_a))
#
#     print("keithley #2 voltage = {3}".format(voltage_b))
#     # print("keithley #2 current = {4}".format(current_b))
#     # print("keithley #2 resistance = {5}".format(resistance_b))
#
#     print("Moku Channel #1 voltage = {0}".format(voltage_c))
#     # print("Moku Channel #1 current = {1}".format(current_a))
#     # print("Moku Channel #1 resistance = {2}".format(resistance_a))
#
#     print("Moku Channel #2 voltage = {3}".format(voltage_d))
#     # print("Moku Channel #2 current = {4}".format(current_b))
#     # print("Moku Channel #2 resistance = {5}".format(resistance_b))
#
#     return {
#         "V_1": voltage_a,
#         # "I_1": current_a,
#         # "R_1": resistance_a,
#         "V_2": voltage_b,
#         # "I_2": current_b,
#         # "R_2": resistance_b,
#
#         "V_3": voltage_c,
#         # "I_3": current_a,
#         # "R_3": resistance_a,
#         "V_4": voltage_d,
#         # "I_4": current_b,
#         # "R_4": resistance_b,
#     }