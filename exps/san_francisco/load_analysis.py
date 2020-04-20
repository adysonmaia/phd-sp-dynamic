from sp.core.model import Scenario
from sp.core.geometry.point.gps import GpsPoint
from sp.simulator import Simulator, Monitor
from datetime import datetime, timedelta
from pytz import timezone
from cycler import cycler
from matplotlib.colors import to_hex
import matplotlib.pyplot as plt
import json
import time
import pandas as pd
import geopandas as gpd
import numpy as np


UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)
SF_SHAPE_FILE = 'input/san_francisco/shapefile/bay_area_zip_codes/geo_export_2defef9a-b2e1-4ddd-84f6-1a131dd80410.shp'


class EnvMonitor(Monitor):
    def __init__(self, load_filename, users_filename):
        Monitor.__init__(self)
        self.load_data = list()
        self.users_data = list()
        self.load_filename = load_filename
        self.users_filename = users_filename

    def on_sim_started(self, sim_time):
        self.load_data.clear()
        self.users_data.clear()

    def on_env_ctrl_ended(self, sim_time, system, environment_input):
        print(datetime.fromtimestamp(sim_time, tz=UTC_TZ).astimezone(SF_TZ))

        for app in system.apps:
            for node in system.nodes:
                load = environment_input.get_generated_load(app.id, node.id)
                datum = {'time': sim_time, 'app': app.id, 'node': node.id, 'load': load}
                self.load_data.append(datum)

        for user in environment_input.get_attached_users():
            lon, lat = None, None
            if user.position is not None and isinstance(user.position, GpsPoint):
                lon, lat = user.position.lon_lat
            datum = {'time': sim_time, 'user': user.id, 'app': user.app_id,
                     'node': user.node_id, 'lon': lon, 'lat': lat}
            self.users_data.append(datum)

    def on_sim_ended(self, sim_time):
        with open(self.load_filename, 'w') as file:
            json.dump(self.load_data, file, indent=2)

        with open(self.users_filename, 'w') as file:
            json.dump(self.users_data, file, indent=2)


def plot_load_by_app(scenario, df):
    bs_nodes_id = [node.id for node in scenario.network.bs_nodes]
    df = df.tz_convert(SF_TZ_STR)
    df = df[df['node'].isin(bs_nodes_id)]

    nb_axes = len(scenario.apps)
    nb_cols = 1
    nb_rows = nb_axes // nb_cols
    if nb_rows * nb_cols < nb_axes:
        nb_rows += 1

    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))
    for (app_index, app) in enumerate(scenario.apps):
        ax_row = app_index // nb_cols
        ax_col = app_index % nb_cols
        ax = axes[ax_row, ax_col]

        ax.set_ylabel('Load')
        ax.set_title('App {} (id {})'.format(app.type, app.id))

        app_df = df[df['app'] == app.id]
        load_df = app_df.groupby('time')['load'].sum()
        load_df.plot(ax=ax, legend=False)

    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= nb_axes:
                axes[row, col].remove()

    fig.tight_layout()
    plt.show()


def plot_load_by_app_node(scenario, df):
    bs_nodes_id = [node.id for node in scenario.network.bs_nodes]
    df = df.tz_convert(SF_TZ_STR)
    df = df[df['node'].isin(bs_nodes_id)]

    cm = plt.cm.get_cmap('gist_rainbow')
    colors = cm(np.linspace(0, 1, len(bs_nodes_id)))
    colors = [to_hex(color, keep_alpha=True) for color in colors]

    colors = ['red', 'blue', 'green', 'pink',
              '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
              'dimgray', 'darkred', 'darkolivegreen', 'darkgoldenrod',
              'darkcyan', 'midnightblue', 'darkviolet', 'tan',
              'lightcoral', 'lightgreen', 'lightblue'] + colors

    nb_axes = len(scenario.apps) + 1
    nb_cols = 2
    nb_rows = nb_axes // nb_cols
    if nb_rows * nb_cols < nb_axes:
        nb_rows += 1

    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))
    for (app_index, app) in enumerate(scenario.apps):
        ax_row = app_index // nb_cols
        ax_col = app_index % nb_cols
        ax = axes[ax_row, ax_col]

        ax.set_ylabel('Load')
        ax.set_prop_cycle(cycler('color', colors))
        ax.set_title('App {} (id {})'.format(app.type, app.id))
        grouped_df = df[df['app'] == app.id].groupby('node')
        grouped_df['load'].plot(ax=ax)

    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= nb_axes:
                axes[row, col].remove()

    legend = axes[0, 0].legend(ncol=5, loc='upper right', handlelength=0.5, columnspacing=1.0)
    for line in legend.get_lines():
        line.set_linewidth(5.0)

    legend_handles_labels = axes[0, 0].get_legend_handles_labels()
    ax_row = (nb_axes - 1) // nb_cols
    ax_col = (nb_axes - 1) % nb_cols
    ax = axes[ax_row, ax_col]
    plot_map(scenario, ax, legend_handles_labels)

    fig.tight_layout()
    plt.show()


