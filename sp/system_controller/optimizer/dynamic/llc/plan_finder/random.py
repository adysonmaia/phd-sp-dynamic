from sp.core.heuristic import nsgaii
from sp.system_controller.optimizer.static import moga
from .plan_finder import PlanFinder, Plan
import random


class RandomPlanFinder(PlanFinder):
    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 control_decoder,
                 system_estimator,
                 pool_size=0,
                 nb_plans=100):
        PlanFinder.__init__(self,
                            system=system,
                            environment_inputs=environment_inputs,
                            objective=objective,
                            objective_aggregator=objective_aggregator,
                            control_decoder=control_decoder,
                            system_estimator=system_estimator,
                            pool_size=pool_size)
        self.nb_plans = nb_plans

    def solve(self, control_inputs):
        """Find random plans
        Args:
            control_inputs (list(list)): list of control inputs for each stage
        Returns:
            list(Plan): list of plans
        """
        sequences = [_gen_rand_sequence(control_inputs) for _ in range(self.nb_plans)]
        return self.create_plans(sequences)


def _gen_rand_sequence(control_inputs):
    """Generate a random sequence based on the passed control inputs for each stage
    Args:
        control_inputs (list(list)): list of control inputs for each stage
    Returns:
        list: a random generated encoded control input
    """
    nb_stages = len(control_inputs)
    sequence = [0] * nb_stages
    for stage in range(nb_stages):
        stage_size = len(control_inputs[stage])
        index = random.randrange(stage_size)
        value = control_inputs[stage][index]
        sequence[stage] = value
    return sequence

