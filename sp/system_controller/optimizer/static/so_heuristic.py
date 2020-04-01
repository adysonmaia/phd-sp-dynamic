from sp.system_controller.optimizer.optimizer import Optimizer, OptimizerError
from sp.system_controller.optimizer.static.soga import SOGAOperator, indiv_gen
from sp.system_controller.metric.static import deadline


class SOHeuristicOptimizer(Optimizer):
    def __init__(self, version=None):
        Optimizer.__init__(self)
        self.objective = None
        self.version = version

        self._all_versions = {
            "cloud": indiv_gen.create_individual_cloud,
            "net_delay": indiv_gen.create_individual_net_delay,
            "cluster_metoids": indiv_gen.create_individual_cluster_metoids,
            "deadline": indiv_gen.create_individual_deadline,
            "cluster_metoids_sc": indiv_gen.create_individual_cluster_metoids_sc
        }

    def init_params(self):
        if self.version is None:
            self.version = ["net_delay", "deadline"]

        if not isinstance(self.version, list):
            self.version = [self.version]

        if self.objective is None:
            self.objective = deadline.max_deadline_violation

    def solve(self, system, environment_input):
        self.init_params()
        ga_operator = SOGAOperator(system=system,
                                   environment_input=environment_input,
                                   objective=self.objective)
        functions = [self._all_versions[v] for v in self.version]
        individual = indiv_gen.merge_creation_functions(ga_operator, functions)
        solution = ga_operator.decode(individual)
        return solution
