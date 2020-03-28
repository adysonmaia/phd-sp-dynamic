from sp.core.geometry import grid
from sp.core.geometry.bound_box import BoundBox
from sp.core.geometry.point.gps import GpsPoint
from glob import glob
from collections import defaultdict
from future.utils import iteritems
from datetime import datetime
from pytz import timezone
import geopandas as gpd
import json
import csv
import copy
import math


DATA_PATH = 'input/san_francisco/'


def main():
    """ Main function. It generates the simulation scenario
    """
    # Bound Box of San Francisco, CA, US
    bbox_pos = [{'lon': -122.5160063624, 'lat': 37.7093}, {'lon': -122.3754337591, 'lat': 37.8112472822}]
    bbox_points = [GpsPoint(**pos) for pos in bbox_pos]
    bbox = BoundBox(*bbox_points)

    # Generate the network
    topology = 'zipcode'
    network_json = gen_network(topology, bbox)
    network_filename = DATA_PATH + 'network_{}.json'.format(topology)
    with open(network_filename, 'w') as outfile:
        json.dump(network_json, outfile, indent=2)

    # Generate applications
    apps_json = gen_apps()
    apps_filename = DATA_PATH + 'apps.json'
    with open(apps_filename, 'w') as outfile:
        json.dump(apps_json, outfile, indent=2)

    # Generate users
    users_json = gen_users(apps_json, bbox)
    users_filename = DATA_PATH + 'users.json'
    with open(users_filename, 'w') as outfile:
        json.dump(users_json, outfile, indent=2)

    # Create scenario composed of net topology, applications, and users
    scenario_json = {
        'network': network_filename,
        'apps': apps_filename,
        'users': users_filename
    }
    scenario_filename = DATA_PATH + 'scenario.json'
    with open(scenario_filename, 'w') as outfile:
        json.dump(scenario_json, outfile, indent=2)


