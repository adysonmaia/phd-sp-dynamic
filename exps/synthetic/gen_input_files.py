from sp.core.geometry import CartesianPoint, BoundBox, create_grid_points
from sp.core.util import random as sp_rnd
import numpy as np
import copy
import random
import math
import json
import os


DATA_PATH = 'input/synthetic/'


def main():
    """ Main function.
    It generates the simulation scenarios
    """
    # Scenarios parameters
    # scenarios = [
    #     {'nb_bs': 25, 'nb_apps': 10, 'nb_users': 10000},
    #     {'nb_bs': 25, 'nb_apps': 20, 'nb_users': 10000},
    #     {'nb_bs': 25, 'nb_apps': 30, 'nb_users': 10000},
    #     {'nb_bs': 25, 'nb_apps': 40, 'nb_users': 10000},
    #     {'nb_bs': 25, 'nb_apps': 50, 'nb_users': 10000},
    #
    #     {'nb_bs': 25, 'nb_apps': 50, 'nb_users': 1000},
    #     {'nb_bs': 25, 'nb_apps': 50, 'nb_users': 4000},
    #     {'nb_bs': 25, 'nb_apps': 50, 'nb_users': 7000},
    # ]
    # scenarios = [
    #     {'nb_bs': 9, 'nb_apps': 5, 'nb_users': 10000},
    #     {'nb_bs': 9, 'nb_apps': 10, 'nb_users': 10000},
    #     {'nb_bs': 9, 'nb_apps': 15, 'nb_users': 10000},
    #     {'nb_bs': 9, 'nb_apps': 20, 'nb_users': 10000},
    # ]
    scenarios = [
        {'nb_bs': 9, 'nb_apps': 5, 'nb_users': 5000},
        {'nb_bs': 9, 'nb_apps': 5, 'nb_users': 10000},
        {'nb_bs': 9, 'nb_apps': 5, 'nb_users': 15000},
        {'nb_bs': 9, 'nb_apps': 5, 'nb_users': 20000},
    ]
    # scenarios = [
    #     {'nb_bs': 9, 'nb_apps': 5, 'nb_users': 10000},
    # ]

    # Simulation times
    time_start = 0.0
    time_step = 30.0 * 60.0  # 30 min
    nb_steps = 48
    # nb_steps = 10
    # nb_steps = 50
    time_stop = (nb_steps - 1) * time_step + time_start
    simulation_data = {
        'time': {'start': time_start, 'stop': time_stop, 'step': time_step},
        'scenarios': []
    }

    # Generate each scenario
    nb_runs = 30
    for run in range(nb_runs):
        for scenario_params in scenarios:
            nb_bs = scenario_params['nb_bs']
            nb_apps = scenario_params['nb_apps']
            nb_users = scenario_params['nb_users']
            scenario_id = 'n{}_a{}_u{}'.format(nb_bs, nb_apps, nb_users)

            scenario_path = os.path.join(DATA_PATH, scenario_id, str(run))
            scenario_filename = gen_scenario(nb_bs, nb_apps, nb_users,
                                             time_start, time_stop, time_step,
                                             scenario_path)

            item = {'scenario_id': scenario_id, 'scenario': scenario_filename, 'run': run}
            simulation_data['scenarios'].append(item)

    # Save simulation configuration
    simulation_filename = os.path.join(DATA_PATH, 'simulation.json')
    with open(simulation_filename, 'w') as outfile:
        json.dump(simulation_data, outfile, indent=2)


def gen_scenario(nb_bs, nb_apps, nb_users, time_start, time_stop, time_step, scenario_path):
    """It generates a scenario with specific parameters

    Args:
        nb_bs (int): number of base stations (edge nodes)
        nb_apps (int): number of applications
        nb_users (int): number of users
        time_start (float): simulation start time (in seconds)
        time_stop (float): simulation stop time (in seconds)
        time_step (float): simulation time step duration (in seconds)
        scenario_path (str): directory to save scenario input files
    Returns:
        str: config filename of the generated scenario
    """

    try:
        os.makedirs(scenario_path)
    except OSError:
        pass

    # Create network
    net_data = gen_network(nb_bs)
    net_filename = os.path.join(scenario_path, 'net.json')
    with open(net_filename, 'w') as outfile:
        json.dump(net_data, outfile, indent=2)

    # Create applications
    apps_data = gen_apps(nb_apps, net_data)
    apps_filename = os.path.join(scenario_path, 'apps.json')
    with open(apps_filename, 'w') as outfile:
        json.dump(apps_data, outfile, indent=2)

    # Create applications' loads in each node
    loads_data = gen_loads(nb_users, time_start, time_stop, time_step, apps_data, net_data)
    loads_filename = os.path.join(scenario_path, 'loads.json')
    with open(loads_filename, 'w') as outfile:
        json.dump(loads_data, outfile, indent=2)

    # Create scenario composed of net topology, applications, and loads
    scenario_data = {
        'network': net_filename,
        'apps': apps_filename,
        'loads': loads_filename
    }
    scenario_filename = os.path.join(scenario_path, 'scenario.json')
    with open(scenario_filename, 'w') as outfile:
        json.dump(scenario_data, outfile, indent=2)

    return scenario_filename


