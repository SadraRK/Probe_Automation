import re

from hardware.visa_interface import VisaInterface


class KEITH2400_A(VisaInterface):
    def __init__(self):
        super().__init__(identifier="GPIB0::2::INSTR", device_name='KEITHLEY INSTRUMENTS INC.,MODEL 2400')
        if self.device is None:
            print("Error: KEITHLEY_A 2400 not found")
            raise Exception("KEITHLEY_A 2400 not found")
        self.write('*RST')

    def get_resistance(self) -> float:
        p = self.property_command('READ')
        out = float(re.split(',', p)[2])
        return out

    def set_compliance_voltage(self, val: float):
        self.property_command('SENS:VOLT:PROT:LEV', val)

    def on(self):
        self.property_command('OUTP:STAT', 'ON')

    def off(self):
        self.property_command('OUTP:STAT', 'OFF')

class KEITH2400_B(VisaInterface):
    def __init__(self):
        super().__init__(identifier="GPIB0::3::INSTR", device_name='KEITHLEY INSTRUMENTS INC.,MODEL 2400')
        if self.device is None:
            print("Error: KEITHLEY_B 2400 not found")
            raise Exception("KEITHLEY_B 2400 not found")
        self.write('*RST')

    def get_resistance(self) -> float:
        p = self.property_command('READ')
        out = float(re.split(',', p)[2])
        return out

    def set_compliance_voltage(self, val: float):
        self.property_command('SENS:VOLT:PROT:LEV', val)

    def on(self):
        self.property_command('OUTP:STAT', 'ON')

    def off(self):
        self.property_command('OUTP:STAT', 'OFF')

# if __name__ == '__main__':
    # keith_a = KEITH2400_A()
    # keith_b = KEITH2400_B()
    # print(keith_a.identification())
    # print(keith_b.identification())
