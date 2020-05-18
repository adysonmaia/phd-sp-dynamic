from .plan_finder import PlanFinder, GAIndividual


class EmptyPlanFinder(PlanFinder):
    """Empty Plan Finder
    """

    def solve(self, control_inputs):
        """Find no plans

        Args:
            control_inputs (list(GAIndividual)): list of control inputs
        Returns:
            list(Plan): list of plans
        """
        return []

