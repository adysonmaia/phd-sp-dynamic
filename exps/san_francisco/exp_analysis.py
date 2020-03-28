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


def metrics_analysis(scenario):
    path = 'output/san_francisco/exp/'
    optimizers = [
        {'key': 'CloudOptimizer', 'label': 'Cloud'},
        {'key': 'MOGAOptimizer', 'label': 'MOGA'},
        # {'key': 'LLCOptimizer', 'label': 'LLC'},
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

    metrics_analysis(scenario)


if __name__ == '__main__':
    main()