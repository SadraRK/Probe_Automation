from asyncio import sleep
from typing import Callable

import pyvisa


def get_visa_manager(backend=None):
    if backend is None:
        rm = pyvisa.ResourceManager()
    else:
        rm = pyvisa.ResourceManager(backend)
    return rm


def default_visa_open_function(name, backend=None):
    return get_visa_manager(backend=backend).open_resource(name)


def try_idn_on(device_uri, initialization=None, backend=None):
    try:
        with default_visa_open_function(device_uri, backend=backend) as device:
            if initialization is not None:
                initialization(device)

            result = device.query('*IDN?')
        return result
    except Exception:
        pass


def list_visa_devices(initialization=None, backend=None):
    results = {}
    rm = get_visa_manager(backend)

    for i in list(rm.list_resources()):
        results[i] = try_idn_on(i, initialization=initialization, backend=backend)

    return results


def find_visa_device(device_name=None, identifier=None, initialization=None, backend=None):
    rm = get_visa_manager(backend=backend)
    list_resources = list(rm.list_resources())
    result = None
    for i in list_resources:
        if identifier is not None:
            if identifier.lower() in i.lower():
                result = i
            else:
                continue
        if device_name is not None:
            idn = try_idn_on(i, initialization=initialization, backend=backend)
            if idn is not None and device_name.lower() in idn.lower():
                result = i
                break

    return result


class VisaInterface:
    def __init__(self, device_name=None, identifier=None, backend=None):
        if device_name is None and identifier is None:
            self.device = None
            self.device_uri = None
            self.termination = None
        else:
            self.set_device_by(device_name=device_name, identifier=identifier, backend=backend)

    def set_device_by(self, device_name=None, identifier=None, backend=None):
        if device_name is None and identifier is None:
            raise ValueError("Both device_name and identifier can not be None")

        self.device_uri = find_visa_device(device_name=device_name, identifier=identifier,
                                           initialization=self.addition_initialization,
                                           backend=backend)
        if self.device_uri is None:
            raise Exception(f"Device not found: {device_name=}, {identifier=}")

        self.device = default_visa_open_function(name=self.device_uri, backend=backend)
        self.addition_initialization(self.device)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.device.close()

    def addition_initialization(self, device):
        pass

    def write(self, command: str):
        self.device.write(command)

    def read(self) -> str:
        return self.device.read()

    def query(self, command: str) -> str:
        return self.device.query(command).strip()

    def ask(self, command: str) -> str:
        return self.query(':' + command + '?')

    def command(self, command: str, value=None):
        if value is None:
            self.write(':' + command)
        else:
            self.write(':' + command + ' ' + str(value))

    def sync_command(self, command: str, value=None):
        self.command(command, value)
        self.wait_for_completion()

    def property_command(self, command: str, val: object = None, round_to: object = None) -> object:
        if val is None:
            response = self.ask(command)
            if response is None or response == "None":
                return None
            elif type(response) is str:
                try:
                    return float(response)
                except:
                    return response
            else:
                return response
        else:
            if round_to is not None:
                val = round(val, round_to)
            self.command(command, val)

    def identification(self):
        return self.query('*IDN?')

    def operation_completion(self):
        return self.query('*OPC?') == '1' and self.ask("WAV:SWE") == '0'

    def is_busy(self):
        return not self.operation_completion()

    async def wait_for_completion(self, timeout: float = 30.0):
        step = 0.5
        await sleep(step)
        for i in range(0, int(timeout / step)):
            if self.operation_completion():
                break
            await sleep(step)

    def reboot(self):
        self.command("SPEC:REB")

    def error(self):
        return self.ask("SYST:ERR")

    def version(self):
        return self.ask("SYST:VERS")

    def is_working(self):
        return not self.operation_completion()


if __name__ == '__main__':
    print(list_visa_devices())
    print(list_visa_devices(backend="@py"))
