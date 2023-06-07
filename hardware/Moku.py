import matplotlib.pyplot as plt
import time
from moku.instruments import ArbitraryWaveformGenerator
from moku.instruments import Datalogger

# class Moku_FG():
#     def __init__(self):
#         self.Moku_FG = ArbitraryWaveformGenerator('172.28.2.6', force_connect=True)
#
#     def connect(self):
#         return self.Moku_FG.claim_ownership(force_connect=True, ignore_busy=True, persist_state=True)
#
#     def setPWR(self, Channel_ID, Voltage, Current):
#         return self.Moku_FG.set_power_supply(Channel_ID, True, voltage=Voltage, current=Current)
#
#     def resetPWR(self, Channel_ID):
#         self.setPWR(Channel_ID, 0, 0)
#
#     def readPWR(self, Channel_ID, All_Channels=False):
#         if (All_Channels is True):
#             out = self.Moku_FG.get_power_supplies()
#         elif (All_Channels is False):
#             out = self.Moku_FG.get_power_supply(Channel_ID)
#             return out
#
#     def enable_output(self, channel, enable=True, strict=True):
#         params = dict(strict=strict, channel=channel, enable=enable, )
#         return self.session.post(self.awg, self.enable_output, params)
#
#     def disconnect(self):
#         return self.Moku_FG.relinquish_ownership()
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.disconnect()

class Moku_OSC():
    def __init__(self):
        self.Moku_OSC= Datalogger('172.28.2.7', force_connect=True)

    def connect(self):
        return self.Moku_OSC.claim_ownership(force_connect=True, ignore_busy=True, persist_state=True)

    def disconnect(self):
        return self.Moku_OSC.relinquish_ownership()

    def set_acq_mode(self, Mode):
        if Mode in ['Precision', 'Normal', 'PeakDetect']:
            temp_mode = Mode
        else:
            temp_mode = 'Normal'
        return self.Moku_OSC.set_acquisition_mode(mode= temp_mode)

    def set_front(self, ch):
        return self.Moku_OSC.set_frontend(ch, "1MOhm", "DC", "4Vpp")

    def set_samprate(self, fs):
        return self.Moku_OSC.set_samplerate(fs, True)

    def disable(self, ch):
        return self.Moku_OSC.disable_channel(ch, True, True)

    def stop_rec(self):
        return self.Moku_OSC.stop_logging()

    def start_rec(self, t_window, t_delay, file, Comments, Strict):
        return self.Moku_OSC.start_logging(duration= t_window, delay = t_delay, file_name_prefix= file, comments= Comments, strict= Strict)

    def dl(self, Target, File, Path):
        return self.Moku_OSC.download(target= Target, file_name= File, local_path= Path)

    def dele(self, Target, File):
        return self.Moku_OSC.delete(target= Target, file_name= File)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

if __name__ == '__main__':
    # with Moku_FG() as moku_fg:
    #     print(moku_fg.Moku_FG.name())

    with Moku_OSC() as moku_osc:
        print(moku_osc.Moku_OSC.name())
        a = moku_osc.start_rec(10, 0, "testREC", "", True)
        file_name = a["file_name"]
        print('Recording Finished')
        time.sleep(0.2)
        moku_osc.stop_rec()
        moku_osc.dl('ssd', file_name, "C:/users/sar247/Desktop/testREC.li")
        moku_osc.dele('ssd', file_name)