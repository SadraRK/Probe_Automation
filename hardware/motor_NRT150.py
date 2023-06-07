import sys
import time
import serial
import glob
import re
import subprocess
import thorlabs_apt as apt
import sys
import usb.core

All_NRT150_Connected_Devices = apt.list_available_devices()
Device_ID = [90333926, 90333925]

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

class NRT150():
    def __init__(self, index=0):
        global All_NRT150_Connected_Devices
        self.motor = apt.Motor(Device_ID[index])
        self.motor.enable()
        if self.motor.serial_number is None:
            raise Exception(f"NRT150 - ({Device_ID(index)}) is not connected or being used by some other device")

        self.motor.maximum_position = 150
        self.reference_align()
        self.extreme_value = 0
        self.min_position = int(0)
        self.max_position = int(150)
        self.dd = 1
    def reference_align(self):
        print(f"Referencing motor: {self.motor}")
        self.motor.set_hardware_limit_switches(2, 1)
        self.motor.set_move_home_parameters(2, 1, 2, 0.1)
        self.motor.move_home(False)

    def extreme(self, val: [-1, 0, 1] = None):
        if val is not None:
            if val == 0:
                self.position(self.position())
                self.stop()
                self.extreme_value = val
            elif val == -1:
                self.position(self.min_position)
                self.extreme_value = val
            elif val == 1:
                self.position(self.max_position)
                self.extreme_value = val
        else:
            return self.extreme_value

    def speed(self, val: float = None):
        if val is None:
            return self.motor.get_velocity_parameters()[2]
        else:
            while (self.is_moving()):
                time.sleep(0.5)
            self.motor.set_velocity_parameters(0, val, val)
            return self.motor.get_velocity_parameters()[2]

    def position(self, val: float = None):
        # while(self.is_moving()):
        #     time.sleep(0.5)
        if val is None:
            return self.motor.position
        else:
            self.motor.move_to(val, False)
            return self.motor.position

    def target_position(self, val: float = None):
        if val is None:
            return self.motor.position
        else:
            while (self.is_moving()):
                time.sleep(0.5)
            self.motor.move_to(val, False)

    def forward(self, val: float):
        while(self.is_moving()):
            time.sleep(0.5)
        self.position(self.position() + val)

    def backward(self, val: float):
        while(self.is_moving()):
            time.sleep(0.5)
        self.position(self.position() - val)

    def stop(self):
        self.position(self.position())
        # self.motor.stop_profiled()

    def is_moving(self):
        return self.motor.is_in_motion

    def is_working(self):
        return self.motor.has_homing_been_completed

if __name__ == '__main__':
    # motor_x = NRT150(0)
    # motor_y = NRT150(1)
    # while(not (motor_x.is_working()) or not(motor_y.is_working())):
    #     time.sleep(1)
    # print(motor_x.speed(), motor_y.speed())
    # print(motor_x.position(), motor_y.position())


    # ser = serial.Serial(
    #     port='/dev/bus/usb/APT',
    #     baudrate=19200,
    #     parity=serial.PARITY_NONE,
    #     stopbits=serial.STOPBITS_ONE,
    #     bytesize=serial.EIGHTBITS
    # )
    # print(ser.isOpen())
    # ser.write("0x80101210")
    # s = ser.read(1)
    # print(s)
    # ser.close()