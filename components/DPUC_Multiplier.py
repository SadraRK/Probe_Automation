import asyncio
from server.requests.add_action import add_action, add_action_by_name
from hardware.daq_devices import run_task_async
from hardware.laser_tsl_550 import TSL550
from components.MOKU import add_moku
from nidaqmx.constants import SampleTimingType, TriggerType, Edge
from scipy.io import savemat
from common.relative_path import get_relative_path
from components.laser import add_laser
import UeiDaq
import time
import numpy as np
import random
from math import sin, cos, asin, acos, pi
from colorama import Fore
from decimal import Decimal
import nidaqmx
from nidaqmx.constants import SampleTimingType
from nidaqmx import stream_readers

laser_tsl_550 = add_laser()
moku_osc = add_moku()

def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    step_size_dec = Decimal(str(5 / multiplier))
    temp = np.zeros(len(n))
    for i in range(len(n)):
        temp[i] = float(int(Decimal(str(n[i] * multiplier)) / step_size_dec / multiplier) * step_size_dec)
    return temp
def Amp2Volt_Phase_Left_MZI(Input):
    Voltage = np.zeros([len(Input)])
    for i in range(len(Input)):
        temp = np.roots([26504.27189 * (1 - 0.10005), -24.12770 * (1 - 0.00994), -5.80826 - asin(2 * Input[i] - 1)])
        temp = temp[temp >= 0]
        if temp.size == 0:
            print(Fore.RED + "No Valid Roots, I= " + str(Voltage[i]))
        else:
            idx = np.isreal(temp)
            if temp[idx].size == 0:
                print(Fore.RED + "No Real Roots, I= " + str(i))
                print(-5.80826 - asin(2 * Input[i] - 1))
            else:
                Voltage[i] = np.min(temp[idx])
    Output_Phase = 26504.27189 * (1 - 0.10005) * np.power(Voltage, 2) - 24.12770 * (1 - 0.00994) * Voltage
    return Voltage, Output_Phase
def Amp2Volt_Phase_Right_MZI(Input):
    Voltage = np.zeros([len(Input)])
    for i in range(len(Input)):
        temp = np.roots([-26931.83810 * (1 - 0.10010), 41.60416 * (1 - 0.01042), 3.18238 - asin(2 * Input[i] - 1)])
        temp = temp[temp >= 0]
        if temp.size == 0:
            print(Fore.RED + "No Valid Roots, I= " + str(Voltage[i]))
        else:
            idx = np.isreal(temp)
            if temp[idx].size == 0:
                print(Fore.RED + "No Real Roots, I= " + str(i))
                print(-5.80826 - asin(2 * Input[i] - 1))
            else:
                Voltage[i] = np.min(temp[idx])
    Output_Phase = (26931.83810 * (1 - 0.10010) * np.power(Voltage, 2) - 41.60416 * (1 - 0.01042)* Voltage)
    return Voltage, Output_Phase
def Phi2Volt_PS_L(Input):
    Voltage = np.zeros([len(Input)])
    for i in range(len(Input)):
        temp = np.roots([27295.69578*(1 - 0.09983), -20.75996*(1 - 0.01153), - Input[i]])
        temp = temp[temp >= 0]
        if temp.size == 0:
            print(Fore.RED + "No Valid Roots, I= " + str(Voltage[i]))
        else:
            idx = np.isreal(temp)
            if temp[idx].size == 0:
                print(Fore.RED + "No Real Roots, I= " + str(i))
                print(-1.14428 - Input[i])
            else:
                Voltage[i] = np.min(temp[idx])
    return Voltage
def Phi2Volt_PS_R(Input):
    Voltage = np.zeros([len(Input)])
    for i in range(len(Input)):
        temp = np.roots([26783.00603*(1 - 0.10784), -11.95903*(1 - 0.01007), - Input[i]])
        temp = temp[temp >= 0]
        if temp.size == 0:
            print(Fore.RED + "No Valid Roots, I= " + str(Voltage[i]))
        else:
            idx = np.isreal(temp)
            if temp[idx].size == 0:
                print(Fore.RED + "No Real Roots, I= " + str(i))
                print(-1.30695 - Input[i])
            else:
                Voltage[i] = np.min(temp[idx])
    return Voltage