def gen_network(topology, bbox):
    """Generate the network graph with a specific topology
    Args:
        topology (str): network's topology, values: 'grid', 'zipcode'
        bbox (BoundBox): bound box of positions
    Returns:
         dict: network in json format
    """
    distance = 2000.0
    dist_tol = 200.0
    # Bound Box of San Francisco, CA, US

    bs_properties = {
        'type': 'BS',
        'avail': 0.99,  # 99 %
        'capacity': {
            'CPU': 1e+9,  # 1 GIPS (Giga Instructions Per Second),
            'RAM': 8e+9,  # 8 GB (Giga Byte)
            'DISK': 500e+9,  # 500 GB (Giga Byte)
        },
        'cost': {
            'CPU': [1.0, 1.0],
            'RAM': [1.0, 1.0],
            'DISK': [1.0, 1.0]
        },
        'power': [50.0, 100.0]  # [Idle, Max] Power (Watt)
    }
    core_properties = {
        'type': 'CORE',
        'avail': 0.999,  # 99.9 %
        'capacity': {
            'CPU': 1e+12,  # 1 TIPS (Tera Instructions Per Second)
            'RAM': 16e+9,  # 16 GB (Giga Byte)
            'DISK': 1e+12  # 1 TB (Tera Byte)
        },
        'cost': {
            'CPU': [0.5, 0.5],
            'RAM': [0.5, 0.5],
            'DISK': [0.5, 0.5]
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
            'CPU': [0.25, 0.25],
            'RAM': [0.25, 0.25],
            'DISK': [0.25, 0.25]
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
    json_data = gen_bs_network(bbox, topology=topology)

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
    Returns:
        dict: network in json format
    """
    if topology == 'grid':
        return gen_grid_bs_network(bbox, **kwargs)
    elif topology == 'zipcode':
        return gen_zipcode_bs_network(bbox)
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
    bs_points = grid.create_grid_points(bbox, distance)

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


def gen_zipcode_bs_network(bbox):
    """Generate base stations in the centroid of each zip code area of San Francisco
    Args:
       bbox (BoundBox): bound box of the grid
    Returns:
       dict: network in json format
    """
    # Load zip code map as a geopanda DataFrame
    crs = 'EPSG:4326'
    shape_file = 'input/san_francisco/shapefile/bay_area_zip_codes/geo_export_2defef9a-b2e1-4ddd-84f6-1a131dd80410.shp'
    map_gdf = gpd.read_file(shape_file)
    map_gdf = map_gdf.to_crs(crs)
    map_gdf = map_gdf.cx[bbox.x_min:bbox.x_max, bbox.y_min:bbox.y_max]
    map_gdf.sort_values('zip', inplace=True)
    map_gdf.reset_index(drop=True, inplace=True)

    # print(map_gdf)
    # import matplotlib.pyplot as plt
    # fig, ax = plt.subplots()
    # map_gdf.plot(ax=ax, color='white', edgecolor='black', zorder=0)
    # map_gdf.centroid.plot(ax=ax, color='red', zorder=1, label='BS')
    # plt.show()

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


def gen_apps():
    """Generate applications
    Returns:
        dict: applications in json format
    """
    embb = {
        'type': 'EMBB',
        'deadline': 0.01,  # seconds or 10 ms
        'work': 100e+6,  # MI (Millions of Instructions)
        'data': 50e+6,  # bits - 50 Mb
        'rate': 1.0,  # requests per second
        'avail': 0.999,  # 99.9 %
        'max_inst': 1000,
        'demand': {
            'RAM': [50e+6, 50e+6],  # Byte - 50 MB
            'DISK': [50e+6, 50e+6]  # Byte - 50 MB
        }
    }
    mmtc = {
        'type': 'MMTC',
        'deadline': 1.0,  # second
        'work': 10e+6,  # MI (Millions of Instructions)
        'data': 100e+3,  # bits - 100 Kb
        'rate': 1.0,  # requests per second
        'avail': 0.99,  # 99.0 %
        'max_inst': 1000,
        'demand': {
            'RAM': [100e+3, 100e+3],  # Byte - 100 KB
            'DISK': [100e+3, 100e+3]  # Byte - 100 KB
        }
    }
    urllc = {
        'type': 'URLLC',
        'deadline': 0.001,  # seconds or 1 ms
        'work': 10e+6,  # MI (Millions of Instructions)
        'data': 100e+3,  # bits - 100 Kb
        'rate': 1.0,  # requests per second
        'avail': 0.9999,  # 99.99 %
        'max_inst': 1000,
        'demand': {
            'RAM': [100e+3, 100e+3],  # Byte - 100 KB
            'DISK': [100e+3, 100e+3]  # Byte - 100 KB
        }
    }

    # Generate apps' properties
    apps = [embb, mmtc, urllc]
    json_data = {'apps': []}
    for (app_id, app) in enumerate(apps):
        app = copy.copy(app)
        app['id'] = app_id

        # Create linear estimator that satisfies the queue and deadline constraints
        # f(x) = ax + b
        cpu_linear_a = app['work'] + 1.0
        cpu_linear_b = app['work'] / float(app['deadline']) + 1.0
        app['demand']['CPU'] = [cpu_linear_a, cpu_linear_b]
        json_data['apps'].append(app)

    return json_data


def gen_users(apps_data, bbox):
    """Generate users
    Args:
        apps_data (dict): applications data in json format
        bbox (BoundBox): bound box of the users' positions
    Returns:
        dict: users in json format
    """
    cabs_pathname = DATA_PATH + 'cabs/new_*.txt'
    cabs_filename = glob(cabs_pathname)
    pos_pathname = DATA_PATH + 'users_position/'
    sf_tz = timezone('America/Los_Angeles')  # San Francisco timezone
    start_time = sf_tz.localize(datetime(2008, 5, 24, 0, 0, 0)).timestamp()
    stop_time = sf_tz.localize(datetime(2008, 5, 24, 23, 59, 59)).timestamp()
    # apps_distribution = {'EMBB': 0.3, 'MMTC': 0.65, 'URLLC': 0.05}
    apps_distribution = {'EMBB': 0.3, 'MMTC': 0.5, 'URLLC': 0.2}
    # apps_distribution = {'EMBB': 0.2, 'MMTC': 0.7, 'URLLC': 0.1}

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
                in_interval = start_time <= time <= stop_time
                in_interval = in_interval and (bbox.x_min <= lon <= bbox.x_max)
                in_interval = in_interval and (bbox.y_min <= lat <= bbox.y_max)
                if in_interval:
                    pos = {'lat': lat, 'lon': lon, 't': time}
                    positions.append(pos)

        # Only create a user if the taxi has GPS traces during the selected time interval
        if len(positions) > 0:
            user_id = len(json_data['users'])
            # Save the position traces in a separated file
            pos_filename = pos_pathname + 'user_{}.json'.format(user_id)
            with open(pos_filename, mode='w') as json_file:
                json.dump(positions, json_file)

            # Set user's properties
            user = {'id': user_id, 'pos': pos_filename}
            json_data['users'].append(user)

    # Distribute users among the generated applications
    nb_users = len(json_data['users'])
    # Calculate number of users for each type of application
    app_types_nb_users = {app_type: int(math.floor(nb_users * dist))
                          for (app_type, dist) in iteritems(apps_distribution)}
    # Calculate number of apps per type
    nb_apps_per_type = {app_type: sum(map(lambda a: a['type'] == app_type, apps_data['apps']))
                        for app_type in apps_distribution.keys()}

    # Map each user to an application according to the calculated distribution
    last_user_id = 0
    for app in apps_data['apps']:
        app_id = app['id']
        app_type = app['type']
        # applications with same type receive an equal amount of users
        app_nb_users = int(math.floor(app_types_nb_users[app_type] / nb_apps_per_type[app_type]))
        for index in range(app_nb_users):
            user_id = last_user_id + index
            json_data['users'][user_id]['app_id'] = app_id
        last_user_id += app_nb_users

    # Remaining users are mapped to a single MMTC application
    if last_user_id < nb_users:
        app_id = 0
        for app in apps_data['apps']:
            if app['type'] == 'MMTC':
                app_id = app['id']
                break
        for user_id in range(last_user_id, nb_users):
            json_data['users'][user_id]['app_id'] = app_id

    return json_data


if __name__ == '__main__':
    main()