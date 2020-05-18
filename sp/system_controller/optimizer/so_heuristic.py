from .optimizer import Optimizer
from sp.system_controller.optimizer.soga import SOGAOperator, indiv_gen
from future.utils import iteritems
import types


class _VersionsEnum:
    """Enumeration of all heuristics

    Attributes:
        CLOUD (function): it places all applications in the cloud
        NET_DELAY (function): it prioritizes nodes with lowest network delay from the users
        CLUSTER_METOIDS (function): it prioritizes nodes in the center of a group/cluster of users
        CLUSTER_METOIDS_SC (function): it prioritizes nodes in the center of a group/cluster of users
            and it tries to detect the number of groups/clusters
        DEADLINE (function): it prioritizes applications with shortest deadline
    """

    def __init__(self):
        """Initialization
        """
        self.CLOUD = indiv_gen.create_individual_cloud
        self.NET_DELAY = indiv_gen.create_individual_net_delay
        self.CLUSTER_METOIDS = indiv_gen.create_individual_cluster_metoids
        self.CLUSTER_METOIDS_SC = indiv_gen.create_individual_cluster_metoids_sc
        self.DEADLINE = indiv_gen.create_individual_deadline

    def to_dict(self):
        """Export the enumeration to a dictionary format

        Returns:
            dict: heuristics
        """
        versions = {}
        for (key, value) in iteritems(self.__dict__):
            if isinstance(key, str) and key.isupper() and isinstance(value, types.FunctionType):
                versions[key] = value
        return versions

    def to_list(self):
        """Export the enumeration to a list format

        Returns:
            list: heuristics
        """
        return list(self.to_dict().values())


class SOHeuristicOptimizer(Optimizer):
    """Single-Objective Heuristic Optimizer

    It implements a list of heuristics for the single-objective problem.
    A heuristic can be any function in the :py:mod:`sp.system_controller.optimizer.soga.indiv_gen` module
    or a combination of those functions.

    A shortcut for those functions are listed in the
    :py:attr:`~sp.system_controller.optimizer.so_heuristic.SOHeuristicOptimizer.versions` attribute, such as:

    * :py:attr:`~sp.system_controller.optimizer.so_heuristic.SOHeuristicOptimizer.versions.CLOUD`
    * :py:attr:`~sp.system_controller.optimizer.so_heuristic.SOHeuristicOptimizer.versions.NET_DELAY`
    * :py:attr:`~sp.system_controller.optimizer.so_heuristic.SOHeuristicOptimizer.versions.CLUSTER_METOIDS`
    * :py:attr:`~sp.system_controller.optimizer.so_heuristic.SOHeuristicOptimizer.versions.CLUSTER_METOIDS_SC`
    * :py:attr:`~sp.system_controller.optimizer.so_heuristic.SOHeuristicOptimizer.versions.DEADLINE`

    E.g.:

    .. code-block:: python

        # Using a single function
        version = SOHeuristicOptimizer.versions.NET_DELAY
        opt = SOHeuristicOptimizer(version)

        # Combining two or more functions
        version = [SOHeuristicOptimizer.versions.NET_DELAY, SOHeuristicOptimizer.versions.DEADLINE]
        opt = SOHeuristicOptimizer(version)


    Attributes:
        version (Union[list, function]): a single or list of heuristic to be used
    """

    versions = _VersionsEnum()
    """Enumeration of all heuristics that can be used.
    """

    def __init__(self, version=None):
        """Initialization

        Args:
            version (Union[list, function]): heuristic version
        """
        Optimizer.__init__(self)
        self.version = version

    def init_params(self):
        """Initialize parameters for a simulation
        """
        if self.version is None:
            self.version = [self.versions.NET_DELAY, self.versions.DEADLINE]

        if not isinstance(self.version, list):
            self.version = [self.version]

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (sp.core.model.system.System): current system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            sp.system_controller.model.opt_solution.OptSolution: problem solution
        Raises:
            OptimizerError: error found while solving the problem
        """
        self.init_params()
        ga_operator = SOGAOperator(system=system,
                                   environment_input=environment_input,
                                   objective=None)

        individual = indiv_gen.merge_creation_functions(ga_operator, self.version)
        solution = ga_operator.decode(individual)
        return solution
