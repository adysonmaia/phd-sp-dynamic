from sp.core.model import Scenario, System
from sp.system_controller.estimator.system import DefaultSystemEstimator
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.optimizer.dynamic.llc.plan_finder import Plan, GAPlanFinder
from sp.system_controller.optimizer.static.moga import MOGAOperator, preferred_dominates
from sp.system_controller.optimizer.static.soga import indiv_gen
from sp.system_controller.metric import deadline, cost, availability, migration
import json
import math
import unittest


class GAPFTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_llc_opt.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)

        system.time = 0
        env_ctl = EnvironmentController()
        env_ctl.init_params()

        env_inputs = []
        for time in range(5):
            system.time = time
            env = env_ctl.update(system)
            env_inputs.append(env)

        system.time = 0
        system.environment_input = env_inputs[0]

        cls.system = system
        cls.environment_inputs = env_inputs

    def test_solver(self):
        system_estimator = DefaultSystemEstimator()
        objective = [
            deadline.max_deadline_violation,
            cost.overall_cost,
            availability.avg_unavailability,
            migration.overall_migration_cost
        ]
        ga_params = {
            "nb_generations": 100,
            "population_size": 100,
            "elite_proportion": 0.1,
            "mutant_proportion": 0.1,
            "elite_probability": 0.6,
            "pool_size": 0,
            "stop_threshold": 0.10,
            "dominance_func": preferred_dominates
        }

        moga_operator = MOGAOperator(objective=objective,
                                     system=self.system,
                                     environment_input=self.environment_inputs[0])
        control_inputs = [
            indiv_gen.create_individual_cloud(moga_operator),
            indiv_gen.create_individual_net_delay(moga_operator),
            indiv_gen.create_individual_cluster_metoids(moga_operator),
            indiv_gen.create_individual_deadline(moga_operator)
        ]
        nb_stages = 2
        stages_control_input = [control_inputs for _ in range(nb_stages)]

        def decode_control_input(system, encoded_control, environment_input):
            decoder = MOGAOperator(objective=objective,
                                   system=system,
                                   environment_input=environment_input)
            return decoder.decode(encoded_control)

        pf = GAPlanFinder(system=self.system,
                          environment_inputs=self.environment_inputs,
                          objective=objective,
                          objective_aggregator=sum,
                          control_decoder=decode_control_input,
                          system_estimator=system_estimator,
                          **ga_params)

        plans = pf.solve(stages_control_input)
        self.assertGreater(len(plans), 0)

        for plan in plans:
            self.assertIsInstance(plan, Plan)
            self.assertEqual(len(plan.fitness), len(objective))

            for value in plan.fitness:
                self.assertGreaterEqual(value, 0.0)
                self.assertLess(value, math.inf)
                self.assertFalse(math.isnan(value))


if __name__ == '__main__':
    unittest.main()