def gen_network(nb_bs):
    """Generate the network graph with a specific topology

    Args:
        nb_bs (int): number of base stations (edge nodes)
    Returns:
         dict: network in json format
    """
    bs_properties = {
        'type': 'BS',
        'avail': 0.99,  # 99 %
        'capacity': {
            'CPU': 2 * 5e+9,  # 2 Core with 5 GIPS (Giga Instructions Per Second)
            'RAM': 8e+9,  # 8 GB (Giga Byte)
            'DISK': 16e+9,  # 16 GB (Giga Byte)
        },
        'cost': {
            'CPU': [1e-12, 1e-12],  # cost for IPS / second
            'RAM': [1e-15, 1e-15],  # cost for Byte / second
            'DISK': [1e-18, 1e-18]  # cost for Byte / second
        },
        'power': [50.0, 100.0]  # [Idle, Max] Power (Watt)
    }
    core_properties = {
        'type': 'CORE',
        'avail': 0.999,  # 99.9 %
        'capacity': {
            'CPU': 4 * 5e+9,  # 4 Core with 5 GIPS (Giga Instructions Per Second)
            'RAM': 16e+9,  # 16 GB (Giga Byte)
            'DISK': 32e+9,  # 32 GB (Giga Byte)
        },
        'cost': {
            'CPU': [0.5e-12, 0.5e-12],  # cost for IPS / second
            'RAM': [0.5e-15, 0.5e-15],  # cost for Byte / second
            'DISK': [0.5e-18, 0.5e-18]  # cost for Byte / second
        },
        'power': [100.0, 200.0],  # [Idle, Max] Power (Watt)
        'position': {'x': -1, 'y': 0},
    }
    cloud_properties = {
        'type': 'CLOUD',
        'avail': 0.9999,  # 99.99 %
        'capacity': {
            'CPU': 'INF',
            'RAM': 'INF',
            'DISK': 'INF'
        },
        'cost': {
            'CPU': [0.25e-12, 0.25e-12],  # cost for IPS / second
            'RAM': [0.25e-15, 0.25e-15],  # cost for Byte / second
            'DISK': [0.25e-18, 0.25e-18]  # cost for Byte / second
        },
        'power': [200.0, 400.0],  # [Idle, Max] Power (Watt)
        'position': {'x': -2, 'y': 0}
    }
    bs_bs_link_properties = {
        'bw': 100e+6,  # 100 Mbps (Mega bits per second)
        'delay': 0.001,  # seconds or 1 ms
    }
    bs_core_link_properties = {
        'bw': 1e+9,  # 1 Gbps (Giga bits per second)
        'delay': 0.001  # seconds or 1 ms
    }
    core_cloud_link_properties = {
        'bw': 10e+9,  # 10 Gbps (Giga bits per second)
        'delay': 0.01  # seconds or 10 ms
    }

    # Generate base stations' positions in a bound box grid
    json_data = gen_bs_network(nb_bs)

    # Set the base station's properties
    for bs in json_data['nodes']:
        bs.update(bs_properties)

    # Set the properties of links between base stations
    for link in json_data['links']:
        link.update(bs_bs_link_properties)

    # Create the core node
    core_node = copy.copy(core_properties)
    core_id = len(json_data['nodes'])
    core_node['id'] = core_id
    # Connect each base station to the core node
    for node in json_data['nodes']:
        node_id = int(node['id'])
        link = copy.copy(bs_core_link_properties)
        link['nodes'] = (node_id, core_id)
        json_data['links'].append(link)
    json_data['nodes'].append(core_node)

    # Create the cloud node and connect it to the core node
    cloud_node = copy.copy(cloud_properties)
    cloud_id = len(json_data['nodes'])
    cloud_node['id'] = cloud_id
    json_data['nodes'].append(cloud_node)
    link = copy.copy(core_cloud_link_properties)
    link['nodes'] = (core_id, cloud_id)
    json_data['links'].append(link)

    return json_data


