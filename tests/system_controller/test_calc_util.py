from sp.core.model import Scenario, Node, System, EnvironmentInput
from sp.system_controller.estimator.system import DefaultSystemEstimator
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller import util
from sp.system_controller.optimizer import CloudOptimizer, SOHeuristicOptimizer
import json
import math
import unittest


class CalcUtilTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_calc_util.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)

        optimizers = [CloudOptimizer(), SOHeuristicOptimizer()]
        sys_estimator = DefaultSystemEstimator()
        env_ctl = EnvironmentController()
        env_ctl.init_params()

        time_duration = 5
        systems = []
        control_inputs = []
        env_inputs = []
        for time in range(time_duration + 1):
            system.time = time
            system.sampling_time = 1
            env_input = env_ctl.update(system)

            opt = optimizers[time % len(optimizers)]
            control_input = opt.solve(system, env_input)

            systems.append(system)
            env_inputs.append(env_input)
            control_inputs.append(control_input)

            system = sys_estimator(system, control_input, env_input)

        cls.time_duration = time_duration
        cls.systems = systems
        cls.control_inputs = control_inputs
        cls.environment_inputs = env_inputs

    def test_calc_processing_delay(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            for app in system.apps:
                for dst_node in system.nodes:
                    proc_delay = util.calc_processing_delay(app.id, dst_node.id,
                                                            system, control_input, env_input)
                    if control_input.get_app_placement(app.id, dst_node.id):
                        self.assertGreater(proc_delay, 0.0)
                        self.assertNotEqual(proc_delay, math.inf)
                    else:
                        self.assertEqual(proc_delay, math.inf)

    def test_calc_network_delay(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            for app in system.apps:
                for src_node in system.nodes:
                    for dst_node in system.nodes:
                        net_delay = util.calc_network_delay(app.id, src_node.id, dst_node.id,
                                                            system, control_input, env_input)
                        env_net_delay = env_input.get_net_delay(app.id, src_node.id, dst_node.id)
                        self.assertEqual(net_delay, env_net_delay)

                        if src_node == dst_node:
                            self.assertEqual(net_delay, 0.0)
                        else:
                            self.assertGreater(net_delay, 0.0)

    def test_calc_initialization_delay(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            for app in system.apps:
                for dst_node in system.nodes:
                    curr_place = control_input.get_app_placement(app.id, dst_node.id)
                    prev_place = True
                    if system.control_input is not None:
                        prev_place = system.control_input.get_app_placement(app.id, dst_node.id)

                    init_delay = util.calc_initialization_delay(app.id, dst_node.id,
                                                                system, control_input, env_input)
                    mig_delay = util.calc_migration_delay(app.id, dst_node.id,
                                                          system, control_input, env_input)
                    if not curr_place:
                        self.assertEqual(init_delay, 0.0)
                    elif curr_place and prev_place:
                        self.assertEqual(init_delay, 0.0)
                    elif curr_place and not prev_place:
                        self.assertGreater(init_delay, 0.0)
                        self.assertLessEqual(init_delay, mig_delay)

    def test_calc_migration_delay(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            for app in system.apps:
                for dst_node in system.nodes:
                    curr_place = control_input.get_app_placement(app.id, dst_node.id)
                    prev_place = False
                    if system.control_input is not None:
                        prev_place = system.control_input.get_app_placement(app.id, dst_node.id)

                    mig_delay = util.calc_migration_delay(app.id, dst_node.id,
                                                          system, control_input, env_input)
                    if system.control_input is None:
                        self.assertEqual(mig_delay, 0.0)
                    elif curr_place and prev_place:
                        self.assertEqual(mig_delay, 0.0)
                    elif curr_place and not prev_place:
                        self.assertGreater(mig_delay, 0.0)

    def test_calc_response_time(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            for app in system.apps:
                for src_node in system.nodes:
                    for dst_node in system.nodes:
                        rt = util.calc_response_time(app.id, src_node.id, dst_node.id,
                                                     system, control_input, env_input)
                        self.assertGreaterEqual(rt, 0.0)
                        if control_input.get_app_placement(app.id, dst_node.id):
                            self.assertLess(rt, math.inf)
                        else:
                            self.assertEqual(rt, math.inf)

    def test_calc_load_before_distribution(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            env_input = self.environment_inputs[time]

            for app in system.apps:
                for src_node in system.nodes:
                    load = util.calc_load_before_distribution(app.id, src_node.id, system, env_input)
                    user_load = env_input.get_generated_load(app.id, src_node.id)
                    self.assertGreaterEqual(load, 0.0)
                    self.assertGreaterEqual(load, user_load)
                    self.assertLess(load, math.inf)
                    self.assertFalse(math.isnan(load))

    def test_calc_load_after_distribution(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            for app in system.apps:
                for src_node in system.nodes:
                    for dst_node in system.nodes:
                        load = util.calc_load_after_distribution(app.id, src_node.id, dst_node.id,
                                                                 system, control_input, env_input)

                        ld = control_input.get_load_distribution(app.id, src_node.id, dst_node.id)
                        before_load = util.calc_load_before_distribution(app.id, src_node.id, system, env_input)

                        self.assertEqual(load, ld * before_load)

    def test_calc_received_load(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            for app in system.apps:
                for dst_node in system.nodes:
                    load = util.calc_received_load(app.id, dst_node.id,
                                                   system, control_input, env_input, use_cache=False)
                    cached_load = util.calc_received_load(app.id, dst_node.id,
                                                          system, control_input, env_input, use_cache=True)
                    self.assertEqual(round(load), round(cached_load))


if __name__ == '__main__':
    unittest.main()
