import time
import math
from typing import Union, Tuple, Dict
import nidaqmx
import numpy as np
from common.wait_for import wait_for_working_device
from components.live_info import add_live_info_class
from hardware.motor_NRT150 import NRT150
from server.requests.add_action import add_action_by_name, add_action

motor_x: NRT150 = None
motor_y: NRT150 = None


@add_action
def add_motors():
    global motor_x, motor_y
    motor_x = NRT150(index=0)
    motor_y = NRT150(index=1)
    while(not (motor_x.is_working()) or not(motor_y.is_working())):
        time.sleep(1)
    motor_x.speed(10)
    motor_y.speed(10)
    motor_x.position(75)
    motor_y.position(75)

    add_action_by_name("motorX", motor_x)
    add_action_by_name("motorY", motor_y)

    add_live_info_class("motorX", motor_x)
    add_live_info_class("motorY", motor_y)

    return motor_x, motor_y


async def get_motors():
    global motor_x, motor_y
    return motor_x, motor_y


async def wait_for_motors():
    await wait_for_working_device(motor_x.is_working)
    await wait_for_working_device(motor_y.is_working)


@add_action
async def find_nearby_device(signal_channel: str, automax=False, step_size: float = 0.001, tries=50):
    def get_value():
        with nidaqmx.Task() as trig_task:
            trig_task.ai_channels.add_ai_voltage_chan(signal_channel)
            data = trig_task.read(number_of_samples_per_channel=1000)
        average_value = float(np.array(data).mean())
        return average_value

    def create_coord(t_x, t_y, old_coord=None) -> Dict[Tuple[float, float], Union[None, float]]:
        if old_coord is None:
            old_coord = {}
        new_coors = {
            (t_x, t_y): 0,
            (t_x + step_size, t_y): 0,
            (t_x - step_size, t_y): 0,
            (t_x, t_y + step_size): 0,
            (t_x, t_y - step_size): 0,
            (t_x + (step_size / math.sqrt(2)), t_y + (step_size / math.sqrt(2))): 0,
            (t_x + (step_size / math.sqrt(2)), t_y - (step_size / math.sqrt(2))): 0,
            (t_x - (step_size / math.sqrt(2)), t_y + (step_size / math.sqrt(2))): 0,
            (t_x - (step_size / math.sqrt(2)), t_y - (step_size / math.sqrt(2))): 0,
        }
        for key in new_coors.keys():
            if key in old_coord:
                new_coors[key] = old_coord[key]
        return new_coors

    await wait_for_motors()
    x_speed = motor_x.speed()
    y_speed = motor_y.speed()
    motor_x.speed(min(1, 10 * step_size))
    motor_y.speed(min(1, 10 * step_size))

    x = motor_x.position()
    y = motor_y.position()

    coors = create_coord(x, y)
    coors[(x, y)] = get_value()
    max_position = (x, y)

    while tries > 0:
        new_position = max_position
        for (pX, pY) in coors.keys():
            if coors[(pX, pY)] != 0:
                continue

            motor_x.position(pX)
            motor_y.position(pY)
            await wait_for_motors()
            coors[(pX, pY)] = get_value()

            new_position = max(coors, key=coors.get)
            if new_position != max_position:
                if automax:
                    tries += 1
                break

        if new_position == max_position:
            break

        max_position = new_position
        coors = create_coord(max_position[0], max_position[1], coors)
        tries -= 1

    motor_x.position(max_position[0])
    motor_y.position(max_position[1])
    await wait_for_motors()
    motor_x.speed(x_speed)
    motor_y.speed(y_speed)
    return [max_position[0], max_position[1], coors[max_position], get_value()]