def gen_bs_network(nb_nodes):
    """Generate base stations with 2D grid topology

    Args:
        nb_nodes (int): number of nodes (points) in the grid
    Returns:
        dict: network in json format
    """
    # Set grid parameters
    cell_side = 1.0
    dist_tol = 0.0

    nb_rows = int(math.ceil(math.sqrt(nb_nodes)))
    nb_cols = nb_rows

    # Set grid's bound box
    point_1 = CartesianPoint(0.0, 0.0)
    point_2 = CartesianPoint(nb_cols * cell_side, nb_rows * cell_side)
    bbox = BoundBox(point_1, point_2)

    # Create grid topology
    bs_points = create_grid_points(bbox, cell_side)
    bs_points = bs_points[:nb_nodes]

    # Set the base station's properties
    json_data = {'nodes': [], 'links': []}
    for (i_1, p_1) in enumerate(bs_points):
        pos = {'x': p_1.x, 'y': p_1.y}
        bs_node = {'id': i_1, 'position': pos}
        json_data['nodes'].append(bs_node)

        # Connect nearby base stations
        for i_2 in range(i_1 + 1, len(bs_points)):
            p_2 = bs_points[i_2]
            p_dist = p_1.distance(p_2)
            if p_1 != p_2 and p_dist <= cell_side + dist_tol:
                link = {'nodes': (i_1, i_2)}
                json_data['links'].append(link)

    return json_data