def plot_load_by_node(scenario, df):
    bs_nodes = scenario.network.bs_nodes
    bs_nodes_id = [node.id for node in bs_nodes]
    df = df.tz_convert(SF_TZ_STR)
    df = df[df['node'].isin(bs_nodes_id)]

    cm = plt.cm.get_cmap('gist_rainbow')
    colors = cm(np.linspace(0, 1, len(bs_nodes_id)))
    colors = [to_hex(color, keep_alpha=True) for color in colors]

    colors = ['red', 'blue', 'green', 'pink',
              '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
              'dimgray', 'darkred', 'darkolivegreen', 'darkgoldenrod',
              'darkcyan', 'midnightblue', 'darkviolet', 'tan',
              'lightcoral', 'lightgreen', 'lightblue'] + colors

    nb_axes = len(bs_nodes)
    nb_cols = 5
    nb_rows = nb_axes // nb_cols
    if nb_rows * nb_cols < nb_axes:
        nb_rows += 1
    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))

    load_min, load_max = df['load'].min(), df['load'].max()
    df['app_label'] = df['app'].map(lambda app_id: 'app {} (id {})'.format(scenario.get_app(app_id).type, int(app_id)))

    for (node_index, node) in enumerate(bs_nodes):
        ax_row = node_index // nb_cols
        ax_col = node_index % nb_cols
        ax = axes[ax_row, ax_col]
        ax.set_ylabel('Load')
        ax.set_prop_cycle(cycler('color', colors))
        ax.set_title('Node {}'.format(node.id))
        ax.set_ylim(load_min, load_max)

        # node_df = df[df['node'] == node.id]
        # load_df = node_df.groupby(['time', 'app_label'])['load'].sum().unstack()
        # load_df.plot(ax=ax, legend=False)

        grouped_df = df[df['node'] == node.id].groupby('app_label')
        grouped_df['load'].plot(ax=ax)

    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= nb_axes:
                axes[row, col].remove()

    axes[0, 0].legend(ncol=3)
    for ax in fig.get_axes():
        ax.label_outer()
    fig.tight_layout()
    plt.show()


def plot_map(scenario, ax=None, legend_handles_labels=None):
    nodes_data = []
    for node in scenario.network.bs_nodes:
        item = {'node': node.id, 'lat': node.position.lat, 'lon': node.position.lon}
        nodes_data.append(item)
    nodes_df = pd.DataFrame.from_records(nodes_data)
    nodes_gdf = gpd.GeoDataFrame(nodes_df,
                                 geometry=gpd.points_from_xy(nodes_df['lon'], nodes_df['lat']),
                                 crs="EPSG:4326")
    bbox = nodes_gdf.total_bounds.tolist()
    map_gdf = gpd.read_file(SF_SHAPE_FILE)
    map_gdf = map_gdf.to_crs(nodes_gdf.crs)
    map_gdf = map_gdf.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]

    show_plot = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(16, 9))
        ax.set_aspect('equal')
        show_plot = True

    for (node_index, node) in nodes_gdf.iterrows():
        try:
            color = 'white'
            edge_color = 'black'
            node_id = node['node']
            if legend_handles_labels is not None:
                handle_index = legend_handles_labels[1].index(str(node_id))
                handle = legend_handles_labels[0][handle_index]
                color = handle.get_color()
                edge_color = 'lightgray'
            pos = node.geometry
            region = map_gdf[map_gdf.contains(pos)]
            region.plot(ax=ax, color=color, edgecolor=edge_color, zorder=0)
            ax.text(pos.x-0.001, pos.y-0.001, str(node_id), zorder=1)
        except ValueError:
            pass

    if show_plot:
        # plt.legend()
        plt.show()


