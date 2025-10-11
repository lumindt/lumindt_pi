delay_EL = 300
delay_FC = 60
CAP_B = 30
CAP_L = 200

PARAM = {
    'E_IN': -2.4,
    'E+': -3.0,
    'E-': -1.8,
    'B_IN': -15,
    'B_OUT': 15,
    'F+': 2.0,
    'F-': 1.5,
    'P_E': 20,
    'P_F': 10,
    'BT_LOW': 0.05,
    'BT_HIGH': 0.95,
    'L1_LOW': 0.05,
    'L1_HIGH': 0.95}

# 8 MODBUS IP addresses of electrolyzers
ELECTROLYZER_IPS = ['10.1.10.6', '10.1.10.231']

DRYER_MIN_THRESHOLD = 10 #BAR #TODO
DRYER_MAX_THRESHOLD = 15 #BAR #TODO

AWS_URL = "https://9s1w5ka37e.execute-api.us-west-2.amazonaws.com/default/storeSensorData"
AWS_REGION = 'us-west-2'

#fuel cell phase dictionary
PHASE_DICTIONARY = {
    1: 'Start',
    2: 'Run',
    3: 'Fault',
    4: 'Standby',
    5: 'Shutting Down',
    6: 'Emergency Stop',
    7: 'Self-Test'
}


DRYER_STATES = {
    257: 'WAITING FOR POWER',
    263: 'WAITING FOR PRESSURE',
    259: 'STOPPED BY USER',
    260: 'STARTING',
    262: 'STANDBY',
    265: 'IDLE',
    513: 'DRYING 0',
    514: 'COOLING 0',
    515: 'SWITCHING 0',
    516: 'PRESSURIZING 0',
    517: 'FINALIZING 0',
    769: 'DRYING 1',
    770: 'COOLING 1',
    771: 'SWITCHING 1',
    772: 'PRESSURIZING 1',
    773: 'FINALIZING 1',
    1281: 'ERROR',
    1537: 'BYPASS',
    1793: 'BYPASS 1',
    2049: 'BYPASS 2',
    2305: 'MAINTENANCE',
    2561: 'EXPERT',
    2817: 'FSR WAIT BEGIN',
    2818: 'FSR WAIT CONFIRM',
    2819: 'FSR WAIT END',
    2820: 'FSR DECLINED',
    3073: 'IDCN WAIT START',
    3074: 'IDCN WAIT CONFIRM',
    3075: 'IDCN BEGIN',
    3076: 'IDCN COMMIT',
    3077: 'IDCN COMMIT ACK',
    3078: 'IDCN WAIT SYNCED',
    3079: 'IDCN SYNCED',
    3080: 'IDCN DECLINED',
    3081: 'IDCN CANCEL',
    3328: 'OTA'
}