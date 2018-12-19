from pypdevs.DEVS import *
from collections import deque
import random
from formulas import *


class Train:

    def __init__(self, id, max_a, dep_time):
        self.id = id
        self.max_a = max_a
        self.dep_time = dep_time

        self.v = 0
        self.x_remaining = 0


class Generator(AtomicDEVS):

    def __init__(self, name, number_of_trains, iat, acceleration):

        AtomicDEVS.__init__(self, name)

        self.trains = deque([])

        for i in range(number_of_trains):
            max_a = random.randint(0, acceleration)
            i_a_t = random.randint(1, iat)
            if len(self.trains) == 0:
                dep_time = 0
            else:
                dep_time = self.trains[-1].dep_time + i_a_t
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
        elif self.state == "Accelerate":
            self.state = "Idle"

        return self.state

    def extTransition(self, inputs):

        train_input = inputs[self.train_in]
        query_receive_ack = inputs[self.query_rack]

        if self.state == "Idle" and train_input is not None:
            self.train = train_input
            self.state = "TrainIn"
        elif query_receive_ack == "Red" and self.state == "Accelerate":
            brake = brake_formula(self.train.v, 1, self.train.x_remaining)
            self.train.v = brake[0]
            self.train.x_remaining -= brake[1]
            self.state = "NextSegLight"
        elif query_receive_ack == "Green" and self.state == "NextSegLight":
            self.state = "Accelerate"

        return self.state

    def timeAdvance(self):

        if self.state == "Idle":
            return float('inf')
        elif self.state == "Accelerate":
            velocity_time = acceleration_formula(self.train.v, 100, self.train.x_remaining, self.train.max_a)
            self.train.v = velocity_time[0]
            return velocity_time[1]
        elif self.state == "NextSegLight":
            return 1

    def outputFnc(self):
        if self.train is not None and self.state != "Idle":
            return "Red"
        else:
            return "Green"


class Collector(AtomicDEVS):
    def __init__(self, name):
        AtomicDEVS.__init__(self, name)
        self.trains = []
        self.query_recv = self.addInPort("Q_recv")
        self.query_sack = self.addOutPort("Q_sack")
        self.train_in = self.addInPort("train_in")

        self.time_advance = 0

        self.state = "Empty"

    def intTransition(self):
        if self.state == "Empty":
           self.state = "TrainIn"
        elif self.state == "TrainIn":
            self.state = "Empty"

        return self.state

    def extTransition(self, inputs):
        self.time_advance += self.elapsed
        train_input = inputs[self.train_in]
        # query_input = inputs[self.query_recv]

        if train_input is not None and isinstance(train_input, Train):
            self.state = "TrainIn"
            self.trains.append(train_input)
        else:
            self.state = self.state

        return self.state

    def timeAdvance(self):

        if self.state == "Wait":
            return float('inf')
        elif self.state == "TrainIn":
            return 0

    # def outputFnc(self):
    #     if self.state == "Wait":


class TrainNetwork(CoupledDEVS):

    def __init__(self, name, num_of_trains, v_max, num_of_tracks, length, acceleration, iat):
        CoupledDEVS.__init__(self, name)

        self.generator = self.addSubModel(Generator("Generator", num_of_trains, iat, acceleration))
        self.segments = []
        for i in range(num_of_tracks):
            self.segments.append(self.addSubModel(RailwaySegment("Railway", v_max, length)))

        self.collector = self.addSubModel(Collector("Collector"))

        self.connectPorts(self.generator.query_send, self.segments[0].query_recv)
        self.connectPorts(self.segments[0].query_sack, self.generator.query_rack)
        self.connectPorts(self.generator.train_out, self.segments[0].train_in)

        for i in range(1, len(self.segments)):
            self.connectPorts(self.segments[i-1].query_send, self.segments[i].query_recv)
            self.connectPorts(self.segments[i].query_sack, self.segments[i-1].query_rack)
            self.connectPorts(self.segments[i-1].train_out, self.segments[i].train_in)

        self.connectPorts(self.segments[-1].query_send, self.collector.query_recv)
        self.connectPorts(self.collector.query_sack, self.segments[-1].query_rack)
        self.connectPorts(self.segments[-1].train_out, self.collector.train_in)
