import os

def clamp(min, x, max):
    return sorted([min, x, max])[1]

def dynamics(controller):
        controller.P_FC = controller.INP_F

        for i, e in enumerate(controller.VAL_E):
            if controller.INP_E[i] != 0:
                if e >= 0.6:
                    controller.VAL_E[i] = controller.INP_E[i]
                else:
                    controller.VAL_E[i] = 0.6 * (controller.delay_EL - controller.count_EL[i]) / controller.delay_EL
            else:
                controller.VAL_E[i] = 0
            controller.count_EL[i] -= 1 if controller.count_EL[i] > 0 else 0
        controller.P_EL = sum(controller.VAL_E) * controller.PARAM['E_IN']

        controller.P_BT = controller.INP_B

        controller.SOC_B = controller.SOC_B - controller.P_BT * controller.TIME / controller.CAP_B
        controller.SOC_L = controller.SOC_L - (controller.P_EL / 4 + controller.P_FC) * controller.TIME / controller.CAP_L

        pert = 0
        controller.GRID = controller.DIST - controller.P_FC - controller.P_EL - controller.P_BT + pert
        controller.GRID_B += controller.GRID * controller.TIME if controller.GRID > 0 else 0
        controller.GRID_S -= controller.GRID * controller.TIME if controller.GRID < 0 else 0
    
def canup_stm():
     # Set up the CAN bus at start
    os.system("sudo ip link set can0 down") # bring can0 down for fresh reboot
    os.system("sudo ip link set can0 type can bitrate 125000") # set can0 to 125kbps
    os.system("sudo ip link set can0 up") # bring can0 up

def canup_fuel_cell():
    os.system("sudo ip link set can1 down") # bring can0 down for fresh reboot
    os.system("sudo ip link set can1 type can bitrate 250000") # set can1 to 250kbps
    os.system("sudo ip link set can1 up") # bring can1 up

def map_range(value, in_min=1.44, in_max=2.4, out_min=60, out_max=100): # map the range of the fuel cell voltage to the range of the fuel cell power
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min