def plot_users(scenario, load_df, users_df):
    crs = "EPSG:4326"

    load_df = load_df.tz_convert(SF_TZ_STR)
    users_df = users_df.tz_convert(SF_TZ_STR)

    nodes_data = []
    for node in scenario.network.bs_nodes:
        item = {'node': node.id, 'lat': node.position.lat, 'lon': node.position.lon}
        nodes_data.append(item)
    nodes_df = pd.DataFrame.from_records(nodes_data)
    nodes_gdf = gpd.GeoDataFrame(nodes_df, geometry=gpd.points_from_xy(nodes_df['lon'], nodes_df['lat']), crs=crs)
    bbox = nodes_gdf.total_bounds.tolist()

    users_df = users_df[users_df['node'].notna()]
    users_gdf = gpd.GeoDataFrame(users_df, geometry=gpd.points_from_xy(users_df['lon'], users_df['lat']), crs=crs)
    # users_gdf = users_gdf.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]

    map_gdf = gpd.read_file(SF_SHAPE_FILE)
    map_gdf = map_gdf.to_crs(crs)
    map_gdf = map_gdf.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    map_bbox = map_gdf.total_bounds.tolist()

    time_series = pd.period_range(load_df.index.min(), load_df.index.max(), freq='4H')
    time_series = [period.start_time for period in time_series]
    time_delta = timedelta(minutes=10)

    nb_cols = 3
    nb_rows = len(time_series) // nb_cols
    if nb_rows * nb_cols < len(time_series):
        nb_rows += 1
    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))
    cm = plt.cm.get_cmap('gist_rainbow')
    colors = cm(np.linspace(0, 1, len(scenario.apps)))
    colors = [to_hex(color, keep_alpha=True) for color in colors]
    colors = ['r', 'g', 'b', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'] + colors

    for (t_index, t) in enumerate(time_series):
        start_t = t
        end_t = start_t + time_delta
        current_users_gdf = users_gdf[start_t:end_t].drop_duplicates(subset='user')

        ax_row = t_index // nb_cols
        ax_col = t_index % nb_cols
        ax = axes[ax_row, ax_col]
        ax.set_aspect('equal')

        ax.set_title(t)
        map_gdf.plot(ax=ax, color='#FFFFFF00', edgecolor='black', zorder=1)
        nodes_gdf.plot(ax=ax, color='k', markersize=15, zorder=1, label='edge node')
        for (app_index, app) in enumerate(scenario.apps):
            app_users_gdf = current_users_gdf[current_users_gdf['app'] == app.id]
            color = colors[app_index]
            label = 'app {} {} (usr {})'.format(app.id, app.type, len(app_users_gdf))
            app_users_gdf.groupby('app').plot(ax=ax, color=color, markersize=2, zorder=0, label=label)

        ax.legend(ncol=2, loc='upper right', columnspacing=0.5, handletextpad=0.0)

    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= len(time_series):
                axes[row, col].remove()

    fig.tight_layout()
    plt.show()


def run_sim(scenario, load_filename, users_filename):
    # Set simulation time based on San Francisco timezone
    start_time = SF_TZ.localize(datetime(2008, 5, 24, 0, 0, 0)).timestamp()
    stop_time = SF_TZ.localize(datetime(2008, 5, 24, 23, 59, 59)).timestamp()
    step_time = 10 * 60  # seconds or 10 min
    # step_time = 60 * 60  # seconds or 1H

    # Set simulation parameters
    sim = Simulator(scenario=scenario)
    sim.set_time(stop=stop_time, start=start_time, step=step_time)
    sim.monitor = EnvMonitor(load_filename=load_filename, users_filename=users_filename)

    # Run simulation
    perf_count = time.perf_counter()
    sim.run()
    elapsed_time = time.perf_counter() - perf_count
    print('sim exec time: {}s'.format(elapsed_time))


def data_analysis(scenario, load_filename, users_filename):
    file_names = [load_filename, users_filename]
    data_frames = []

    for filename in file_names:
        df = pd.read_json(filename, orient='records')
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df.set_index(['time'], inplace=True)
        df.sort_index(inplace=True)
        data_frames.append(df)

    load_df, users_df = data_frames

    # plot_load_by_app(scenario, load_df)
    # plot_load_by_app_node(scenario, load_df)
    # plot_load_by_node(scenario, load_df)
    plot_users(scenario, load_df, users_df)
    # plot_map(scenario)


def main():
    scenario_filename = 'input/san_francisco/scenario.json'
    load_filename = 'output/san_francisco/load_analysis/load.json'
    users_filename = 'output/san_francisco/load_analysis/users.json'
    scenario = None
    with open(scenario_filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)

    # run_sim(scenario, load_filename, users_filename)
    data_analysis(scenario, load_filename, users_filename)


if __name__ == '__main__':
    main()
