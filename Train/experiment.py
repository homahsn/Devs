from pypdevs.simulator import Simulator

from model import TrainNetwork


def terminate_whenStateIsReached(clock, model):
    return len(model.collector.trains) == 10


total_railway_length = 100
num_of_segments = 1
num_of_trains = 1
max_velocity = 150
acceleration = 15
iat = 10
trainNetwork = TrainNetwork("TrainNetwork", num_of_trains, max_velocity, num_of_segments,
                            total_railway_length, acceleration, iat)
sim = Simulator(trainNetwork)
sim.setTerminationCondition(terminate_whenStateIsReached)
sim.setClassicDEVS(True)
sim.setVerbose(None)
sim.setTerminationTime(20.0)
sim.simulate()