@add_action
async def DPUC_Homodyne_SimpleMul_Sweep(
        input_channels, trigger_channel,
        power, Wavelength, duty_cycle, name="",
        bit_res= "0",   num_trials = "0",
        ws_send=None
):
    In_range = np.linspace(0, 1, 2 ** bit_res)
    amp = np.power(In_range, 2)

    Volt_Left_MZI, OutPhase_Left_MZI = Amp2Volt_Phase_Left_MZI(amp)
    Volt_Right_MZI, OutPhase_Right_MZI = Amp2Volt_Phase_Right_MZI(amp)
    Input_left = np.zeros((10, 8))
    Input_right = np.zeros((10, 8))
    Input_MUL = np.zeros((10, 8))
    if duty_cycle > 0.5:
        duty_cycle = 1 - duty_cycle
    Pulse_zero = np.zeros((int((1-duty_cycle)/duty_cycle), 8))

    for i in range(len(amp)):
        Input_left = np.append(Input_left, [[0, 0, Volt_Left_MZI[i], 0, 0, 0, 0, 0]], 0)
        Input_left = np.append(Input_left, Pulse_zero, 0)

        Input_right = np.append(Input_right, [[0, 0, 0, 0, 0, Volt_Right_MZI[i], 0, 0]], 0)
        Input_right = np.append(Input_right, Pulse_zero, 0)

        Input_MUL = np.append(Input_MUL, [[0, 0, Volt_Left_MZI[i], 0, 0, Volt_Right_MZI[i], 0, 0]], 0)
        Input_MUL = np.append(Input_MUL, Pulse_zero, 0)

    Input_left = np.append(Input_left, np.zeros((10, 8)), 0)
    Input_right = np.append(Input_right, np.zeros((10, 8)), 0)
    Input_MUL = np.append(Input_MUL, np.zeros((10, 8)), 0)

    print("Input Shape: " + str(Input_left.shape))
    print("Recoridng Time: " + str(int(5 + (Input_left.shape[0] + 100) * num_trials * 3e-3 + num_trials * 0.1)) + "sec")
    print("Setting Up Moku ...")
    try:
        moku_osc.set_acq_mode('Normal')
        moku_osc.set_front(1)
        moku_osc.disable(2)
        moku_osc.disable(3)
        moku_osc.set_front(4)
        moku_osc.set_samprate(1e6)
        print("Moku is ready")
    except:
        moku_osc.disconnect()
        moku_osc.connect()
        moku_osc.set_acq_mode('Normal')
        moku_osc.set_front(1)
        moku_osc.disable(2)
        moku_osc.disable(3)
        moku_osc.set_front(4)
        moku_osc.set_samprate(1e6)
        print("Connected to Moku (2nd try)")

    # Laser Wavelength
    laser_tsl_550.laser.wavelength(Wavelength)
    laser_tsl_550.power.power(TSL550.Power.Unit.mW, power)
    laser_tsl_550.power.on()
    laser_tsl_550.power.shutter(True)
    laser_tsl_550.output_trigger.output(TSL550.OutputTrigger.Status.START)
    print("Laser is Ready")

    try:
        session = UeiDaq.CUeiSession()
        session.CreateAOCurrentChannel("pdna://172.28.2.4/Dev1/AO0:7", 0, 20.0)

        session.ConfigureTimingForSimpleIO()
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()

        await asyncio.sleep(0.1)
        writer.WriteSingleScan(np.zeros((8)))
        await asyncio.sleep(0.1)
        session.Stop()
        print("Finished Initializing MZIs and Thermal Heaters")
        print("Starting Multiplication...")

        session.ConfigureTimingForBufferedIO((Input_left.shape[0] + 100) * 3 * num_trials, UeiDaq.UeiTimingClockSourceInternal, 8000, UeiDaq.UeiDigitalEdgeRising, UeiDaq.UeiTimingDurationContinuous)
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()

        try:
            a = moku_osc.start_rec(3600, 0, name, "", True)
            print("Recording...")
        except:
            moku_osc.connect()
            a = moku_osc.start_rec(3600, 0, name, "", True)
            print("Connection Issue Resolved. /n Recording...")

        file_name = a["file_name"]
        await asyncio.sleep(0.5)

        for i in range(0, num_trials):
            writer.WriteMultipleScans(Input_left)
            writer.WriteMultipleScans(np.zeros((100, 8)))
            writer.WriteMultipleScans(Input_right)
            writer.WriteMultipleScans(np.zeros((100, 8)))
            writer.WriteMultipleScans(Input_MUL)
            writer.WriteMultipleScans(np.zeros((100, 8)))
            time.sleep(0.1*3)
            print("MZI Sweep, Trial " + str(i + 1) + " Done!")
        time.sleep(10 + (Input_left.shape[0] + 100) * num_trials * 3e-3 - num_trials*0.3)

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
        print("Expected_Input: " + str(In_range))
        print("MZI_Left Input Current: " + str(Volt_Left_MZI))
        print("MZI_Right Input Current: " + str(Volt_Right_MZI))
        print("Finished Multiplication Sweep")

    except UException as e:
        print(e)
    return In_range
