from .input_finder import InputFinder


class PipelineInputFinder(InputFinder):
    """Pipeline Input Finder

    It execute in sequence a list of input finder heuristics where the result of previous heuristic is passed
    as an input to the next heuristic

    Attributes:
        input_finder_class (Union[class, list]): list of input finder classes
        input_finder_params (Union[dict, list]): list of initialization parameters for each input finder class
    """

    def __init__(self,
                 input_finder_class,
                 input_finder_params=None,
                 **kwargs):
        """Initialization
        """

        InputFinder.__init__(self, **kwargs)
        self.input_finder_class = input_finder_class
        self.input_finder_params = input_finder_params

    def solve(self):
        """Execute the heuristic

        Returns:
            list(GAIndividual): list of encoded control inputs
        """

        if not isinstance(self.input_finder_class, list):
            self.input_finder_class = [self.input_finder_class]

        if not isinstance(self.input_finder_params, list):
            self.input_finder_params = [self.input_finder_params] * len(self.input_finder_class)

        control_inputs = []
        if self.last_inputs is not None:
            control_inputs = self.last_inputs

        for (index, finder_class) in enumerate(self.input_finder_class):
            params = {}
            if index < len(self.input_finder_params) and self.input_finder_params[index] is not None:
                params.update(self.input_finder_params[index])

            finder = finder_class(system=self.system,
                                  environment_inputs=self.environment_inputs,
                                  objective=self.objective,
                                  objective_aggregator=self.objective_aggregator,
                                  system_estimator=self.system_estimator,
                                  dominance_func=self.dominance_func,
                                  pool_size=self.pool_size,
                                  last_inputs=control_inputs,
                                  **params)

            control_inputs = finder.solve()

        return control_inputs
