from sp.core.model import Scenario
from sp.simulator import Simulator, Monitor
from datetime import datetime
from pytz import timezone
import json
import glob
import time
import os
import pandas as pd
import matplotlib.pyplot as plt

UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)


def plot_placement(scenario):
    path = 'output/san_francisco/exp/'
    optimizers = [
        {'key': 'CloudOptimizer', 'label': 'Cloud'},
        {'key': 'SOHeuristicOptimizer', 'label': 'SOH'},
        {'key': 'MOGAOptimizer', 'label': 'MOGA'},
        {'key': 'SOGAOptimizer', 'label': 'SOGA'},
        {'key': 'LLCOptimizer', 'label': 'LLC'}
    ]

    files = [os.path.join(path, opt['key'], 'placement.json') for opt in optimizers]
    list_df = [pd.read_json(file, orient='records') for file in files]
    for (index, df) in enumerate(list_df):
        df['opt'] = optimizers[index]['label']

    df = pd.concat(list_df)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df.set_index(['time'], inplace=True)
    df.sort_index(inplace=True)
    df = df.tz_convert(SF_TZ_STR)

    nb_axes = len(scenario.apps)
    nb_cols = 1
    nb_rows = nb_axes // nb_cols
    if nb_rows * nb_cols < nb_axes:
        nb_rows += 1
    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))

    df['place'] = df['place'].astype(int)
    for (app_index, app) in enumerate(scenario.apps):
        ax_row = app_index // nb_cols
        ax_col = app_index % nb_cols
        ax = axes[ax_row, ax_col]
        ax.set_title('App {} (id {})'.format(app.type, app.id))

        app_df = df[df['app'] == app.id]
        place_df = app_df.groupby(['time', 'opt'])['place'].sum()
        # y_min, y_max = place_df.min(), place_df.max()
        # y_tics = range(0, y_max + 1) if y_max > 1 else [0, 1, 2]
        # place_df.unstack().plot(ax=ax, legend=False, yticks=y_tics)
        place_df.unstack().plot(ax=ax, legend=False)

    axes[0, 0].legend()
    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= nb_axes:
                axes[row, col].remove()

    fig.tight_layout()
    plt.show()


def plot_metrics(scenario):
    path = 'output/san_francisco/exp/'
    optimizers = [
        {'key': 'CloudOptimizer', 'label': 'Cloud'},
        # {'key': 'SOHeuristicOptimizer', 'label': 'SOH'},
        {'key': 'MOGAOptimizer', 'label': 'MOGA'},
        # {'key': 'SOGAOptimizer', 'label': 'SOGA'},
        {'key': 'LLCOptimizer', 'label': 'LLC'},
        # {'key': 'LLCOptimizer_2', 'label': 'LLC 2'},
        # {'key': 'LLCOptimizer_3', 'label': 'LLC 3'},
        # {'key': 'LLCOptimizer_4', 'label': 'LLC 4'}
    ]
    metrics = [
        {'key': 'max_deadline_violation', 'label': 'deadline violation - s'},
        {'key': 'overall_cost', 'label': 'allocation cost'},
        {'key': 'avg_unavailability', 'label': 'avg. unavailability'},
        {'key': 'overall_migration_cost', 'label': 'migration cost'},
        {'key': 'elapsed_time', 'label': 'exec time - s'}
    ]

    files = [os.path.join(path, opt['key'], 'metrics.json') for opt in optimizers]
    list_df = [pd.read_json(file, orient='records') for file in files]

    df = pd.concat(list_df)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df.set_index(['time'], inplace=True)
    df.sort_index(inplace=True)
    df = df.tz_convert(SF_TZ_STR)

    nb_cols = 3
    nb_rows = len(metrics) // nb_cols
    if nb_rows * nb_cols < len(metrics):
        nb_rows += 1
    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))

    grouped_df = df.groupby('opt')
    for (metric_index, metric) in enumerate(metrics):
        ax_row = metric_index // nb_cols
        ax_col = metric_index % nb_cols
        ax = axes[ax_row, ax_col]

        grouped_df[metric['key']].plot(ax=ax)
        ax.set_ylabel(metric['label'])

    axes[0, 0].legend()
    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= len(metrics):
                axes[row, col].remove()

    fig.tight_layout()
    plt.show()


def main():
    scenario_filename = 'input/san_francisco/scenario.json'
    scenario = None
    with open(scenario_filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)

    plot_metrics(scenario)
    # plot_placement(scenario)


if __name__ == '__main__':
    main()