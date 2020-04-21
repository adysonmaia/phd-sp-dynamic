from sp.system_controller.optimizer.moga import MOGAOperator, indiv_gen, preferred_dominates
from sp.system_controller.estimator.system import DefaultSystemEstimator
from . import plan_finder as pf
from . import input_finder as cif

_PF_PARAMS = {
    pf.GAPlanFinder: {
        "nb_generations": 100,
        "population_size": 100,
        "elite_proportion": 0.1,
        "mutant_proportion": 0.1,
        "elite_probability": 0.6,
        "stop_threshold": 0.10,
    },
    pf.BeamPlanFinder: {
        "beam_width": 10,
        "prune": True,
    },
    pf.RandomPlanFinder: {
        "nb_plans": 100
    }
}

_CIF_PARAMS = {
    cif.MGAInputFinder: {
        "nb_generations": 100,
        "population_size": 100,
        "elite_proportion": 0.1,
        "mutant_proportion": 0.1,
        "elite_probability": 0.6,
        "stop_threshold": 0.10,
    },
    cif.SSGAInputFinder: {
        "nb_generations": 100,
        "population_size": 100,
        "elite_proportion": 0.1,
        "mutant_proportion": 0.1,
        "elite_probability": 0.6,
        "stop_threshold": 0.10,
    },
    cif.SGAInputFinder: {
        "nb_generations": 100,
        "population_size": 100,
        "elite_proportion": 0.1,
        "mutant_proportion": 0.1,
        "elite_probability": 0.6,
        "stop_threshold": 0.10,
    }
}


class TwoStep:
    def __init__(self,
                 system,
                 environment_input,
                 objective,
                 prediction_window=1,
                 use_heuristic=True,
                 system_estimator=None,
                 environment_predictor=None,
                 objective_aggregator=None,
                 plan_finder_class=None,
                 plan_finder_params=None,
                 input_finder_class=None,
                 input_finder_params=None,
                 dominance_func=None,
                 last_population=None,
                 pool_size=0):

        self.use_heuristic = use_heuristic
        self.prediction_window = prediction_window
        self.sequence_length = 1 + prediction_window
        self.system = system
        self.system_estimator = system_estimator
        self.environment_input = environment_input
        self.environment_predictor = environment_predictor
        self.objective = objective
        self.objective_aggregator = objective_aggregator
        self.dominance_func = dominance_func
        self.pool_size = pool_size
        self.plan_finder_class = plan_finder_class
        self.plan_finder_params = plan_finder_params
        self.input_finder_class = input_finder_class
        self.input_finder_params = input_finder_params
        self.last_population = last_population

        self._env_inputs = None
        self._plan_finder = None
        self._input_finder = None

    def __del__(self):
        """Finalizer
        """
        try:
            self.clear_params()
        except AttributeError:
            pass

    def clear_params(self):
        self._clear_env_inputs()
        self._clear_plan_finder()
        self._clear_input_finder()

    def init_params(self):
        if self.dominance_func is None:
            self.dominance_func = preferred_dominates

        if self.objective_aggregator is None:
            self.objective_aggregator = sum

        if self.system_estimator is None:
            self.system_estimator = DefaultSystemEstimator()

        if self.dominance_func is None:
            self.dominance_func = preferred_dominates

        self._init_env_inputs()
        self._init_plan_finder()
        self._init_input_finder()

    def _init_env_inputs(self):
        self._env_inputs = []
        if self.environment_predictor is not None and self.prediction_window > 0:
            self._env_inputs = [self.environment_input]
            self._env_inputs += self.environment_predictor.predict(self.prediction_window)
        else:
            self._env_inputs = [self.environment_input] * self.sequence_length

    def _clear_env_inputs(self):
        self._env_inputs = None

    def _init_plan_finder(self):
        self._clear_plan_finder()
        if self.plan_finder_class is None:
            return

        params = {}
        if self.plan_finder_class in _PF_PARAMS:
            params.update(_PF_PARAMS[self.plan_finder_class])

        if self.plan_finder_params is not None:
            params.update(self.plan_finder_params)

        self._plan_finder = self.plan_finder_class(system=self.system,
                                                   environment_inputs=self._env_inputs,
                                                   objective=self.objective,
                                                   objective_aggregator=self.objective_aggregator,
                                                   dominance_func=self.dominance_func,
                                                   system_estimator=self.system_estimator,
                                                   pool_size=self.pool_size,
                                                   **params)

    def _clear_plan_finder(self):
        if self._plan_finder is not None:
            self._plan_finder.clear_params()
        self._plan_finder = None

    def _init_input_finder(self):
        self._clear_input_finder()

        params = {}
        if self.input_finder_class is None:
            self.input_finder_class = cif.SSGAInputFinder

        if self.input_finder_class in _CIF_PARAMS:
            params.update(_CIF_PARAMS[self.input_finder_class])

        if self.input_finder_params is not None:
            params.update(self.input_finder_params)

        self._input_finder = self.input_finder_class(system=self.system,
                                                     environment_inputs=self._env_inputs,
                                                     objective=self.objective,
                                                     objective_aggregator=self.objective_aggregator,
                                                     system_estimator=self.system_estimator,
                                                     dominance_func=self.dominance_func,
                                                     pool_size=self.pool_size,
                                                     last_inputs=self.last_population,
                                                     **params)

    def _clear_input_finder(self):
        if self._input_finder is not None:
            self._input_finder.clear_params()
        self._input_finder = None

    def solve(self):
        self.init_params()

        control_inputs = self._exec_step_1()
        population = control_inputs

        if self._plan_finder is not None:
            plans = self._exec_step_2(control_inputs)
            first_slot = 0
            population = [plan[first_slot] for plan in plans]

        self.clear_params()
        return population

    def _exec_step_1(self):
        return self._input_finder.solve()

    def _exec_step_2(self, control_inputs):
        ga_operator = MOGAOperator(system=self.system,
                                   environment_input=self.environment_input,
                                   objective=self.objective,
                                   use_heuristic=True)

        if len(control_inputs) == 0:
            control_inputs = ga_operator.first_population()

        plans = self._plan_finder.solve(control_inputs)

        if self.use_heuristic:
            control_sequences = []
            for indiv in control_inputs:
                sequence = [indiv] * self.sequence_length
                control_sequences.append(sequence)
            for plan in plans:
                indiv = indiv_gen.merge_population(ga_operator, plan.control_sequence)
                sequence = [indiv] * self.sequence_length
                control_sequences.append(sequence)
            plans += self._plan_finder.create_plans(control_sequences)

        plans = self._plan_finder.sort_plans(plans)
        return plans

    def decode_control_input(self, control_input):
        ga_operator = MOGAOperator(system=self.system,
                                   environment_input=self.environment_input,
                                   objective=self.objective,
                                   use_heuristic=True)
        return ga_operator.decode(control_input)
