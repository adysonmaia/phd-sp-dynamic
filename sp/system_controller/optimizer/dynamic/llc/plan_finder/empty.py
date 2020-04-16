from .plan_finder import PlanFinder


class EmptyPlanFinder(PlanFinder):
    def solve(self, control_inputs):
        """Find random plans
        Args:
            control_inputs (list(list)): list of control inputs for each stage
        Returns:
            list(Plan): list of plans
        """
        return []

