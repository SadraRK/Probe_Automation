import asyncio
import csv
from asyncio import sleep
from datetime import datetime

import nidaqmx
import numpy as np
from nidaqmx.constants import SampleTimingType, TriggerType, Edge
from scipy.io import savemat

from common.relative_path import get_relative_path
from components.live_info import add_live_info_class
from components.motors import wait_for_motors, get_motors, find_nearby_device
from hardware.daq_devices import run_task_async
from hardware.laser_tsl_550 import TSL550
from server.requests.add_action import add_action, add_action_by_name

laser_tsl_550: TSL550 = None
_stop_grid_laser_sweep = False


@add_action
def add_laser():
    global laser_tsl_550
    laser_tsl_550 = TSL550()
    add_action_by_name("laser_tsl_550", laser_tsl_550)
    add_live_info_class("laser_tsl_550", laser_tsl_550)
    add_action(laser_sweep)
    add_action(grid_laser_sweep)
    add_action(stop_grid_laser_sweep)
    return laser_tsl_550


async def laser_sweep(
        input_channels, trigger_channel,
        start_wavelength, stop_wavelength,
        number_of_samples, speed, power,
        responsivity, gain_knob, gain, attn,
        name="", save=True
):
    global laser_tsl_550
    pre_wavelength = laser_tsl_550.laser.wavelength()
    pre_shutter = laser_tsl_550.power.shutter()

    if not isinstance(input_channels, list):
        input_channels = [input_channels]

    if len(input_channels) == 0:
        raise Exception("no input channels")

    trig_task = nidaqmx.Task()
    for channel in input_channels:
        trig_task.ai_channels.add_ai_voltage_chan(channel)
    trig_task.timing.samp_timing_type = SampleTimingType.SAMPLE_CLOCK
    trig_task.timing.samp_clk_rate = number_of_samples / ((stop_wavelength - start_wavelength) / speed)
    trig_task.triggers.start_trigger.trig_type = TriggerType.DIGITAL_EDGE
    trig_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=trigger_channel, trigger_edge=Edge.RISING)

    print("Turning on laser...")
    # Laser Wavelength
    laser_tsl_550.laser.wavelength(start_wavelength)
    laser_tsl_550.power.power(TSL550.Power.Unit.mW, power)
    laser_tsl_550.power.on()
    laser_tsl_550.power.shutter(True)
    laser_tsl_550.output_trigger.output(TSL550.OutputTrigger.Status.START)

    await laser_tsl_550.wait_for_completion()
    await asyncio.sleep(0.5)

    daq_data = run_task_async(trig_task, number_of_samples_per_channel=number_of_samples, timeout=60)
    print("Starting sweep...")
    laser_tsl_550.sweep.wavelength(
        start=start_wavelength,
        stop=stop_wavelength,
        speed=speed,
        mode=TSL550.Sweep.Mode.CONTINUOUS_ONE_WAY
    )

    daq_data = await daq_data
    if len(np.array(daq_data).shape) == 1:
        daq_data = [daq_data]

    data_scaled = (np.array(daq_data) / (responsivity * gain_knob * gain * power * attn)).tolist()
    wavelength_list = np.linspace(start_wavelength, stop_wavelength, number_of_samples).tolist()

    results = {"wavelength": wavelength_list}

    for i in range(len(input_channels)):
        channel_name = input_channels[i].replace("/", "_")
        results[channel_name + "_raw"] = daq_data[i]
        results[channel_name] = data_scaled[i]

    name = f"_{name}" if len(name) > 0 else ""
    filename = f"../data/{datetime.timestamp(datetime.now())}{name}"
    if save:
        savemat(get_relative_path(__file__, f"{filename}.mat"), results)

        with open(get_relative_path(__file__, f"{filename}.csv"), 'w', newline='') as file:
            writerfile = csv.writer(file)
            writerfile.writerow(results.keys())
            writerfile.writerows(zip(*results.values()))

    await laser_tsl_550.wait_for_completion()
    print("Sweep completed successfully...")

    laser_tsl_550.power.shutter(pre_shutter)
    laser_tsl_550.laser.wavelength(pre_wavelength)
    trig_task.close()

    return results


