from pypdevs.simulator import Simulator

from model import TrainNetwork

trainNetwork = TrainNetwork(name="TrainNetwork", num_of_tracks=10, length=15000, num_of_trains=100, iat=(1,10), v_max=150)
sim = Simulator(trainNetwork)


def terminate_whenStateIsReached(clock, model):
    return len(model.TrainNetwork.Collector.trains) == len(model.TrainNetwork.Generator.trains)

sim.setTerminationCondition(terminate_whenStateIsReached)

sim.setTerminationTime(500.0)


sim.classicDEVS()
sim.simulate()
