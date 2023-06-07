import asyncio
from asyncio import sleep
from datetime import datetime
import time
import nidaqmx
import numpy as np
import random
from nidaqmx.constants import SampleTimingType
from scipy.io import savemat
import UeiDaq
from common.relative_path import get_relative_path
# from components.core import laser_tsl_550, keith2400_a, moku_osc
from components.core import laser_tsl_550, moku_osc
from hardware.laser_tsl_550 import TSL550
from server.requests.add_action import add_action


# @add_action
# async def DPUC_Corr(
#     input_channels, trigger_channel,
#     start_wavelength,
#     number_of_samples, power,
#     input_a, input_b,
#     save=True,
#     name=""
# ):
#     input_a = [float(x) for x in input_a.split(",")]
#     input_b = [float(x) for x in input_b.split(",")]
#     lst = [len(input_a), len(input_b)]
#
#     if (len(input_a) != len(input_b)) and (len(input_a) * len(input_b) == 0):
#         raise Exception("Input_a and Input_b should be the same length. Inputs cannot be empty!")
#     elif (len(input_a) != len(input_b)) and (len(input_a) * len(input_b) != 0):
#         for item in lst:
#             if item < max(lst):
#                 temp = np.zeros(abs(item - max(lst)))
#                 index = lst.index(item)
#                 if index == 0:
#                     input_a.extend(temp)
#                 elif index == 1:
#                     input_b.extend(temp)
#
#     volt_a = 3.1
#     volt_b = 2.6
#
#     volt_ps = []
#
#     for i in range(len(input_a)):
#         if input_a[i] * input_b[i] >= 0:
#             volt_ps.append(3.4)
#         elif input_a[i] * input_b[i] < 0:
#             volt_ps.append(1.7)
#
#     print("Turning on laser...")
#     # Laser Wavelength
#     laser_tsl_550.laser.wavelength(start_wavelength)
#     laser_tsl_550.power.power(TSL550.Power.Unit.mW, power)
#     laser_tsl_550.power.on()
#     laser_tsl_550.power.shutter(True)
#     laser_tsl_550.output_trigger.output(TSL550.OutputTrigger.Status.START)
#
#     try:
#         moku_fg.setPWR(1, volt_a, 0.05)
#     except:
#         moku_fg.connect()
#     else:
#         moku_fg.setPWR(2, volt_b, 0.05)
#
#     keith2400_a.write(':SENS:FUNC "CURR"')
#     keith2400_a.write(':SENS:CURR:RANG:AUTO 1')
#     keith2400_a.write(':SENS:CURR:PROT 100e-3')
#     keith2400_a.write(':SOUR:FUNC VOLT')
#     keith2400_a.write(':FORM:ELEM CURR')
#
#     await sleep(0.1)
#
#     Corr_Out = []
#
#     for i in range(len(volt_ps)):
#         with nidaqmx.Task() as trig_task:
#             for channel in input_channels:
#                 trig_task.ai_channels.add_ai_voltage_chan(channel)
#             trig_task.timing.samp_timing_type = SampleTimingType.SAMPLE_CLOCK
#             trig_task.timing.samp_clk_rate = 60
#
#             await laser_tsl_550.wait_for_completion()
#             await asyncio.sleep(0.5)
#
#             print("Starting Correlation #" + str(i))
#
#             current_v_ps = float(volt_ps[i])
#             keith2400_a.write(f":SOUR:VOLT {current_v_ps}")
#             keith2400_a.write(':OUTP ON')
#
#             await sleep(0.5)
#
#             daq_data = trig_task.read(number_of_samples_per_channel=60, timeout=60)
#
#             if len(np.array(daq_data).shape) == 1:
#                 daq_data = [daq_data]
#
#             Corr_Out.append(np.mean(daq_data[0]))
#             keith2400_a.write(':OUTP OFF')
#
#             if i == len(volt_ps):
#                 moku_fg.resetPWR(1)
#                 moku_fg.resetPWR(2)
#
#     Index = list(range(len(input_a)))
#     results = {"Index": Index}
#     channel_name = input_channels[0].replace("/", "_")
#     results[channel_name + "_raw"] = Corr_Out
#
#     name = f"_{name}" if len(name) > 0 else ""
#     filename = f"../data/{datetime.timestamp(datetime.now())}{name}"
#     if save:
#         savemat(get_relative_path(__file__, f"{filename}.mat"), results)
#
#     await laser_tsl_550.wait_for_completion()
#
#     print("Detection Successful")
#     print(input_a)
#     print(input_b)
#     print(Corr_Out)
#
#     try:
#         moku_fg.resetPWR(1)
#     except:
#         moku_fg.connect()
#     else:
#         moku_fg.resetPWR(2)
#         moku_fg.disconnect()
#
#     return results

