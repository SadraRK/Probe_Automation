from enum import Enum

from hardware.visa_interface import VisaInterface


class TSL550(VisaInterface):
    class InputTrigger:
        class Status(Enum):
            DISABLE = 0
            ENABLE = 1

        class Standby(Enum):
            NORMAL_OPERATION = 0
            TRIGGER_STANDBY = 1

        def __init__(self, device):
            self.device: TSL550 = device

        def input(self, status: Status = None):
            result = self.device.property_command('TRIG:INP:EXT', status.value if status is not None else None)
            if result is not None:
                return self.Status(int(result))

        def standby(self, status: Standby = None):
            result = self.device.property_command('TRIG:INP:STAN', status.value if status is not None else None)
            if result is not None:
                return self.Standby(int(result))

    class OutputTrigger:
        class Status(Enum):
            NONE = 0
            STOP = 1
            START = 2
            STEP = 3

        def __init__(self, device):
            self.device: TSL550 = device

        def output(self, status: Status = None):
            result = self.device.property_command('TRIG:OUTP', status.value if status is not None else None)
            if result is not None:
                return self.Status(int(result))

        def step(self, val: float = None):
            return self.device.property_command('TRIG:OUTP:STEP', val, 4)

    class Power:
        class Unit(Enum):
            dBW = 0
            mW = 1

        class Control(Enum):
            MANUAL = 0
            AUTO = 1

        def __init__(self, device):
            self.device: TSL550 = device

        def power(self, unit: Unit, val=None):
            self.device.command("POW:UNIT", unit.value)
            return self.device.property_command('POW', val)

        def power_mw(self, val=None):
            return self.power(TSL550.Power.Unit.mW, val)

        def control(self, val: Control = None):
            result = self.device.property_command('POW:ATT:AUT', val.value if val is not None else None)
            if result is not None:
                return self.Control(int(result))

        def shutter(self, val: bool = None):
            if val is None:
                return self.device.property_command('POW:SHUT') == 0
            else:
                self.device.property_command('POW:SHUT', str(int(not val)))

        def status(self, on: bool = None):
            if on is None:
                return self.device.property_command('POW:STAT') == 1
            else:
                self.device.property_command('POW:STAT', str(int(on)))

        def on(self):
            self.status(True)

        def off(self):
            self.status(False)

    class Laser:
        class Unit(Enum):
            nm = 0
            THz = 1

        def __init__(self, device):
            self.device: TSL550 = device

        def unit(self, unit: Unit):
            result = self.device.property_command('WAV:UNIT', unit.value if unit is not None else None)
            if result is not None:
                return self.Unit(int(result))

        def min_wavelength(self):
            return self.device.property_command("WAV:MIN")

        def max_wavelength(self):
            return self.device.property_command("WAV:MAX")

        def wavelength(self, val: float = None):
            return self.device.property_command('WAV', val, 4)

        def min_frequency(self):
            return self.device.property_command("WAV:FREQ:MIN")

        def max_frequency(self):
            return self.device.property_command("WAV:FREQ:MAX")

        def frequency(self, val: float = None):
            return self.device.property_command('FREQ', val, 5)

        def fine_tuning(self, val=None):
            return self.device.property_command('WAV:FIN', val)

        def disable_fine_tuning(self):
            return self.device.command('WAV:FIN:DIS')

    class Sweep:
        class Play(Enum):
            STOP = 0
            START = 1
            PAUSE = 2
            RESUME = 3

        class Status(Enum):
            STOP = 0
            OPERATION = 1
            PAUSE = 2
            TRIGGER_STANDBY = 3
            RETURNING_TO_START = 4

        class Mode(Enum):
            STEP_ONE_WAY = 0
            CONTINUOUS_ONE_WAY = 1
            STEP_TWO_WAY = 2
            CONTINUOUS_TWO_WAY = 3

        def __init__(self, device):
            self.device: TSL550 = device

        def wavelength(self, start, stop, speed, mode: Mode = Mode.CONTINUOUS_ONE_WAY,
                       number=1, delay=0):
            r"""
            Conduct a sweep between two wavelengths. This method goes from
            the start wavelength to the stop wavelength (units:
            manometres). The sweep is then repeated the number of times
            set in the number parameter.

            If delay (units: seconds) is specified, there is a pause of
            that duration between each sweep.

            If the parameter continuous is False, then the sweep will be
            conducted in steps of fixed size as set by the step_size
            parameter (units: nanometres).

            In continuous mode, the duration is interpreted as the time
            for one sweep. In stepwise mode, it is used as the dwell time
            for each step. In both cases it has units of seconds and
            should be specified in 100 microsecond intervals.

            If the twoway parameter is True then one sweep is considered
            to be going from the start wavelength to the stop wavelength
            and then back to the start; if it is False then one sweep
            consists only of going from the start to the top, and the
            laser will simply jump back to the start wavelength at the
            start of the next sweep.

            If the trigger parameter is False then the sweep will execute
            immediately. If it is true, the laser will wait for an
            external trigger before starting.

            To illustrate the different sweep modes:

                Continuous, one-way    Continuous, two-way
                    /   /                  /\    /\      <-- stop frequency
                   /   /                  /  \  /  \
                  /   /                  /    \/    \    <-- start frequency
                  <-> duration           <----> duration

                Stepwise, one-way      Stepwise, two-way
                        __|      __|              _||_        _||_      <-- stop frequency
                     __|      __|               _|    |_    _|    |_ } step size
                  __|      __|               _|        |__|        |_  <-- start frequency
                  <-> duration               <> duration

                Continuous, one-way, delay    Continuous, two-way, delay
                    /     /                       /\       /\
                   /     /                       /  \     /  \
                  /  ___/                       /    \___/    \
                     <-> delay                        <-> delay
            """

            # Set start and end wavelengths
            self.start_wavelength(start)
            self.end_wavelength(stop)

            # Set timing
            self.delay(delay)
            if mode == self.Mode.CONTINUOUS_ONE_WAY or mode == self.Mode.CONTINUOUS_TWO_WAY:  # Calculate speed
                self.speed(speed)
            else:
                self.step_time(abs(stop - start) / speed)

            self.set_mode(mode)

            if not self.device.power.status():  # Make sure the laser is on
                self.device.power.on()

            self.cycles(number)
            self.sweep(self.Play.START)

        def sweep(self, val: Play = None):
            result = self.device.property_command("WAV:SWE", val.value if val is not None else None)
            if result is not None:
                return self.Status(int(result))

        def cycles(self, val: int = None):
            return self.device.property_command("WAV:SWE:CYCL", val)

        def stop_immediately(self):
            self.sweep(self.Play.PAUSE)
            self.sweep(self.Play.STOP)

        def set_mode(self, mode: Mode = None):
            result = self.device.property_command('WAV:SWE:MOD', mode.value if mode is not None else None)
            if result is not None:
                return self.Mode(int(result))

        def speed(self, val=None):
            return self.device.property_command('WAV:SWE:SPE', val, 1)

        def start_wavelength(self, val=None):
            return self.device.property_command('WAV:SWE:STAR', val, 4)

        def end_wavelength(self, val=None):
            return self.device.property_command('WAV:SWE:STOP', val, 4)

        def step_wavelength(self, val=None):
            return self.device.property_command('WAV:SWE:STEP', val, 4)

        def delay(self, val=None):
            return self.device.property_command('WAV:SWE:DEL', val, 1)

        def step_time(self, val=None):
            return self.device.property_command('WAV:SWE:DWEL', val, 1)

    def __init__(self):
        super().__init__(identifier="visa://viv.ypl.local/GPIB0::1::INSTR", device_name='TSL-550')
        self.input_trigger = TSL550.InputTrigger(self)
        self.output_trigger = TSL550.OutputTrigger(self)
        self.power = TSL550.Power(self)
        self.laser = TSL550.Laser(self)
        self.sweep = TSL550.Sweep(self)

        if self.device is None:
            print("Error: Laser not found")
            raise Exception("Laser not found")


if __name__ == '__main__':
    print(TSL550().identification())
