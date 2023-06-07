from components.daq_data import add_daq
# from components.keith2400 import add_keith
from components.keith2400 import DAQ_sweep
from components.DPUC_Multiplier import DPUC_Homodyne_SimpleMul, DPUC_Homodyne_SimpleMul_Sweep, DPUC_Homodyne_DotProduct
from components.DPUC_Complex_Numbers import DPUC_Complex_Numbers
from components.MOKU import add_moku
from components.laser import add_laser
from components.motors import add_motors

motor_x, motor_y = add_motors()
add_daq()
laser_tsl_550 = add_laser()
moku_osc = add_moku()
# keith2400_a, keith2400_b = add_keith()


