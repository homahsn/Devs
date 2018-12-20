import random

from formulas import *
from pypdevs.DEVS import *


class Train:

    def __init__(self, id, a_max, dep_time):
        self.id = id
        self.a_max = a_max
        self.dep_time = dep_time

        self.v = 0
        self.x_remaining = 0


class Generator(AtomicDEVS):

    def __init__(self, name, number_of_trains, acceleration, iat):
        AtomicDEVS.__init__(self, name)

        self.generated_trains = []
        self.number_of_trains = number_of_trains

        for i in range(number_of_trains):
            max_a = random.randint(1, acceleration)
            i_a_t = random.randint(1, iat)
            if len(self.generated_trains) == 0:
                dep_time = 0
            else:
                dep_time = self.generated_trains[0].dep_time + i_a_t

            train = Train(i, max_a, dep_time)
            self.generated_trains.insert(0, train)

        self.time_advance = 0
        self.state = "Wait"  # Init

        self.query_send = self.addOutPort("Q_send")
        self.query_rack = self.addInPort("Q_rack")
        self.train_out = self.addOutPort("train_out")

    def intTransition(self):

        self.time_advance += self.timeAdvance()

        if self.state == "Wait":
            self.state = "Send"
            return self.state
        elif self.state == "Send":
            return "RequestAccess"
        elif self.state == "RequestAccess":
            self.state = "Send"
            return self.state
        elif self.state == "Allowed":
            self.state = "Wait"
            return self.state

    def extTransition(self, inputs):
        received_ack = inputs.get(self.query_rack)

        if received_ack == "GREEN":
            self.state = "Allowed"
            return self.state
        else:
            return self.state

    def timeAdvance(self):
        if self.state == "RequestAccess":
            return 1
        elif self.state == "Wait":
            if len(self.generated_trains) > 0:
                wait = max(0, self.generated_trains[0].dep_time - self.time_advance)
            else:
                wait = float('inf')
            return wait
        elif self.state == "Allowed":
            return 0
        elif self.state == "Send":
            return 0

    def outputFnc(self):
        if self.state == "Allowed":
            return {self.train_out: self.generated_trains.pop()}
        elif self.state == "Send":
            return {self.query_send: "QUERY"}
        elif self.state == "RequestAccess" or self.state == "Wait":
            return {}


class RailwaySegment(AtomicDEVS):

    def __init__(self, name, v_max, length):

        AtomicDEVS.__init__(self, name)

        self.state = "Idle"  # Init

        self.query_recv = self.addInPort("Q_recv")
        self.query_send = self.addOutPort("Q_send")
        self.query_sack = self.addOutPort("Q_sack")
        self.query_rack = self.addInPort("Q_rack")
        self.train_in = self.addInPort("train_in")
        self.train_out = self.addOutPort("train_out")

        self.time_advance = 0
        self.v_max = v_max
        self.length = length
        self.train = None

    def intTransition(self):
        self.time_advance += self.timeAdvance()
        if self.state == "Idle":
            self.state = "Allow"
            return self.state
        elif self.state == "Allow":
            self.state = "Allow"
            return self.state
        elif self.state == "TrainIn":
            self.state = "Accelerate"
            return self.state
        elif self.state == "Accelerate":
            self.state = "NextSegment"
            return self.state
        elif self.state == "NextSegment":
            self.state = "RequestAccess"
            return self.state
        elif self.state == "RequestAccess":
            return self.state
        elif self.state == "ExitSeg":
            self.state = "Idle"
            return self.state

    def extTransition(self, inputs):
        query_rack = inputs.get(self.query_rack)
        incoming_train = inputs.get(self.train_in)

        if self.state == "Idle":
            self.state = "Allow"
            return self.state
        elif self.state == "Allow" and isinstance(incoming_train, Train):
            self.train = incoming_train
            self.state = "TrainIn"
            return self.state
        elif query_rack == "RED" and self.state == "RequestAccess":
            brake = brake_formula(self.train.v, 1, self.train.x_remaining)
            self.train.v = brake[0]
            self.train.x_remaining -= brake[1]
            self.state = "NextSegment"
            return self.state
        elif query_rack == "GREEN" and self.state == "RequestAccess":
            self.state = "ExitSeg"
            return self.state
        else:
            return self.state

    def timeAdvance(self):

        if self.state == "Idle" or self.state == "RequestAccess":
            return float('inf')
        elif self.state == "Accelerate":
            accel = acceleration_formula(self.train.v, self.v_max, self.train.x_remaining - 1000, self.train.a_max)
            self.train.v = accel[0]
            self.train.x_remaining = self.length - 1000
            return accel[1]
        elif self.state == "ExitSeg":
            accel = acceleration_formula(self.train.v, self.v_max, self.train.x_remaining, self.train.a_max)
            self.train.v = accel[0]
            self.train.x_remaining = self.length - 1000
            return accel[1]
        elif self.state == "TrainIn":
            return 0
        elif self.state == "NextSegment":
            return 1
        elif self.state == "Allow":
            return 0

    def outputFnc(self):
        if self.state == "TrainIn":
            return {self.query_sack: "RED"}
        elif self.state == "ExitSeg":
            return {self.query_sack: "GREEN", self.train_out: self.train}
        elif self.state == "NextSegment":
            return {self.query_send: "QUERY"}
        elif self.state == "Idle":
            return {self.query_sack: "GREEN"}
        elif self.state == "Allow":
            return {self.query_sack: "GREEN"}
        else:
            return {}


