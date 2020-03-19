from sp.core.model import Scenario
from sp.simulator import Simulator
from sp.system_controller.optimizer.dynamic import LLCOptimizer
from sp.system_controller.optimizer.static import SOGAOptimizer
from datetime import datetime
import json


def main():
    # Read input
    filename = 'input/san_francisco/scenario.json'
    scenario = None
    with open(filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)

    # Set simulation time
    start_time = datetime(2008, 5, 24, 0, 0, 0).timestamp()
    stop_time = datetime(2008, 5, 24, 23, 59, 59).timestamp()
    step_time = 10 * 60  # seconds or 10 min

    # Set optimizer solution
    opt = LLCOptimizer()
    opt.prediction_window = 3
    opt.max_iterations = 5
    # opt = SOGAOptimizer()

    # Set simulation parameters
    sim = Simulator(scenario=scenario)
    sim.set_time(stop=stop_time, start=start_time, step=step_time)
    sim.set_optimizer(opt)

    # Run simulation
    sim.run()


if __name__ == '__main__':
    main()