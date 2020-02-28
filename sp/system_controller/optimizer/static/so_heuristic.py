from sp.system_controller.optimizer import Optimizer, OptimizerError
from sp.system_controller.optimizer.static.soga import SOChromosome, indiv_gen
from sp.system_controller.metric.static import deadline


class SOHeuristicOptimizer(Optimizer):
    def __init__(self, version=None):
        Optimizer.__init__(self)
        self.objective = None
        self.version = version

        self._versions = {
            "cloud": indiv_gen.create_individual_cloud,
            "net_delay": indiv_gen.create_individual_net_delay,
            "cluster_metoids": indiv_gen.create_individual_cluster_metoids,
            "deadline": indiv_gen.create_individual_deadline,
            "cluster_metoids_sc": indiv_gen.create_individual_cluster_metoids_sc
        }

    def solve(self, system):
        if self.version is None:
            self.version = ["net_delay", "deadline"]

        if self.objective is None:
            self.objective = deadline.max_deadline_violation

        functions = []
        if isinstance(self.version, list) or isinstance(self.version, tuple):
            functions = [self._versions[v] for v in self.version]
        elif isinstance(self.version, str):
            functions = [self._versions[self.version]]
        else:
            OptimizerError("Version not found")

        chromosome = SOChromosome(system, objective=self.objective)
        individual = indiv_gen.merge_creation_functions(chromosome, functions)

        solution = chromosome.decode(individual)
        return solution