@add_action
async def DPUC_test_PS(
        input_channels, trigger_channel,
        power, Wavelength, duty_cycle, name="",
        num_trials = "0", save=True,
        ws_send=None
):
    ideal_Input = np.linspace(0, 1, 8)
    Phase_shifter_sweep_values = np.linspace(0, 20, 21)*1e-3
    Volt_Left_MZI, OutPhase_Left_MZI = Amp2Volt_Phase_Left_MZI(ideal_Input)
    Volt_Right_MZI, OutPhase_Right_MZI = Amp2Volt_Phase_Right_MZI(ideal_Input)

    Device_Values = np.zeros([len(Phase_shifter_sweep_values) * len(ideal_Input) ** 2, 7])

    for i in range(len(ideal_Input)):
        for j in range(len(ideal_Input)):
            for k in range(len(Phase_shifter_sweep_values)):
                Device_Values[i * len(ideal_Input)*len(Phase_shifter_sweep_values) + j * len(Phase_shifter_sweep_values) + k, 0] = ideal_Input[i]
                Device_Values[i * len(ideal_Input)*len(Phase_shifter_sweep_values) + j * len(Phase_shifter_sweep_values) + k, 3] = Volt_Left_MZI[i]
                Device_Values[i * len(ideal_Input)*len(Phase_shifter_sweep_values) + j * len(Phase_shifter_sweep_values) + k, 4] = OutPhase_Left_MZI[i]
                Device_Values[i * len(ideal_Input)*len(Phase_shifter_sweep_values) + j * len(Phase_shifter_sweep_values) + k, 1] = ideal_Input[j]
                Device_Values[i * len(ideal_Input)*len(Phase_shifter_sweep_values) + j * len(Phase_shifter_sweep_values) + k, 5] = Volt_Right_MZI[i]
                Device_Values[i * len(ideal_Input)*len(Phase_shifter_sweep_values) + j * len(Phase_shifter_sweep_values) + k, 6] = OutPhase_Right_MZI[i]
                Device_Values[i * len(ideal_Input)*len(Phase_shifter_sweep_values) + j * len(Phase_shifter_sweep_values) + k, 2] = Phase_shifter_sweep_values[k]

    data_final = np.zeros((Device_Values.shape[0], len(input_channels)))
    Input = np.zeros((8))
    Pulse_zero = np.zeros((8))

    print("Input Shape: " + str(Device_Values.shape[0]))
    print("Recoridng Time: " + str(int(5 + Device_Values.shape[0] * 1e-3)) + "sec")

    # Laser Wavelength
    laser_tsl_550.laser.wavelength(Wavelength)
    laser_tsl_550.power.power(TSL550.Power.Unit.mW, power)
    laser_tsl_550.power.on()
    laser_tsl_550.power.shutter(True)
    laser_tsl_550.output_trigger.output(TSL550.OutputTrigger.Status.START)
    print("Laser is Ready")

    try:
        session = UeiDaq.CUeiSession()
        session.CreateAOCurrentChannel("pdna://172.28.2.4/Dev1/AO0:7", 0, 20.0)

        session.ConfigureTimingForSimpleIO()
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()

        time.sleep(0.1)
        writer.WriteSingleScan(Pulse_zero)
        time.sleep(0.1)
        print("Finished Initializing MZIs and Thermal Heaters")
        print("Starting Sweep...")

        time.sleep(0.5)

        for i in range(0, Device_Values.shape[0]):
            Input[2] = Device_Values[i, 3]
            Input[0] = Device_Values[i, 2]
            Input[5] = Device_Values[i, 5]
            with nidaqmx.Task() as trig_task:
                for channel in input_channels:
                    trig_task.ai_channels.add_ai_voltage_chan(channel)
                trig_task.timing.samp_timing_type = SampleTimingType.SAMPLE_CLOCK
                trig_task.timing.samp_clk_rate = 1000
                time.sleep(0.01)
                writer.WriteSingleScan(Input)
                time.sleep(0.01)
                daq_data = trig_task.read(number_of_samples_per_channel= 1000, timeout=10)
                if len(np.array(daq_data).shape) == 1:
                    daq_data = [daq_data]
                data_final[i] = np.mean(np.transpose(daq_data), 0)
            print("Loop #" + str(i+1))
            writer.WriteSingleScan(Pulse_zero)
            time.sleep(0.5)
        session.Stop()
        print(data_final)

        Index = list(range(len(data_final)))
        results = {"Index": Index}
        for i in range(len(input_channels)):
            channel_name = input_channels[i].replace("/", "_")
            results[channel_name + "_raw"] = data_final[:, i]
        results["Ideal_Input_Left"] = Device_Values[:, 0]
        results["Ideal_Input_Right"] = Device_Values[:, 1]
        results["Current_Phase_Shifter"] = Device_Values[:, 2]
        results["Current_Left_MZI"] = Device_Values[:, 3]
        results["Phase_Left_MZI"] = Device_Values[:, 4]
        results["Current_Right_MZI"] = Device_Values[:, 5]
        results["Phase_Right_MZI"] = Device_Values[:, 6]
        name = f"{name}" if len(name) > 0 else ""
        filename = f"../data/{name}"
        if save:
            savemat(get_relative_path(__file__, f"{filename}.mat"), results)
        print("Finished Sweep")

    except UException as e:
        print(e)
    return Input

