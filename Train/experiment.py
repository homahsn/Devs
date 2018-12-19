from pypdevs.simulator import Simulator

from model import TrainNetwork


def terminate_whenStateIsReached(clock, model):
    return len(model.TrainNetwork.Collector.trains) == len(model.TrainNetwork.Generator.trains)


total_railway_length = 15000
num_of_segments = 10
num_of_trains = 100
max_velocity = 150
acceleration = 15
iat = 10
trainNetwork = TrainNetwork("TrainNetwork", num_of_trains, max_velocity, num_of_segments,
                            total_railway_length, acceleration, iat)
sim = Simulator(trainNetwork)
sim.setTerminationCondition(terminate_whenStateIsReached)
sim.classicDEVS()
sim.simulate()