def stop_grid_laser_sweep(val=None):
    global _stop_grid_laser_sweep
    if val is not None:
        _stop_grid_laser_sweep = val
    return _stop_grid_laser_sweep


async def grid_laser_sweep(
        grid_x, grid_y, step_x, step_y,
        input_channels, trigger_channel,
        start_wavelength, stop_wavelength,
        number_of_samples, speed, power,
        responsivity, gain_knob, gain, attn,
        name="",
        ws_send=None
):
    global _stop_grid_laser_sweep, laser_tsl_550
    _stop_grid_laser_sweep = False
    local_stop_grid_laser_sweep = False

    if not isinstance(input_channels, list):
        input_channels = [input_channels]
    sweep_parameters = {
        "input_channels": input_channels,
        "trigger_channel": trigger_channel,
        "start_wavelength": start_wavelength,
        "stop_wavelength": stop_wavelength,
        "number_of_samples": number_of_samples,
        "speed": speed,
        "power": power,
        "responsivity": responsivity,
        "gain_knob": gain_knob,
        "gain": gain,
        "attn": attn,
        "name": name
    }
    motor_x, motor_y = await get_motors()
    original_position = (motor_x.position(), motor_y.position())
    original_wavelength = laser_tsl_550.laser.wavelength()
    motor_x.speed(0.5)
    motor_y.speed(0.5)
    await wait_for_motors()

    motor_x.position(original_position[0])
    motor_y.position(original_position[1])
    await wait_for_motors()
    for i in range(grid_x):
        if i != 0:
            motor_x.forward(step_x)
            motor_y.backward(step_y * (grid_y - 1))

        for j in range(grid_y):
            index = f"[{i * grid_y + j + 1}/{grid_x * grid_y}]"
            print(f"{index} Going to location...")

            if j != 0:
                motor_y.forward(step_y)

            await wait_for_motors()
            results = await laser_sweep(**sweep_parameters, save=False)
            max_wavelength = results["wavelength"][np.argmax(results[input_channels[0].replace("/", "_")])]
            laser_tsl_550.laser.wavelength(max_wavelength)
            if ws_send is not None:
                await ws_send({"uuid": "grid_laser_sweep_sweep", "data": results})

            values = await find_nearby_device(input_channels[0])
            print(f"Detected max value: {values[-1]}")
            values = await find_nearby_device(input_channels[0])
            print(f"Detected max value: {values[-1]}")

            if values[-1] < 0.02:
                print(f"{index} Detected max value less then threshold (0.02)")

                # if ws_send is not None:
                #     await ws_send({"uuid": "grid_laser_sweep_sweep", "data": await laser_sweep(**sweep_parameters)})
                #
                # if (input("Continue? [Yn]: ").lower() or "y") == "n":
                #     stop_grid_laser_sweep(True)

            current_position = (motor_x.position(), motor_y.position())
            if i == 0 and j == 0:
                original_position = current_position
            indexed_name = f"{name}_{i}_{j}_{current_position[0]}_{current_position[1]}"
            sweep_parameters["name"] = indexed_name

            for k in range(5):
                print(f"{index} Starting ({k + 1}/{5}) Sweep for " + indexed_name)
                # values = await find_nearby_device(input_channels[0])
                # print(f"Detected max value: {values[-1]}")

                sweep_parameters["name"] = indexed_name + f"_{k}"
                results = await laser_sweep(**sweep_parameters)

                if ws_send is not None:
                    await ws_send({"uuid": "grid_laser_sweep_sweep", "data": results})

                await sleep(1)
            print(f"{index} Completed Sweep for " + indexed_name)

            local_stop_grid_laser_sweep = stop_grid_laser_sweep()
            if local_stop_grid_laser_sweep:
                print(f"Stopped Grid Laser Sweep!!!")
                break

        if local_stop_grid_laser_sweep:
            print(f"Stopped Grid Laser Sweep!!!")
            break

    motor_x.position(original_position[0])
    motor_y.position(original_position[1])
    laser_tsl_550.laser.wavelength(original_wavelength)
    await wait_for_motors()
    if local_stop_grid_laser_sweep:
        raise Exception("Sweep Aborted")
    return None
