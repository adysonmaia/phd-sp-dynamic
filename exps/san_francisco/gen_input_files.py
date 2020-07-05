from sp.core.geometry import BoundBox, GpsPoint, create_grid_points
from sp.core.util import random as sp_rnd
from glob import glob
from collections import defaultdict
from future.utils import iteritems
from datetime import datetime
from pytz import timezone
import geopandas as gpd
import numpy as np
import json
import csv
import copy
import math
import random
import os
import base64


DATA_PATH = 'input/san_francisco/'
UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)


def main():
    """ Main function.
    It generates the simulation scenarios
    """

    # Input parameters
    map_path = os.path.join(DATA_PATH, 'shapefile/bay_area_zip_codes/')
    map_filename = os.path.join(map_path, 'geo_export_2defef9a-b2e1-4ddd-84f6-1a131dd80410.shp')
    mobility_path = os.path.join(DATA_PATH, 'cabs')

    # Simulation time
    train_start = SF_TZ.localize(datetime(2008, 5, 22, 0, 0, 0)).timestamp()
    time_start = SF_TZ.localize(datetime(2008, 5, 24, 0, 0, 0)).timestamp()
    time_stop = SF_TZ.localize(datetime(2008, 5, 24, 23, 59, 59)).timestamp()
    # time_step = 60 * 60  # seconds or 1H
    time_step = 30 * 60  # seconds or 30min
    simulation_data = {
        'time': {'start': time_start, 'stop': time_stop, 'step': time_step, 'train_start': train_start},
        'scenarios': []
    }

    # Scenarios parameters
    scenarios = [
        {'nb_apps': 1},
        # {'nb_apps': 5},
        # {'nb_apps': 10},
        # {'nb_apps': 15},
        # {'nb_apps': 508},
    ]

    # scenarios = [
    #     {'nb_apps': 1},
    #     {'nb_apps': 4},
    #     {'nb_apps': 7},
    #     {'nb_apps': 10}
    # ]

    # scenarios = [
    #     {'nb_apps': 4, 'time': {'step': 15 * 60}},
    #     {'nb_apps': 4, 'time': {'step': 30 * 60}},
    #     {'nb_apps': 4, 'time': {'step': 45 * 60}},
    #     {'nb_apps': 4, 'time': {'step': 60 * 60}},
    # ]

    # Generate each scenario
    nb_runs = 30
    cached_users_data = None
    for run in range(nb_runs):
        for scenario_params in scenarios:
            nb_apps = scenario_params['nb_apps']
            # scenario_id = 'n{}_a{}_u{}'.format(nb_bs, nb_apps, nb_users)
            scenario_id = base64.urlsafe_b64encode(bytes(json.dumps(scenario_params), 'utf-8')).decode('utf-8')
            scenario_id = 'a{}_{}'.format(nb_apps, scenario_id)
            scenario_path = os.path.join(DATA_PATH, scenario_id, str(run))
            scenario_filename, scenario_data = gen_scenario(nb_apps=nb_apps,
                                                            time_start=train_start,
                                                            time_stop=time_stop,
                                                            map_filename=map_filename,
                                                            mobility_path=mobility_path,
                                                            output_path=scenario_path,
                                                            cached_users_data=cached_users_data)
            if cached_users_data is None:
                cached_users_data = scenario_data['users']

            item = {'scenario_id': scenario_id, 'scenario': scenario_filename, 'run': run}
            item.update(scenario_params)
            simulation_data['scenarios'].append(item)

    # Save simulation configuration
    simulation_filename = os.path.join(DATA_PATH, 'simulation.json')
    with open(simulation_filename, 'w') as outfile:
        json.dump(simulation_data, outfile, indent=2)


