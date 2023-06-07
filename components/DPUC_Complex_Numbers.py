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
import operator
from functools import reduce
from colorama import Fore
from decimal import Decimal

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
    Output_Phase = (31872.76000 *(1-0.10248)* np.power(Voltage, 2) - 99.32522 *(1-0.01331)* Voltage)
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
async def DPUC_Complex_Numbers(
        power, wavelength, duty_cycle, name="",
        radial_res="0", phase_res="0", num_trials="0",
        ws_send=None
):
    Phase_range = np.linspace(0, 2 * pi, 2 ** phase_res)
    In_range = np.linspace(0, 1, 2 ** radial_res)
    amp = np.power(In_range, 2)

    ideal_Input = In_range
    Volt_Left_MZI, OutPhase_Left_MZI = Amp2Volt_Phase_Left_MZI(amp)
    Volt_Right_MZI, OutPhase_Right_MZI = Amp2Volt_Phase_Right_MZI(amp)

    Volt_Right_MZI = truncate(Volt_Right_MZI, 7)
    Volt_Left_MZI = truncate(Volt_Left_MZI, 7)

    Volt_Left_MZI = np.ones(Volt_Left_MZI.shape) * Volt_Left_MZI[-1]
    OutPhase_Left_MZI = np.ones(OutPhase_Left_MZI.shape) * OutPhase_Left_MZI[-1]
    Temp_In = np.zeros([len(ideal_Input) * len(Phase_range), 6])

    for i in range(len(ideal_Input)):
        for j in range(len(Phase_range)):
            Temp_In[i * len(Phase_range) + j, 0] = Volt_Left_MZI[i]
            Temp_In[i * len(Phase_range) + j, 1] = Volt_Right_MZI[i]
            Temp_In[i * len(Phase_range) + j, 4] = ideal_Input[i]
            Temp_In[i * len(Phase_range) + j, 5] = Phase_range[j]
            dPhi = OutPhase_Right_MZI[i] - OutPhase_Left_MZI[i]
            while (dPhi < 0):
                dPhi = dPhi + 2 * pi
            while (dPhi > 2 * pi):
                dPhi = dPhi - 2 * pi
            temp_dphi = Phase_range[j] + dPhi - 4.97623
            # + (pi / 2 - 0.2652 + 1.14428)
            while (temp_dphi < 0):
                temp_dphi = temp_dphi + 2 * pi
            while (temp_dphi > 2 * pi):
                temp_dphi = temp_dphi - 2 * pi
            Temp_In[i * len(Phase_range) + j, 3] = temp_dphi
            Temp_In[i * len(Phase_range) + j, 2] = 0

    Temp_In[:, 2] = 0
    Temp_In[:, 3] = truncate(Phi2Volt_PS_R(Temp_In[:, 3]), 7)
    temp_phase = truncate(Phi2Volt_PS_L(np.ones(len(Temp_In[:, 2])) * (pi / 2)), 7)

    Input = np.zeros((10, 8))
    Input_Q = np.zeros((10, 8))
    if duty_cycle > 0.5:
        duty_cycle = 1 - duty_cycle
    Pulse_zero = np.zeros((int((1 - duty_cycle) / duty_cycle), 8))

    for i in range(len(Temp_In)):
        Input = np.append(Input, [[Temp_In[i, 2], 0, Temp_In[i, 0], Temp_In[i, 3], 0, Temp_In[i, 1], 0, 0]], 0)
        Input = np.append(Input, Pulse_zero, 0)
        Input_Q = np.append(Input_Q, [[temp_phase[0], 0, Temp_In[i, 0], Temp_In[i, 3], 0, Temp_In[i, 1], 0, 0]], 0)
        Input_Q = np.append(Input_Q, Pulse_zero, 0)

    Input = np.append(Input, np.zeros((10, 8)), 0)
    Input_Q = np.append(Input_Q, np.zeros((10, 8)), 0)

    print("Input Shape: " + str(Input.shape))
    print("Recoridng Time: " + str(int(5 + (Input.shape[0] + 100) * num_trials * 2e-3 + num_trials * 0.1)) + "sec")
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
    laser_tsl_550.laser.wavelength(wavelength)
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

        session.ConfigureTimingForBufferedIO((Input.shape[0] + 100) * 2 * num_trials,
                                             UeiDaq.UeiTimingClockSourceInternal, 8000, UeiDaq.UeiDigitalEdgeRising,
                                             UeiDaq.UeiTimingDurationContinuous)
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
            writer.WriteMultipleScans(Input_Q)
            writer.WriteMultipleScans(np.zeros((100, 8)))
            time.sleep(0.2)
            print("Multiplication, Trial " + str(i + 1) + " Done!")
        time.sleep(10 + (Input.shape[0] + 100) * num_trials * 2e-3 - num_trials * 0.2)

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
        session.CleanUp()

        Index = list(range(len(Temp_In)))
        results = {"Index": Index}
        results["Expected_Values"] = Temp_In

        name = f"{name}" if len(name) > 0 else ""
        filename = f"../data/{name}"
        savemat(get_relative_path(__file__, f"{filename}_Expected.mat"), results)
        print("Finished Complex Number Generation")

    except UException as e:
        print(e)
    return Input