@add_action
async def DPUC_Homodyne_SimpleMul(
        input_channels, trigger_channel,
        power, Wavelength, duty_cycle, name="",
        bit_res= "0",   num_trials = "0",
        ws_send=None
):
    In_range = np.linspace(0, 1, 2 ** bit_res)
    amp = np.power(In_range, 2)

    ideal_Input = In_range
    ideal_Input = np.append(-ideal_Input[len(ideal_Input):0:-1], ideal_Input)

    Volt_Left_MZI, OutPhase_Left_MZI = Amp2Volt_Phase_Left_MZI(amp)
    Volt_Left_MZI = np.append(Volt_Left_MZI[len(Volt_Left_MZI):0:-1], Volt_Left_MZI)
    OutPhase_Left_MZI = np.append(OutPhase_Left_MZI[len(OutPhase_Left_MZI):0:-1], OutPhase_Left_MZI)

    Volt_Right_MZI, OutPhase_Right_MZI = Amp2Volt_Phase_Right_MZI(amp)
    Volt_Right_MZI = np.append(Volt_Right_MZI[len(Volt_Right_MZI):0:-1], Volt_Right_MZI)
    OutPhase_Right_MZI = np.append(OutPhase_Right_MZI[len(OutPhase_Right_MZI):0:-1], OutPhase_Right_MZI)

    Temp_In = np.zeros([len(ideal_Input) ** 2, 6])

    for i in range(len(ideal_Input)):
        for j in range(len(ideal_Input)):
            Temp_In[i * len(ideal_Input) + j, 0] = Volt_Left_MZI[i]
            Temp_In[i * len(ideal_Input) + j, 1] = Volt_Right_MZI[j]
            Temp_In[i * len(ideal_Input) + j, 3] = ideal_Input[i]
            Temp_In[i * len(ideal_Input) + j, 4] = ideal_Input[j]
            dPhi = OutPhase_Left_MZI[i] - OutPhase_Right_MZI[j]
            while (dPhi < - 2 *pi):
                dPhi = dPhi + 2 * pi
            while (dPhi > 2 * pi):
                dPhi = dPhi - 2 * pi
            if (ideal_Input[i] * ideal_Input[j]) >= 0:
                temp_dphi = pi / 2 + dPhi
                while (temp_dphi < 0):
                    temp_dphi = temp_dphi + 2 * pi
                while (temp_dphi > 2 * pi):
                    temp_dphi = temp_dphi - 2 * pi
                Temp_In[i * len(ideal_Input) + j, 2] = temp_dphi
            elif (ideal_Input[i] * ideal_Input[j]) < 0:
                temp_dphi = - pi / 2 + dPhi
                while (temp_dphi < 0):
                    temp_dphi = temp_dphi + 2 * pi
                while (temp_dphi > 2 * pi):
                    temp_dphi = temp_dphi - 2 * pi
                Temp_In[i * len(ideal_Input) + j, 2] = temp_dphi
            Temp_In[i * len(ideal_Input) + j, 5] = ideal_Input[i] * ideal_Input[j]

    Temp_In[:, 2] = Phi2Volt_PS_L(Temp_In[:, 2])
    Input = np.zeros((10, 8))
    if duty_cycle > 0.5:
        duty_cycle = 1 - duty_cycle
    Pulse_zero = np.zeros((int((1-duty_cycle)/duty_cycle), 8))

    for i in range(Temp_In.shape[0]):
        Input = np.append(Input, [[Temp_In[i, 2], 0, Temp_In[i, 0], 0, 0, Temp_In[i, 1], 0, 0]], 0)
        Input = np.append(Input, Pulse_zero, 0)

    Input = np.append(Input, np.zeros((10, 8)), 0)

    print("Input Shape: " + str(Input.shape))
    print("Recoridng Time: " + str(int(5 + (Input.shape[0] + 100) * num_trials * 1e-3 + num_trials * 0.1)) + "sec")
    print("Setting Up Moku ...")
    try:
        moku_osc.set_acq_mode('Normal')
        moku_osc.set_front(1)
        moku_osc.set_front(2)
        moku_osc.set_front(3)
        moku_osc.set_front(4)
        moku_osc.set_samprate(1e6)
        print("Moku is ready")
    except:
        moku_osc.disconnect()
        moku_osc.connect()
        moku_osc.set_acq_mode('Normal')
        moku_osc.set_front(1)
        moku_osc.set_front(2)
        moku_osc.set_front(3)
        moku_osc.set_front(4)
        moku_osc.set_samprate(1e6)
        print("Connected to Moku (2nd try)")

    # Laser Wavelength
    laser_tsl_550.laser.wavelength(Wavelength)
    laser_tsl_550.power.power(TSL550.Power.Unit.mW, power)
    laser_tsl_550.power.on()
    laser_tsl_550.power.shutter(False)
    laser_tsl_550.output_trigger.output(TSL550.OutputTrigger.Status.START)
    print("Laser is Ready")

    try:
        session = UeiDaq.CUeiSession()
        session.CreateAOCurrentChannel("pdna://172.28.2.4/Dev1/AO0:7", 0, 20.0)

        session.ConfigureTimingForSimpleIO()
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()

        await asyncio.sleep(0.1)
        writer.WriteSingleScan(np.zeros((8)))
        await asyncio.sleep(0.1)
        session.Stop()
        print("Finished Initializing MZIs and Thermal Heaters")
        print("Starting Multiplication...")

        session.ConfigureTimingForBufferedIO((Input.shape[0] + 100) * num_trials, UeiDaq.UeiTimingClockSourceInternal, 8000, UeiDaq.UeiDigitalEdgeRising, UeiDaq.UeiTimingDurationContinuous)
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()

        try:
            a = moku_osc.start_rec(3600, 0, name, "", True)
            print("Recording...")
        except:
            moku_osc.connect()
            a = moku_osc.start_rec(3600, 0, name, "", True)
            print("Connection Issue Resolved. /n Recording...")

        file_name = a["file_name"]
        await asyncio.sleep(0.5)

        for i in range(0, num_trials):
            writer.WriteMultipleScans(Input)
            writer.WriteMultipleScans(np.zeros((100, 8)))
            time.sleep(0.1)
            print("Multiplication, Trial " + str(i + 1) + " Done!")
        time.sleep(10 + (Input.shape[0] + 100) * num_trials * 1e-3 - num_trials * 0.1)

        try:
            moku_osc.stop_rec()
            print("Recording Stopped...")
            moku_osc.dl(Target='ssd', File=file_name,
                        Path="C:/Users/sar247/OneDrive - University of Pittsburgh/#PHOTONICS LAB#/#PROJECTS#/Components/SProbeAutomation/data/" + name + ".li")
            moku_osc.dele(Target='ssd', File=file_name)
        except:
            moku_osc.connect()
            moku_osc.stop_rec()
            moku_osc.dl(Target='ssd', File=file_name,
                        Path="C:/Users/sar247/OneDrive - University of Pittsburgh/#PHOTONICS LAB#/#PROJECTS#/Components/SProbeAutomation/data/" + name + ".li")
            moku_osc.dele(Target='ssd', File=file_name)
            print("Connection Issue Resolved, and Recording Stopped...")

        session.Stop()

        Index = list(range(len(Temp_In)))
        results = {"Index": Index}
        results["Expected_Values"] = Temp_In

        name = f"{name}" if len(name) > 0 else ""
        filename = f"../data/{name}"
        savemat(get_relative_path(__file__, f"{filename}_Expected.mat"), results)
        print("Finished Homodyne Multiplication")

    except UException as e:
        print(e)
    return Input
