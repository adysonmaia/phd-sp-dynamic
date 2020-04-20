from sp.system_controller.optimizer.optimizer import Optimizer
from sp.system_controller.optimizer.soga import SOGAOperator
from sp.system_controller.optimizer.soga import indiv_gen
from sp.system_controller.metric import deadline
from future.utils import iteritems
import types


class _VersionEnum:
    def __init__(self):
        self.CLOUD = indiv_gen.create_individual_cloud
        self.NET_DELAY = indiv_gen.create_individual_net_delay
        self.CLUSTER_METOIDS = indiv_gen.create_individual_cluster_metoids
        self.CLUSTER_METOIDS_SC = indiv_gen.create_individual_cluster_metoids_sc
        self.DEADLINE = indiv_gen.create_individual_deadline

    def to_dict(self):
        versions = {}
        for (key, value) in iteritems(self.__dict__):
            if isinstance(key, str) and key.isupper() and isinstance(value, types.FunctionType):
                versions[key] = value
        return versions

    def to_list(self):
        return list(self.to_dict().values())


class SOHeuristicOptimizer(Optimizer):
    versions = _VersionEnum()

    def __init__(self, version=None):
        Optimizer.__init__(self)
        self.objective = None
        self.version = version

    def init_params(self):
        if self.version is None:
            self.version = [self.versions.NET_DELAY, self.versions.DEADLINE]

        if not isinstance(self.version, list):
            self.version = [self.version]

        if self.objective is None:
            self.objective = deadline.max_deadline_violation

    def solve(self, system, environment_input):
        self.init_params()
        ga_operator = SOGAOperator(system=system,
                                   environment_input=environment_input,
                                   objective=self.objective)

        individual = indiv_gen.merge_creation_functions(ga_operator, self.version)
        solution = ga_operator.decode(individual)
        return solution
