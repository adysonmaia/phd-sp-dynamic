from .plan_finder import PlanFinder


class ExhaustivePlanFinder(PlanFinder):
    def solve(self, control_inputs):
        """Find random plans
        Args:
            control_inputs (list(list)): list of control inputs for each stage
        Returns:
            list(Plan): list of plans
        """
        sequences = [[]]
        for pool in control_inputs:
            sequences = [i + [j] for i in sequences for j in pool]

        return self.create_plans(sequences)

