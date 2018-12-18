from pypdevs.DEVS import *

from collections import deque

import random


class Train:

    def __init__(self, id, max_a, dep_time):
        self.__id = id
        self.__max_a = max_a
        self.__dep_time = dep_time


class Generator(AtomicDEVS):

    def __init__(self, name, number_of_trains, iat = (), max_a = ()):

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

        self.elapsed = 0

        self.state = "Wait"  # Initial state

    def intTransition(self):

        self.elapsed += self.timeAdvance()

        if self.state == "Wait":
            self.set("Send")
        elif self.state == "Send":
            self.set("Poll")
        elif self.state == "Poll":
            self.set("Send")
        elif self.state == "Allowed":
            self.set("Wait")

    def extTransition(self, inputs):
        ext_input = inputs[self.query_rack.name]

        if ext_input == "Green":
            self.set("Allowed")
        else:
            self.set(self.state)

    def timeAdvance(self):
        if self.state == "Wait":
            if len(self.trains) == 0:
                wait = float('inf')
            else:
                wait = max(0, self.trains[-1].dep_time - self.elapsed)
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

