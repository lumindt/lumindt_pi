from transitions import Machine, MachineError
import time
import board as board
import os
import sys
from utils.relay import RelayBoard, RelayControl

class FSM:
    def __init__(self):
        transitions = [
            {'trigger': 'stop', 'source': '*', 'dest': 'standby'},
            {'trigger': 'end', 'source': 'standby', 'dest': 'clean'},
            {'trigger': 'fill', 'source': ['standby', 'desorb'], 'dest': 'absorb'},
            {'trigger': 'empty', 'source': ['standby', 'absorb'], 'dest': 'desorb'},
        ]

        self.machine = Machine(
            model=self,
            states=[
            'standby',
            'absorb',
            'desorb',
            'clean',
            ],
            transitions=transitions,
            initial='standby'
        )

        relay_board = RelayBoard()

        self.svi = RelayControl(relay_board=relay_board,relay='R4')
        self.svo = RelayControl(relay_board=relay_board,relay='R3')

    
    def on_enter_standby(self):
        self.flow_none()

    def on_enter_absorb(self):
        self.flow_in()

    def on_enter_desorb(self):
        self.flow_out()

    def flow_in(self):
        time.sleep(0.2)
        self.svo.off()
        time.sleep(1)
        self.svi.on()

    def flow_out(self):
        time.sleep(0.2)
        self.svi.off()
        time.sleep(1)
        self.svo.on()

    def flow_none(self):
        time.sleep(0.2)
        self.svo.off()
        self.svi.off()

if __name__ == '__main__':
    cycler = FSM()

    cycler.svi.off()
    cycler.svo.off()
