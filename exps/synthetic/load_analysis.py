from sp.core.model import Scenario
from sp.simulator import Simulator, Monitor
from datetime import datetime, timedelta
from cycler import cycler
from matplotlib.colors import to_hex
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import time
import os


class EnvMonitor(Monitor):
    def __init__(self, load_filename):
        Monitor.__init__(self)
        self.load_data = list()
        self.load_filename = load_filename

    def on_sim_started(self, sim_time):
        self.load_data.clear()

    def on_env_ctrl_ended(self, sim_time, system, environment_input):
        print(sim_time)

        for app in system.apps:
            for node in system.nodes:
                load = environment_input.get_generated_load(app.id, node.id)
                datum = {'time': sim_time, 'app': app.id, 'node': node.id, 'load': load}
                self.load_data.append(datum)

    def on_sim_ended(self, sim_time):
        with open(self.load_filename, 'w') as file:
            json.dump(self.load_data, file, indent=2)


def run_sim(scenario, load_filename):
    # Set simulation time based on San Francisco timezone
    time_start = 0.0
    time_step = 60 * 60  # 1 Hour
    time_end = 50 * time_step + time_start

    # Set simulation parameters
    sim = Simulator(scenario=scenario)
    sim.set_time(stop=time_end, start=time_start, step=time_step)
    sim.monitor = EnvMonitor(load_filename=load_filename)

    # Run simulation
    perf_count = time.perf_counter()
    sim.run()
    elapsed_time = time.perf_counter() - perf_count
    print('sim exec time: {}s'.format(elapsed_time))


def data_analysis(scenario, load_filename):
    df = pd.read_json(load_filename, orient='records')
    df.set_index(['time'], inplace=True)
    df.sort_index(inplace=True)

    plot_load_by_app(scenario, df)
    # plot_load_by_app_node(scenario, df)


def plot_load_by_app(scenario, df):
    bs_nodes_id = [node.id for node in scenario.network.bs_nodes]
    df = df[df['node'].isin(bs_nodes_id)]

    load_df = df.groupby(['time', 'app'])['load'].sum()
    min_load, max_load = load_df.min(), load_df.max()

    nb_axes = len(scenario.apps)
    nb_cols = 5
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
        ax.set_ylim(min_load, max_load)

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

    nb_axes = len(scenario.apps)
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

    fig.tight_layout()
    plt.show()


def main():
    nb_bs = 25
    nb_apps = 10
    nb_users = 1000
    scenario_id = 'n{}_a{}_u{}'.format(nb_bs, nb_apps, nb_users)
    scenario_filename = 'input/synthetic/scenario_{}.json'.format(scenario_id)
    output_path = 'output/synthetic/load_analysis/'
    load_filename = os.path.join(output_path, 'load.json')

    scenario = None
    with open(scenario_filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)

    try:
        os.makedirs(output_path)
    except OSError:
        pass

    # run_sim(scenario, load_filename)
    data_analysis(scenario, load_filename)


if __name__ == '__main__':
    main()
