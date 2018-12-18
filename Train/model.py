from pypdevs.DEVS import *
from collections import deque
import random
from formulas import *

class Train:

    def __init__(self, id, max_a, dep_time):
        self.__id = id
        self.__max_a = max_a
        self.__dep_time = dep_time

        self.v = 0
        self.x_remaining = 0

class Generator(AtomicDEVS):

    def __init__(self, name, number_of_trains, iat=(), max_a=()):

        AtomicDEVS.__init__(self, name)

        self.trains = deque([])

        for i in range(number_of_trains):
            max_a = random.randint(max_a[0], max_a[1])
            iat = random.randint(iat[0], iat[1])
            if len(self.trains) == 0:
                dep_time = 0
            else:
                dep_time = self.trains[-1].dep_time + iat
            self.trains.append(Train(i, max_a, dep_time))

        self.query_send = self.addOutPort("Q_send")
        self.query_rack = self.addInPort("Q_rack")
        self.train_out = self.addOutPort("train_out")

        self.time_advance = 0

        self.state = "Wait"  # Initial state

    def intTransition(self):

        self.time_advance += self.timeAdvance()

        if self.state == "Wait":
            self.state = "Send"
        elif self.state == "Send":
            self.state = "Poll"
        elif self.state == "Poll":
            self.state = "Send"
        elif self.state == "Allowed":
            self.state = "Wait"

        return self.state

    def extTransition(self, inputs):
        ext_input = inputs[self.query_rack]

        if ext_input == "Green":
            self.state = "Allowed"
        else:
            self.state = self.state

        return self.state

    def timeAdvance(self):
        if self.state == "Wait":
            if len(self.trains) == 0:
                wait = float('inf')
            else:
                wait = max(0, self.trains[-1].dep_time - self.time_advance)
            return wait
        elif self.state == "Allowed":
            return 0
        elif self.state == "Send":
            return 0
        elif self.state == "Poll":
            return 1

    def outputFnc(self):
        if self.state == "Send":
            return {self.query_send: "QUERY"}
        elif self.state == "Poll" or self.state == "Wait":
            return {}
        elif self.state == "Allowed":
            return {self.train_out: self.trains.popleft()}

    def set(self, state):
        self.state = state


class RailwaySegment(AtomicDEVS):

    def __init__(self, name, v_max, length):

        AtomicDEVS.__init__(self, name)

        self.query_recv = self.addInPort("Q_recv")
        self.query_sack = self.addOutPort("Q_sack")
        self.query_send = self.addOutPort("Q_send")
        self.query_rack = self.addInPort("Q_rack")
        self.train_in = self.addInPort("train_in")
        self.train_out = self.addOutPort("train_out")

        self.state = "Idle"
        self.length = length
        self.train = None
        self.v_max = v_max


    def intTransition(self):

        if self.state == "Idle":
            self.state = "TrainIn"
        elif self.state == "TrainIn":
            self.state = "Accelerate"
        elif self.state == "Accelerate":
            self.state = "NextSegLight"

        return self.state


    def extTransition(self, inputs):

        train_input = inputs[self.train_in]
        query_receive_ack = inputs[self.query_rack]

        if self.state == "Idle" and train_input is not None:
            self.train = train_input
            return "TrainIn"
        elif  query_receive_ack == "Red" and self.state == "Accelerate":
            brake = brake_formula(self.train.v, 1, self.train.x_remaining)
            self.train.v = brake[0]
            self.train.x_remaining -= brake[1]
            return "NextSegLight"


    def timeAdvance(self):

    def outputFnc(self):
        if self.train is None and self.state == "Idle":
            return "Red"
        else:
            return "Green"

