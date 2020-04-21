from .plan_finder import PlanFinder, Plan
import random


class RandomPlanFinder(PlanFinder):
    def __init__(self, nb_plans=100, **pf_params):
        PlanFinder.__init__(self, **pf_params)
        self.nb_plans = nb_plans

    def solve(self, control_inputs):
        """Find random plans
        Args:
            control_inputs (list): list of control inputs
        Returns:
            list(Plan): list of plans
        """
        sequences = [_gen_rand_sequence(control_inputs, self.sequence_length) for _ in range(self.nb_plans)]
        return self.create_plans(sequences)


def _gen_rand_sequence(control_inputs, sequence_length):
    """Generate a random sequence based on the passed control inputs
    Args:
        control_inputs (list): list of control inputs
        sequence_length (int): sequence's length
    Returns:
        list: a random generated encoded control input
    """
    sequence = [0] * sequence_length
    inputs_length = len(control_inputs)
    for seq_index in range(sequence_length):
        input_index = random.randrange(inputs_length)
        value = control_inputs[input_index]
        sequence[seq_index] = value
    return sequence

