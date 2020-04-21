from sp.core.heuristic import nsgaii
from .plan_finder import PlanFinder, Plan, decode_control_input
from functools import cmp_to_key
import multiprocessing as mp


class BeamPlanFinder(PlanFinder):
    def __init__(self, beam_width=10, prune=True, **pf_params):
        PlanFinder.__init__(self, **pf_params)
        self.beam_width = beam_width
        self.prune = prune

    def _decode_control_inputs(self, system, control_inputs, environment_input):
        def decode(control_input):
            return decode_control_input(system, control_input, environment_input)

        map_func = map
        func = decode
        pool = None
        if self.pool_size > 0:
            try:
                # Require UNIX fork to work
                mp_ctx = mp.get_context("fork")
                pool_size = min(self.pool_size, mp_ctx.cpu_count())
                pool = mp_ctx.Pool(processes=pool_size,
                                   initializer=_init_pool,
                                   initargs=[system, environment_input, decode_control_input])
                map_func = pool.map
                func = _decode_control_input
            except ValueError:
                pass

        results = map_func(func, control_inputs)
        if pool is not None:
            pool.terminate()
        return results

    def solve(self, control_inputs):
        beam_node = BeamNode()
        beam_node.system = self.system
        beam_nodes = [beam_node]

        for seq_index in range(self.sequence_length):
            next_beam_nodes = []
            env_input = self.environment_inputs[seq_index]
            stage_ctrl_inputs = control_inputs[seq_index]

            for beam_node in beam_nodes:
                system = beam_node.system
                decoded_ctrl_inputs = self._decode_control_inputs(system, stage_ctrl_inputs, env_input)
                for (ctrl_index, ctrl_input) in enumerate(decoded_ctrl_inputs):
                    next_system = self.system_estimator(system, ctrl_input, env_input)

                    add_system = True
                    if self.prune:
                        for next_beam_node in next_beam_nodes:
                            if next_beam_node.system == next_system:
                                add_system = False
                                break

                    if add_system:
                        fitness = [func(system, ctrl_input, env_input) for func in self.objective]

                        next_beam_node = BeamNode()
                        next_beam_node.parent = beam_node
                        next_beam_node.system = next_system
                        next_beam_node.control_input = stage_ctrl_inputs[ctrl_index]
                        next_beam_node.fitness = fitness
                        next_beam_nodes.append(next_beam_node)

            next_beam_nodes = _sort_beam_nodes(next_beam_nodes, self.objective_aggregator, self.dominance_func)
            beam_nodes = next_beam_nodes[:self.beam_width]

        plans = [bn.create_plan(self.objective_aggregator) for bn in beam_nodes]
        return plans


class BeamNode:
    def __init__(self):
        self.system = None
        self.control_input = None
        self.fitness = None
        self.parent = None

    def aggregated_fitness(self, aggregator):
        a_fitness = [[value] for value in self.fitness]
        parent = self.parent
        while parent is not None:
            if parent.fitness is not None:
                for (index, value) in enumerate(parent.fitness):
                    a_fitness[index].append(value)
            parent = parent.parent
        a_fitness.reverse()

        return [aggregator(value) for value in a_fitness]

    def control_sequence(self):
        sequence = [self.control_input]
        parent = self.parent
        while parent is not None:
            if parent.control_input is not None:
                sequence.append(parent.control_input)
            parent = parent.parent
        sequence.reverse()
        return sequence

    def create_plan(self, fitness_aggregator):
        fitness = self.aggregated_fitness(fitness_aggregator)
        control_sequence = self.control_sequence()

        return Plan(control_sequence, fitness)


def _sort_beam_nodes(beam_nodes, fitness_aggregator, dominance_operator):
    fitnesses = [bn.aggregated_fitness(fitness_aggregator) for bn in beam_nodes]
    fronts, rank = nsgaii.fast_non_dominated_sort(fitnesses, dominance_operator)
    crwd_dist = nsgaii.crowding_distance(fitnesses, fronts)

    def sort_cmp(item_1, item_2):
        index_1 = beam_nodes.index(item_1)
        index_2 = beam_nodes.index(item_2)
        if rank[index_1] < rank[index_2]:
            return -1
        elif (rank[index_1] == rank[index_2]
              and crwd_dist[index_1] < crwd_dist[index_2]):
            return -1
        else:
            return 1

    return sorted(beam_nodes, key=cmp_to_key(sort_cmp))


class _ControlInputDecoder:
    def __init__(self, system, environment_input, decoder_func):
        self.system = system
        self.environment_input = environment_input
        self.decoder_func = decoder_func

    def __call__(self, control_input):
        return self.decoder_func(self.system, control_input, self.environment_input)


def _init_pool(system, environment_input, decoder_func):
    global _decoder
    _decoder = _ControlInputDecoder(system, environment_input, decoder_func)


def _decode_control_input(control_input):
    global _decoder
    return _decoder(control_input)