def gen_scenario(nb_apps, time_start, time_stop, map_filename, mobility_path, output_path, cached_users_data=None):
    """ It generates a simulation scenario with specific parameters

    Args:
        nb_apps (int): number of applications
        time_start (float): simulation start time (in seconds)
        time_stop (float): simulation stop time (in seconds)
        map_filename (str): map filename
        mobility_path (str): directory of the mobility traces
        output_path (str): directory to save scenario config files
        cached_users_data (dict): cached users' data in json format. It reuses this previously generated data
    Returns:
        str: config filename of the generated scenario
        dict: scenario's data in json format
    """
    try:
        os.makedirs(output_path)
    except OSError:
        pass

    # Bound Box of San Francisco, CA, US
    # bbox_pos = [{'lon': -122.5160063624, 'lat': 37.7093}, {'lon': -122.3754337591, 'lat': 37.8112472822}]
    bbox_pos = [{'lon': -122.452, 'lat': 37.7315}, {'lon': -122.3754337591, 'lat': 37.8112472822}]
    bbox_points = [GpsPoint(**pos) for pos in bbox_pos]
    bbox = BoundBox(*bbox_points)

    # Generate the network
    topology = 'zipcode'
    net_data = gen_network(bbox, topology, map_filename=map_filename)
    net_filename = os.path.join(output_path, 'network_{}.json'.format(topology))
    with open(net_filename, 'w') as outfile:
        json.dump(net_data, outfile, indent=2)

    # Generate applications
    apps_data = gen_apps(nb_apps, net_data)
    apps_filename = os.path.join(output_path, 'apps.json')
    with open(apps_filename, 'w') as outfile:
        json.dump(apps_data, outfile, indent=2)

    # Generate users if cache is None
    users_data = None
    if cached_users_data is not None:
        users_data = copy.deepcopy(cached_users_data)
    else:
        users_pos_path = os.path.join(output_path, 'users_position')
        users_data = gen_users(time_start, time_stop, bbox, mobility_path, users_pos_path)

    # Distribute users among all applications
    users_data = distribute_users(users_data, apps_data, net_data)
    users_filename = os.path.join(output_path, 'users.json')
    with open(users_filename, 'w') as outfile:
        json.dump(users_data, outfile, indent=2)

    # Create scenario composed of net topology, applications, and users
    scenario_data = {
        'network': net_filename,
        'apps': apps_filename,
        'users': users_filename
    }
    scenario_filename = os.path.join(output_path, 'scenario.json')
    with open(scenario_filename, 'w') as outfile:
        json.dump(scenario_data, outfile, indent=2)

    scenario_data = {
        'network': net_data,
        'apps': apps_data,
        'users': users_data
    }
    return scenario_filename, scenario_data