@add_action
async def DPUC_rand_Corr(
    input_channels, trigger_channel,
    power, NUM, fc, r, Corr_in,
    save=True,
    name=""
):
    data_rst_num = 0.1*fc
    trig_rst_num = 0.1*2*fc - 2*4

    Input = np.zeros((8))
    Input[2] = 7.05e-3
    Input[5] = 8.95e-3
    Corr_In = np.zeros((NUM, 8))
    Corr_In[:, 2] = [7.05e-3] * NUM
    Corr_In[:, 5] = [8.95e-3] * NUM

    reset = np.zeros((int(data_rst_num), 8))
    reset[:, 2] = [7.05e-3] * int(data_rst_num)
    reset[:, 5] = [8.95e-3] * int(data_rst_num)
    reset[:, 0] = [15.4e-3] * int(data_rst_num)

    Trig = np.zeros((int(2 * (NUM + 4)), 8))
    Trig_reset = np.zeros((int(trig_rst_num), 8))

    count = 0
    Corr_in = str(Corr_in)

    In_a = np.zeros((NUM))
    In_b = np.zeros((NUM))
    c = np.zeros((NUM))
    x_temp = np.zeros((NUM))
    x_temp_bar = np.zeros((NUM))

    if Corr_in.lower() == "false":
        for i in range(0, NUM):
            In_a[i] = random.randint(0, 1)
            In_b[i] = random.randint(0, 1)
            c[i] = bool(In_a[i]) ^ bool(In_b[i])
            if c[i] == False:
                Corr_In[i, 0] = 17.25e-3
            elif c[i] == True:
                Corr_In[i, 0] = 13e-3

    elif Corr_in.lower() == "true":
        for i in range(0, NUM):
            In_a[i] = random.randint(0, 1)

        while (count == 0):
            for i in range(0, NUM):
                x_temp[i] = random.randint(0, 1)
                x_temp_bar[i] = x_temp[i] - 1

            r_b = sum(x_temp) + sum(x_temp_bar)

            if ((round(r * NUM) - r_b) != 0):
                count = 0
            else:
                count = 1

        for i in range(0, NUM):
            if (bool(In_a[i]) ^ bool(x_temp[i]) == 0):
                In_b[i] = 1
            elif (bool(In_a[i]) ^ bool(x_temp[i]) == 1):
                In_b[i] = 0

        c = x_temp
        for i in range(0, NUM):
            c[i] = bool(c[i])
            if c[i] == False:
                Corr_In[i, 0] = 17.25e-3
            elif c[i] == True:
                Corr_In[i, 0] = 13e-3

    for i in range(0, Trig.shape[0]):
        Trig[i, 7] = (i % 2) * 20e-3

    print("Setting Up Moku ...")
    try:
        moku_osc.set_acq_mode('Normal')
        moku_osc.set_front(1)
        moku_osc.set_front(2)
        moku_osc.set_samprate(1e6)
        moku_osc.disable(3)
        moku_osc.disable(4)
        # moku_osc.disable(4)
        print("Moku is ready")
    except:
        moku_osc.connect()
        moku_osc.set_acq_mode('Normal')
        moku_osc.set_front(1)
        moku_osc.set_front(2)
        moku_osc.set_samprate(1e6)
        moku_osc.disable(3)
        moku_osc.disable(4)
        # moku_osc.disable(4)
        print("Connected to Moku (2nd try)")

    print(Input)
    print("Checking laser...")
    # Laser Wavelength
    if laser_tsl_550.power.status() == True:
        print(laser_tsl_550.power.status())
    else:
        laser_tsl_550.laser.wavelength(1550)
        laser_tsl_550.power.power(TSL550.Power.Unit.mW, power)
        laser_tsl_550.power.on()
        laser_tsl_550.power.shutter(True)
        laser_tsl_550.output_trigger.output(TSL550.OutputTrigger.Status.START)
        print("Laser is Ready!")

    try:
        session = UeiDaq.CUeiSession()
        # session_Dev1 = UeiDaq.CUeiSession()
        session.CreateAOCurrentChannel("pdna://172.28.2.4/Dev1/AO0:7", 0, 20.0)
        # session_Dev1.CreateAOCurrentChannel("pdna://172.28.2.4/Dev0/AO0:7", 0, 20.0)

        session.ConfigureTimingForSimpleIO()
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()
        print("Initial izing MZIs and Thermal Heaters")
        await asyncio.sleep(0.1)
        writer.WriteSingleScan(Input)
        await asyncio.sleep(0.2)
        session.Stop()

        session.ConfigureTimingForBufferedIO(1000, UeiDaq.UeiTimingClockSourceInternal, 8*fc, UeiDaq.UeiDigitalEdgeRising, UeiDaq.UeiTimingDurationContinuous)
        # session_Dev1.ConfigureTimingForBufferedIO(1000, UeiDaq.UeiTimingClockSourceInternal, 16*fc, UeiDaq.UeiDigitalEdgeRising, UeiDaq.UeiTimingDurationContinuous)

        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        # writer_Dev1 = UeiDaq.CUeiAnalogScaledWriter(session_Dev1.GetDataStream())
        session.Start()
        # session_Dev1.Start()
        print("Starting Correlation Measurement")

        try:
            a = moku_osc.start_rec(50, 0, name, "", True)
            print("Recording...")
        except:
            moku_osc.connect()
            a = moku_osc.start_rec(50, 0, name, "", True)
            print("Connection Issue Resolved. /n Recording...")

        file_name = a["file_name"]
        time.sleep(1)

        for i in range(0, 100):
            writer.WriteMultipleScans(Corr_In)
            # time.sleep(round(NUM/fc, 5))
            writer.WriteMultipleScans(reset)
            time.sleep(0.1 + NUM / fc)
            # time.sleep(0.1)
            print("Wrote frame# %d" % i)

        try:
            moku_osc.stop_rec()
            print("Recording Stopped...")
            moku_osc.dl(Target= 'ssd', File= file_name, Path= "C:/Users/sar247/OneDrive - University of Pittsburgh/#PHOTONICS LAB#/#PROJECTS#/Components/SProbeAutomation/data/" + name + ".li")
            moku_osc.dele(Target='ssd', File=file_name)
        except:
            moku_osc.connect()
            moku_osc.stop_rec()
            moku_osc.dl(Target='ssd', File= file_name, Path="C:/Users/sar247/OneDrive - University of Pittsburgh/#PHOTONICS LAB#/#PROJECTS#/Components/SProbeAutomation/data/" + name + ".li")
            moku_osc.dele(Target='ssd', File=file_name)
            print("Connection Issue Resolved, and Recording Stopped...")

        session.Stop()
        # session_Dev1.Stop()
        # session.CleanUp()
        # session_Dev1.CleanUp()

        print("Finished Correlation Detection")
        print("Input_a : ", In_a)
        print("Input_b : ", In_b)
        print("Out : ", 2*c-1, ", Number of 1s: ", sum(c), ", Number of -1s: ", sum(c-1))
        print(Corr_In[:, 0])

    except UException as e:
        print(e)
    return Corr_In
