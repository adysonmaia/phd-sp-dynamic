from .plan_finder import PlanFinder


class ExhaustivePlanFinder(PlanFinder):
    def solve(self, control_inputs):
        """Find random plans
        Args:
            control_inputs (list): list of control inputs
        Returns:
            list(Plan): list of plans
        """
        sequences = [[]]
        for _ in range(self.sequence_length):
            for control_input in control_inputs:
                sequences = [seq + [control_input] for seq in sequences]

        return self.create_plans(sequences)