def gen_network(bbox, topology, **kwargs):
    """Generate the network graph with a specific topology

    Args:
        bbox (BoundBox): bound box of positions
        topology (str): network's topology, values: 'grid', 'zipcode'
        **kwargs: extra parameters for creating a specific topology
    Returns:
         dict: network in json format
    """
    # Nodes properties
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
        # https://www.datacenters.com/6x7-networks-6x7-sm1
        'position': {'lat': 37.56167221069336, 'lon': -122.32598114013672},
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
        # https://www.datacenters.com/6x7-networks-equinix-palo-alto-sv8
        'position': {'lat': 37.4459157, 'lon': -122.1607421}
    }
    light_speed = 3e+9  # speed of light in vacuum - 300,000,000 m/s
    light_speed_glass = 2e+9  # speed of light in a glass medium - 200,000,000 m/s
    bs_bs_link_properties = {
        'bw': 100e+6,  # 100 Mbps (Mega bits per second)
        'delay': 0.001  # seconds or 1 ms
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
    json_data = gen_bs_network(bbox, topology, **kwargs)

    # Set the base station's properties
    for bs in json_data['nodes']:
        bs.update(bs_properties)

    # Set the properties of links between base stations
    for link in json_data['links']:
        link.update(bs_bs_link_properties)
        if 'distance' in link and 'delay' in link:
            extra_delay = link['distance'] / float(light_speed_glass)
            link['delay'] += extra_delay
            del link['distance']

    # Create the core node
    core_node = copy.copy(core_properties)
    core_id = len(json_data['nodes'])
    core_node['id'] = core_id
    # Connect each base station to the core node
    for node in json_data['nodes']:
        node_id = node['id']
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


def gen_bs_network(bbox, topology='grid', **kwargs):
    """Generate base stations in a specific format (topology)

    Args:
        bbox (BoundBox): limits where base stations' positions will be placed
        topology (str): format / topology of the network
        **kwargs: extra parameters for creating a specific topology
    Returns:
        dict: network in json format
    """
    if topology == 'grid':
        return gen_grid_bs_network(bbox, **kwargs)
    elif topology == 'zipcode':
        return gen_zipcode_bs_network(bbox, **kwargs)
    else:
        raise TypeError('Invalid topology format {}'.format(topology))


def gen_grid_bs_network(bbox, distance=2000.0, tol=200.0):
    """Generate base stations in a grid topology

    Args:
        bbox (BoundBox): bound box of the grid
        distance (float): distance between base stations
        tol (float): distance tolerance to connect two base stations
    Returns:
        dict: network in json format
    """
    # Generate base stations' positions in a bound box grid
    bs_points = create_grid_points(bbox, distance)

    # Set the base station's properties
    json_data = {'nodes': [], 'links': []}
    for (i_1, p_1) in enumerate(bs_points):
        pos = {'lat': p_1.lat, 'lon': p_1.lon}
        bs_node = {'id': i_1, 'position': pos}
        json_data['nodes'].append(bs_node)

        # Connect nearby base stations
        for i_2 in range(i_1 + 1, len(bs_points)):
            p_2 = bs_points[i_2]
            p_dist = p_1.distance(p_2)
            if p_1 != p_2 and p_dist <= distance + tol:
                link = {'nodes': (i_1, i_2), 'distance': p_dist}
                json_data['links'].append(link)

    return json_data


def gen_zipcode_bs_network(bbox, map_filename):
    """Generate base stations in the centroid of each zip code area of San Francisco

    Args:
       bbox (BoundBox): bound box of the grid
       map_filename (str): file name of the zip code map
    Returns:
       dict: network in json format
    """
    # Load zip code map as a geopanda DataFrame
    crs = 'EPSG:4326'
    map_gdf = gpd.read_file(map_filename)
    map_gdf = map_gdf.to_crs(crs)
    map_gdf = map_gdf.cx[bbox.x_min:bbox.x_max, bbox.y_min:bbox.y_max]
    centroids = map_gdf.centroid.cx[bbox.x_min:bbox.x_max, bbox.y_min:bbox.y_max]
    map_gdf = map_gdf.loc[centroids.index]
    map_gdf.sort_values('zip', inplace=True)
    map_gdf.reset_index(drop=True, inplace=True)

    link_exists = defaultdict(lambda: defaultdict(bool))
    json_data = {'nodes': [], 'links': []}
    # Create a base station for each zip code area
    for (index, row) in map_gdf.iterrows():
        centroid = row.geometry.centroid
        pos = GpsPoint(lon=centroid.x, lat=centroid.y)
        bs_node = {'id': index, 'position': {'lon': pos.lon, 'lat': pos.lat}}
        json_data['nodes'].append(bs_node)

        # Find neighbors areas and create a link between the neighbors
        neighbors_gdf = map_gdf[map_gdf.touches(row.geometry)]
        for (neighbor_index, neighbor) in neighbors_gdf.iterrows():
            # Check if the link is already created
            if not link_exists[index][neighbor_index]:
                # Transform centroid point to GpsPoint to correctly calculate the distance
                neighbor_centroid = neighbor.geometry.centroid
                neighbor_pos = GpsPoint(lon=neighbor_centroid.x, lat=neighbor_centroid.y)
                dist = pos.distance(neighbor_pos)

                # Set link's properties
                link = {'nodes': (index, neighbor_index), 'distance': dist}
                json_data['links'].append(link)

                # Create undirected graph
                link_exists[index][neighbor_index] = True
                link_exists[neighbor_index][index] = True

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
    # max_instance_range = [1]
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
        # app_type = selected_type[index]
        app_type = 'URLLC'

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
        # demand_cpu_a = cpu_work + 1.0
        # demand_cpu_b = cpu_work / float(deadline) + 1.0
        # demand_cpu_b = 2.0 * cpu_work / float(deadline) + 1.0
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


def gen_users(time_start, time_stop, bbox, mobility_path, output_path):
    """Generate users

    Args:
        time_start (float): simulation start time (unix timestamp)
        time_stop (float): simulation stop time (unix timestamp)
        bbox (BoundBox): bound box of the users' positions
        mobility_path (str): directory of the mobility traces
        output_path (str): directory to save users' positions
    Returns:
        dict: users in json format
    """
    cabs_pathname = os.path.join(mobility_path, 'new_*.txt')
    cabs_filename = glob(cabs_pathname)

    try:
        os.makedirs(output_path)
    except OSError:
        pass

    # Each taxi has its own GPS trace file and it will be a user if the trace is not empty
    json_data = {'users': []}
    for filename in cabs_filename:
        positions = []
        # Convert GPS traces on csv format to json format
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=" ")
            for row in csv_reader:
                lat = float(row[0])
                lon = float(row[1])
                time = int(row[3])

                # Filter positions in a time and position interval
                in_interval = time_start <= time <= time_stop
                in_interval = in_interval and (bbox.x_min <= lon <= bbox.x_max)
                in_interval = in_interval and (bbox.y_min <= lat <= bbox.y_max)
                if in_interval:
                    pos = {'lat': lat, 'lon': lon, 't': time}
                    positions.append(pos)

        # Only create a user if the taxi has GPS traces during the selected time interval
        if len(positions) > 0:
            user_id = len(json_data['users'])
            # Save the position traces in a separated file
            pos_filename = os.path.join(output_path, 'user_{}.json'.format(user_id))
            with open(pos_filename, mode='w') as json_file:
                json.dump(positions, json_file)

            # Set user's properties
            user = {'id': user_id, 'pos': pos_filename}
            json_data['users'].append(user)

    return json_data