@add_action
async def DPUC_Homodyne_DotProduct(
        input_channels, trigger_channel,
        power, Wavelength, duty_cycle, data_length, name="",
        bit_res= "0",   num_trials = "0",
        ws_send=None
):
    In_range = np.linspace(0, 1, 2 ** bit_res)
    ideal_Input = In_range
    ideal_Input = np.append(-ideal_Input[len(ideal_Input):0:-1], ideal_Input)
    IN_L = []
    IN_R = []
    while (np.array_equal(IN_L, IN_R) == True):
        for i in range(data_length):
            IN_L.append(random.choice(ideal_Input))
            IN_R.append(random.choice(ideal_Input))

    amp_L = np.power(IN_L, 2)
    amp_R = np.power(IN_R, 2)
    Volt_Left_MZI, OutPhase_Left_MZI = Amp2Volt_Phase_Left_MZI(amp_L)
    Volt_Right_MZI, OutPhase_Right_MZI = Amp2Volt_Phase_Right_MZI(amp_R)

    Temp_In = np.zeros([len(IN_L), 6])

    for i in range(len(IN_L)):
        Temp_In[i, 0] = Volt_Left_MZI[i]
        Temp_In[i, 1] = Volt_Right_MZI[i]
        Temp_In[i, 3] = IN_L[i]
        Temp_In[i, 4] = IN_R[i]
        dPhi = OutPhase_Left_MZI[i] - OutPhase_Right_MZI[i]
        while (dPhi < - 2 * pi):
            dPhi = dPhi + 2 * pi
        while (dPhi > 2 * pi):
            dPhi = dPhi - 2 * pi
        if (IN_L[i] * IN_R[i]) >= 0:
            temp_dphi = pi / 2 + dPhi
            while (temp_dphi < 0):
                temp_dphi = temp_dphi + 2 * pi
            while (temp_dphi > 2 * pi):
                temp_dphi = temp_dphi - 2 * pi
            Temp_In[i, 2] = temp_dphi
        elif (IN_L[i] * IN_R[i]) < 0:
            temp_dphi = - pi / 2 + dPhi
            while (temp_dphi < 0):
                temp_dphi = temp_dphi + 2 * pi
            while (temp_dphi > 2 * pi):
                temp_dphi = temp_dphi - 2 * pi
            Temp_In[i, 2] = temp_dphi
        Temp_In[i, 5] = IN_L[i] * IN_R[i]

    Temp_In[:, 2] = Phi2Volt_PS_L(Temp_In[:, 2])
    Input = np.zeros((10, 8))
    if duty_cycle > 0.5:
        duty_cycle = 1 - duty_cycle
    Pulse_zero = np.zeros((int((1-duty_cycle)/duty_cycle), 8))

    for i in range(Temp_In.shape[0]):
        Input = np.append(Input, [[Temp_In[i, 2], 0, Temp_In[i, 0], 0, 0, Temp_In[i, 1], 0, 0]], 0)
        Input = np.append(Input, Pulse_zero, 0)

    Input = np.append(Input, np.zeros((10, 8)), 0)

    print("Input Shape: " + str(Input.shape))
    print("Recoridng Time: " + str(int(5 + (Input.shape[0] + 100) * num_trials * 1e-3 + num_trials * 0.1)) + "sec")
    print("Setting Up Moku ...")
    try:
        moku_osc.set_acq_mode('Normal')
        moku_osc.set_front(1)
        moku_osc.set_front(2)
        moku_osc.set_front(3)
        moku_osc.set_front(4)
        moku_osc.set_samprate(1e6)
        print("Moku is ready")
    except:
        moku_osc.disconnect()
        moku_osc.connect()
        moku_osc.set_acq_mode('Normal')
        moku_osc.set_front(1)
        moku_osc.set_front(2)
        moku_osc.set_front(3)
        moku_osc.set_front(4)
        moku_osc.set_samprate(1e6)
        print("Connected to Moku (2nd try)")

    # Laser Wavelength
    laser_tsl_550.laser.wavelength(Wavelength)
    laser_tsl_550.power.power(TSL550.Power.Unit.mW, power)
    laser_tsl_550.power.on()
    laser_tsl_550.power.shutter(True)
    laser_tsl_550.output_trigger.output(TSL550.OutputTrigger.Status.START)
    print("Laser is Ready")

    try:
        session = UeiDaq.CUeiSession()
        session.CreateAOCurrentChannel("pdna://172.28.2.4/Dev1/AO0:7", 0, 20.0)

        session.ConfigureTimingForSimpleIO()
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()

        await asyncio.sleep(0.1)
        writer.WriteSingleScan(np.zeros((8)))
        await asyncio.sleep(0.1)
        session.Stop()
        print("Finished Initializing MZIs and Thermal Heaters")
        print("Starting Multiplication...")

        session.ConfigureTimingForBufferedIO((Input.shape[0] + 100) * num_trials, UeiDaq.UeiTimingClockSourceInternal, 8000, UeiDaq.UeiDigitalEdgeRising, UeiDaq.UeiTimingDurationContinuous)
        writer = UeiDaq.CUeiAnalogScaledWriter(session.GetDataStream())
        session.Start()

        try:
            a = moku_osc.start_rec(3600, 0, name, "", True)
            print("Recording...")
        except:
            moku_osc.connect()
            a = moku_osc.start_rec(3600, 0, name, "", True)
            print("Connection Issue Resolved. /n Recording...")

        file_name = a["file_name"]
        await asyncio.sleep(0.5)

        for i in range(0, num_trials):
            writer.WriteMultipleScans(Input)
            writer.WriteMultipleScans(np.zeros((100, 8)))
            time.sleep(0.1)
            print("Multiplication, Trial " + str(i + 1) + " Done!")
        time.sleep(10 + (Input.shape[0] + 100) * num_trials * 1e-3 - num_trials * 0.1)

        try:
            moku_osc.stop_rec()
            print("Recording Stopped...")
            moku_osc.dl(Target='ssd', File=file_name,
                        Path="C:/Users/sar247/OneDrive - University of Pittsburgh/#PHOTONICS LAB#/#PROJECTS#/Components/SProbeAutomation/data/" + name + ".li")
            moku_osc.dele(Target='ssd', File=file_name)
        except:
            moku_osc.connect()
            moku_osc.stop_rec()
            moku_osc.dl(Target='ssd', File=file_name,
                        Path="C:/Users/sar247/OneDrive - University of Pittsburgh/#PHOTONICS LAB#/#PROJECTS#/Components/SProbeAutomation/data/" + name + ".li")
            moku_osc.dele(Target='ssd', File=file_name)
            print("Connection Issue Resolved, and Recording Stopped...")

        session.Stop()

        Index = list(range(len(Temp_In)))
        results = {"Index": Index}
        results["Expected_Values"] = Temp_In

        name = f"{name}" if len(name) > 0 else ""
        filename = f"../data/{name}"
        savemat(get_relative_path(__file__, f"{filename}_Expected.mat"), results)
        print("Finished Dot Product Multiplication")

    except UException as e:
        print(e)
    return Input