def gen_apps(nb_apps, net_data):
    """Generate applications

    Args:
        nb_apps (int): number of applications
        net_data (dict): network's data
    Returns:
        dict: applications in json format
    """
    # Deadline for response time (in seconds)
    deadline_options = {
        'URLLC': np.linspace(0.001, 0.01, num=10),
        'EMBB': np.linspace(0.01, 0.1, num=10),
        'MMTC': np.linspace(0.1, 1.0, num=10),
    }
    # Number of CPU instructions to process a request
    cpu_work_options = {
        'URLLC': np.linspace(1, 5, num=5) * 1e+6,
        'MMTC': np.linspace(1, 5, num=5) * 1e+6,
        'EMBB': np.linspace(5, 10, num=5) * 1e+6,
    }
    # Packet data size of a request transmitted on the network (in bits)
    packet_size_options = {
        'URLLC': np.linspace(100, 1000, num=10),
        'MMTC': np.linspace(100, 1000, num=10),
        'EMBB': np.linspace(100, 10000, num=10),
    }
    # Request generation rate (request / second)
    request_rate_options = {
        'URLLC': np.linspace(1, 100, num=10),
        'MMTC': np.linspace(0.1, 1.0, num=10),
        'EMBB': np.linspace(1, 100, num=10),
    }
    # Availability probability (between 0 and 1)
    availability_options = {
        'URLLC': np.linspace(0.99, 0.999, num=10),
        'MMTC': np.linspace(0.9, 0.99, num=10),
        'EMBB': np.linspace(0.9, 0.99, num=10),
    }

    # Maximum number of instances running at the same time-slot
    max_instance_range = list(range(1, len(net_data['nodes']) + 1))
    # max_instance_range = [len(net_data['nodes'])]
    max_instance_options = {
        'URLLC': max_instance_range,
        'MMTC': max_instance_range,
        'EMBB': max_instance_range,
    }

    # Linear demand for RAM resource (in byte)
    demand_ram_a_options = {
        'URLLC': np.linspace(0.1, 1, num=10) * 1e+6,
        'MMTC': np.linspace(0.1, 1, num=10) * 1e+6,
        'EMBB': np.linspace(1, 10, num=10) * 1e+6,
    }
    demand_ram_b_options = {
        'URLLC': np.linspace(10, 100, num=10) * 1e+6,
        'MMTC': np.linspace(10, 100, num=10) * 1e+6,
        'EMBB': np.linspace(100, 1000, num=10) * 1e+6,
    }

    # Linear demand for DISK resource (in byte)
    demand_disk_a_options = {
        'URLLC': np.linspace(0.1, 1, num=10) * 1e+6,
        'MMTC': np.linspace(0.1, 1, num=10) * 1e+6,
        'EMBB': np.linspace(1, 10, num=10) * 1e+6,
    }
    demand_disk_b_options = {
        'URLLC': np.linspace(10, 100, num=10) * 1e+6,
        'MMTC': np.linspace(10, 100, num=10) * 1e+6,
        'EMBB': np.linspace(100, 1000, num=10) * 1e+6,
    }
    # CPU parameters
    cpu_attenuation_options = {
        'URLLC': np.linspace(0.1, 0.5, num=5),
        'MMTC': np.linspace(0.1, 0.5, num=5),
        'EMBB': np.linspace(0.1, 0.5, num=5),
    }

    app_type_options = ['URLLC', 'MMTC', 'EMBB']
    selected_type = None
    if nb_apps >= len(app_type_options):
        selected_type = copy.copy(app_type_options)
        selected_type += list(np.random.choice(app_type_options, size=nb_apps - len(selected_type)))
    else:
        selected_type = list(np.random.choice(app_type_options, size=nb_apps))

    # Generate applications
    json_data = {'apps': []}
    for index in range(nb_apps):
        app_type = selected_type[index]

        deadline = random.choice(deadline_options[app_type])
        cpu_work = random.choice(cpu_work_options[app_type])
        packet_size = random.choice(packet_size_options[app_type])
        request_rate = random.choice(request_rate_options[app_type])
        availability = random.choice(availability_options[app_type])
        max_instance = random.choice(max_instance_options[app_type])

        # Linear demand, f(x) = ax + b
        demand_ram_a = random.choice(demand_ram_a_options[app_type])
        demand_ram_b = random.choice(demand_ram_b_options[app_type])
        demand_disk_a = random.choice(demand_disk_a_options[app_type])
        demand_disk_b = random.choice(demand_disk_b_options[app_type])

        # Create linear estimator that satisfies the queue and deadline constraints
        # f(x) = ax + b
        # demand_cpu_a = cpu_work
        # demand_cpu_b = 2.0 * cpu_work / float(deadline)
        demand_cpu_a = cpu_work + 1.0
        cpu_attenuation = random.choice(cpu_attenuation_options[app_type])
        demand_cpu_b = (cpu_work / float(cpu_attenuation * deadline)) + 1.0

        app = {
            'id': index,
            'type': app_type,
            'deadline': deadline,
            'work': cpu_work,
            'data': packet_size,
            'rate': request_rate,
            'avail': availability,
            'max_inst': max_instance,
            'demand': {
                'RAM': [demand_ram_a, demand_ram_b],
                'DISK': [demand_disk_a, demand_disk_b],
                'CPU': [demand_cpu_a, demand_cpu_b]
            }
        }
        json_data['apps'].append(app)
    return json_data


def gen_loads(nb_users, time_start, time_stop, time_step, apps_data, net_data):
    """Generate loads for each application in each node along the simulation

    Args:
        nb_users (int): total number of users in the system
        time_start (float): simulation start time (in seconds)
        time_stop (float): simulation stop time (in seconds)
        time_step (float): simulation time step duration (in seconds)
        apps_data (dict): applications' data
        net_data (dict): network's data
    Returns:
        list: generated load
    """
    bs_nodes_id = [row['id'] for row in net_data['nodes'] if row['type'] == 'BS']
    nb_bs_nodes = len(bs_nodes_id)

    # Distribute users among the applications
    users_per_app = distribute_users(nb_users, apps_data, net_data)

    json_data = []
    for app in apps_data['apps']:
        app_id = app['id']
        total_users = users_per_app[app_id]
        for node_id in bs_nodes_id:
            # Users are equally distributed to each node
            users = total_users / float(nb_bs_nodes)
            min_load = 0.0
            max_load = users * app['rate']

            # Varies load during simulation time steps
            loads = distribute_load(min_load, max_load, time_start, time_stop, time_step)

            # Save load
            item = {'app_id': app_id, 'node_id': node_id, 'load': loads}
            json_data.append(item)

    return json_data