def distribute_users(users_data, apps_data, net_data):
    """Distribute users among the generated applications

    Args:
        users_data (dict): users data in json format
        apps_data (dict): applications data in json format
        net_data (dict): network data in json format
    Returns:
        dict: distributed users in json format
    """
    apps_id = [row['id'] for row in apps_data['apps']]
    nb_apps = len(apps_id)
    nb_nodes = len(net_data['nodes'])
    total_nb_users = len(users_data['users'])
    users_index = list(range(total_nb_users))

    # Generate distribution factors for all applications
    # users_distribution = gen_users_distribution(users_data, apps_data, net_data, dist_type='zipf')
    # users_distribution = gen_users_distribution(users_data, apps_data, net_data, dist_type='app_type')
    users_distribution = gen_users_distribution(users_data, apps_data, net_data, dist_type='equal')

    # Distribute users among all applications
    remaining_users = frozenset(users_index)
    # min_nb_users = min(nb_nodes, total_nb_users // nb_apps)
    min_nb_users = 1
    # min_nb_users = total_nb_users // nb_apps
    nb_users_to_distribute = max(0.0, total_nb_users - nb_apps * min_nb_users)
    users_per_app = {}
    max_dist_app_id = None
    max_dist = 0.0
    for (app_index, distribution) in enumerate(users_distribution):
        app_id = apps_id[app_index]
        nb_users = math.floor(distribution * nb_users_to_distribute) + min_nb_users
        nb_users = int(min(nb_users, len(remaining_users)))

        users = []
        if nb_users > 0:
            users = list(random.sample(remaining_users, nb_users))
            remaining_users = remaining_users.difference(users)
        users_per_app[app_id] = users

        if distribution >= max_dist:
            max_dist = distribution
            max_dist_app_id = app_id

    # Put the remaining users to the most popular application (i.e., app with highest distribution)
    if len(remaining_users) > 0 and max_dist_app_id is not None:
        users_per_app[max_dist_app_id] += list(remaining_users)

    # Set the requested application for each user
    for (app_id, users) in iteritems(users_per_app):
        for user_index in users:
            user = users_data['users'][user_index]
            user['app_id'] = app_id

    return users_data


def gen_users_distribution(users_data, apps_data, net_data, dist_type='zipf'):
    """Generate users distribution factor for each application

    Args:
        users_data (dict): users data in json format
        apps_data (dict): applications data in json format
        net_data (dict): network data in json format
        dist_type (str): distribution type. Options: 'zipf', 'app_type', 'equal'
    Returns:
        list: distribution factor for each application
    """

    users_distribution = None
    if dist_type == 'zipf':
        # Use zipf (zeta) distribution to set number of users of each application
        nb_apps = len(apps_data['apps'])
        zipf_alpha = 1.6
        users_distribution = sp_rnd.random_zipf(zipf_alpha, nb_apps)
    elif dist_type == 'app_type':
        # Set users percentage for each application based on its type
        app_type_distribution = {'URLLC': 0.1, 'EMBB': 0.2, 'MMTC': 0.7}
        app_types = list(app_type_distribution.keys())
        nb_apps_per_type = {app_type: sum(map(lambda a: a['type'] == app_type, apps_data['apps']))
                            for app_type in app_types}
        nb_types_with_app = len([t for t in app_types if nb_apps_per_type[t] > 0])
        users_distribution = [app_type_distribution[a['type']] / float(nb_apps_per_type[a['type']])
                              for a in apps_data['apps']]
    else:
        nb_apps = len(apps_data['apps'])
        users_distribution = [1 / float(nb_apps)] * nb_apps
    return users_distribution


if __name__ == '__main__':
    main()