class Collector(AtomicDEVS):

    def __init__(self, name):
        AtomicDEVS.__init__(self, name)

        self.trains = []
        self.time_advance = 0
        self.state = "Idle"

        self.query_recv = self.addInPort("Q_recv")
        self.query_sack = self.addOutPort("Q_sack")
        self.train_in = self.addInPort("train_in")

    def intTransition(self):
        self.time_advance += self.timeAdvance()
        if self.state == "Idle":
            self.state = "TrainIn"
            return self.state
        elif self.state == "TrainIn":
            self.state = "Idle"
            return self.state
        else:
            return self.state

    def extTransition(self, inputs):

        if self.state == "Idle" and isinstance(inputs.get(self.train_in), Train):
            self.trains.append(inputs.get(self.train_in))
            self.state = "TrainIn"
            return self.state
        else:
            return self.state

    def timeAdvance(self):
        if self.state == "Idle":
            return float('inf')
        else:
            return 0

    def outputFnc(self):
        return {self.query_sack: "GREEN"}


class TrainNetwork(CoupledDEVS):

    def __init__(self, name, num_of_trains, v_max, num_of_tracks, length, acceleration, iat):
        CoupledDEVS.__init__(self, name)

        self.generator = self.addSubModel(Generator("Generator", num_of_trains, iat, acceleration))
        self.segments = []
        for i in range(num_of_tracks):
            segment_length = length / num_of_tracks
            self.segments.append(self.addSubModel(RailwaySegment("Railway", v_max, segment_length)))

        self.connectPorts(self.generator.query_send, self.segments[0].query_recv)
        self.connectPorts(self.segments[0].query_sack, self.generator.query_rack)
        self.connectPorts(self.generator.train_out, self.segments[0].train_in)

        for i in range(1, len(self.segments)):
            self.connectPorts(self.segments[i-1].query_send, self.segments[i].query_recv)
            self.connectPorts(self.segments[i].query_sack, self.segments[i-1].query_rack)
            self.connectPorts(self.segments[i-1].train_out, self.segments[i].train_in)

        self.collector = self.addSubModel(Collector("Collector"))

        self.connectPorts(self.segments[-1].query_send, self.collector.query_recv)
        self.connectPorts(self.collector.query_sack, self.segments[-1].query_rack)
        self.connectPorts(self.segments[-1].train_out, self.collector.train_in)