def distribute_users(nb_users, apps_data, net_data):
    """Distribute a specific amount of users among the applications

    Args:
        nb_users (int): total number of users
        apps_data (dict): applications' data
        net_data (dict): network's data
    Returns:
        dict: number of users per application after the distribution
    """
    apps_id = [row['id'] for row in apps_data['apps']]
    nb_apps = len(apps_id)
    nb_nodes = len(net_data['nodes'])

    # Set a minimum amount of users for each application
    min_users = nb_nodes
    users_per_app = {app_id: min_users for app_id in apps_id}
    remaining_users = nb_users - min_users * nb_apps

    # Set users percentage for each application based on its type
    app_type_distribution = {'URLLC': 0.1, 'EMBB': 0.2, 'MMTC': 0.7}
    app_types = list(app_type_distribution.keys())
    nb_apps_per_type = {app_type: sum(map(lambda a: a['type'] == app_type, apps_data['apps']))
                        for app_type in app_types}
    nb_types_with_app = len([t for t in app_types if nb_apps_per_type[t] > 0])
    users_distribution = None
    if nb_types_with_app > 1:
        users_distribution = [app_type_distribution[a['type']] / float(nb_apps_per_type[a['type']])
                              for a in apps_data['apps']]
    else:
        zipf_alpha = 1.6
        users_distribution = sp_rnd.random_zipf(zipf_alpha, nb_apps)

    # Distribute users among all applications
    users_count = 0.0
    max_dist_app_id = None
    max_dist = 0.0
    for (app_index, distribution) in enumerate(users_distribution):
        users = math.floor(distribution * remaining_users)
        app_id = apps_id[app_index]
        users_per_app[app_id] += users
        users_count += users
        if distribution >= max_dist:
            max_dist = distribution
            max_dist_app_id = app_id

    # Put the remaining users to the most popular application (i.e., app with highest distribution)
    remaining_users -= users_count
    if remaining_users > 0.0 and max_dist_app_id is not None:
        users_per_app[max_dist_app_id] += remaining_users

    return users_per_app


def distribute_load(min_load, max_load, time_start, time_end, time_step):
    """Distribute load in a range along the simulation time

    Args:
        min_load (float): minimum load
        max_load (float): maximum load
        time_start (float): start time of the simulation
        time_end (float): end time of the simulation
        time_step (float): time step duration of the simulation
    Returns:
        list: distributed load in a json format
    """
    # time_step = min(10 * 60.0, time_step)  # 10 min
    nb_steps = int(math.floor((time_end - time_start) / float(time_step)))

    # Different load patterns
    rnd_funcs = [
        sp_rnd.random_burst,
        sp_rnd.random_beta_pdf,
        sp_rnd.random_cycle,
        sp_rnd.random_linear,
        sp_rnd.random_constant,
        sp_rnd.random_uniform,
        sp_rnd.random_time_series,
    ]

    rnd_params = {
        sp_rnd.random_burst: [
            {'normal_transition': 0.1, 'burst_transition': 0.1},
            {'normal_transition': 0.2, 'burst_transition': 0.2},
            {'normal_transition': 0.3, 'burst_transition': 0.3},
        ],
        sp_rnd.random_beta_pdf: [
            {'alpha': 2, 'beta': 2},
            {'alpha': 2, 'beta': 3},
            {'alpha': 3, 'beta': 2},
            {'alpha': 1, 'beta': 5},
            {'alpha': 5, 'beta': 1}
        ],
        sp_rnd.random_cycle: [
            {'period': nb_steps},
            {'period': nb_steps / 2.0}
        ],
        sp_rnd.random_time_series: [
            {'time_series': 'input/san_francisco/loads/1d.json', 'min_value': 0.0},
            {'time_series': 'input/san_francisco/loads/1d.json', 'min_value': None},
            {'time_series': 'input/san_francisco/loads/1d_n15_4.json', 'min_value': 0.0},
            {'time_series': 'input/san_francisco/loads/1d_n15_4.json', 'min_value': None},
        ],
        sp_rnd.random_linear: [{}],
        sp_rnd.random_constant: [{}],
        sp_rnd.random_uniform: [{}]
    }

    # Choose a load pattern
    func = random.choice(rnd_funcs)
    func_kwargs = random.choice(rnd_params[func])

    # Generate load along the simulation according to the selected pattern
    noise = 0.01
    samples = func(nb_samples=nb_steps, noise=noise, **func_kwargs)
    loads = []
    for step in range(nb_steps):
        distribution = samples[step]
        load = max_load * distribution + min_load
        time = step * time_step + time_start
        item = {'t': time, 'v': load}
        loads.append(item)

    return loads


if __name__ == '__main__':
    main()
