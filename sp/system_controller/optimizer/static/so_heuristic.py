from sp.controller.solver import Solver, SolverError, utils
from sp.controller.solver.static.soga import SOChromosome, indiv_gen


class SOHeuristicSolver(Solver):
    def __init__(self):
        Solver.__init__(self)
        self.objective = None
        self.version = None

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

        functions = []
        if isinstance(self.version, list) or isinstance(self.version, tuple):
            functions = [self._versions[v] for v in self.version]
        elif isinstance(self.version, str):
            functions = [self._versions[self.version]]
        else:
            SolverError("Version not found")

        chromosome = SOChromosome(system, objective=self.objective)
        individual = indiv_gen.merge_creation_functions(chromosome, functions)

        allocation = chromosome.decode(individual)
        return utils.alloc_demanded_resources(system, allocation)
