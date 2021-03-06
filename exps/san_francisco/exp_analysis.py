from sp.core.model import Scenario
from sp.simulator import Simulator, Monitor
from datetime import datetime
from future.utils import iteritems
from pytz import timezone
from glob import glob
import json
import time
import os
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as st


UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)


def load_opts_df(optimizers, output_path, filename, nb_runs):
    opts_df = {}

    stop_time = SF_TZ.localize(datetime(2008, 5, 24, 23, 59, 59))

    for opt in optimizers:
        opt_df = []
        for run in range(nb_runs):
            file = os.path.join(output_path, str(run), opt['id'], filename)
            if not os.path.isfile(file):
                continue
            df = pd.read_json(file, orient='records')
            df['run'] = run
            df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
            df = df[df['time'] <= stop_time]
            opt_df.append(df)

        opt_df = pd.concat(opt_df)
        opt_df.set_index(['time'], inplace=True)
        opt_df.sort_index(inplace=True)
        opts_df[opt['id']] = opt_df

    return opts_df


def calc_stats(df, columns, group_by='time'):
    if not isinstance(columns, list):
        columns = [columns]

    confidence_alpha = 0.95
    stats_df = df[columns].groupby(group_by).agg(['mean', 'count', 'sem'])
    data = {}
    for col in columns:
        values = []
        errors = []
        for i in stats_df.index:
            m, c, s = stats_df.loc[i, col]
            error = 0.0
            if s > 0.0:
                ci = st.t.interval(confidence_alpha, c - 1, loc=m, scale=s)
                error = ci[1] - m
            values.append(m)
            errors.append(error)
        data[col] = values
        data[col + '_error'] = errors

    return pd.DataFrame(data=data, index=stats_df.index)


def plot_metrics(optimizers, output_path, nb_runs):
    metrics = [
        {'id': 'overall_deadline_violation', 'label': 'overall deadline violation - s'},
        {'id': 'weighted_avg_deadline_violation', 'label': 'w. avg. deadline violation - s'},
        # {'id': 'max_deadline_violation', 'label': 'max. deadline violation - s'},
        # {'id': 'deadline_satisfaction', 'label': 'deadline satisfaction - %'},
        {'id': 'overall_cost', 'label': 'allocation cost'},
        {'id': 'overall_migration_cost', 'label': 'migration cost'},
        {'id': 'weighted_migration_rate', 'label': 'w. migration rate'},
        {'id': 'overall_response_time', 'label': 'overall response time'},
        {'id': 'weighted_avg_response_time', 'label': 'w. avg. response time'},
        {'id': 'elapsed_time', 'label': 'exec time - s'}
    ]
    metrics_id = [m['id'] for m in metrics]
    list_df = []
    opts_df = load_opts_df(optimizers, output_path, 'metrics.json', nb_runs)
    for opt in optimizers:
        opt_df = opts_df[opt['id']]
        opt_df = calc_stats(opt_df, metrics_id)
        opt_df['opt'] = opt['label']
        list_df.append(opt_df)

    df = pd.concat(list_df)
    df.sort_index(inplace=True)
    df = df.tz_convert(SF_TZ_STR)

    nb_axes = len(metrics)
    nb_cols = 2
    nb_rows = nb_axes // nb_cols
    if nb_rows * nb_cols < nb_axes:
        nb_rows += 1
    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))

    for (metric_index, metric) in enumerate(metrics):
        ax_row = metric_index // nb_cols
        ax_col = metric_index % nb_cols
        ax = axes[ax_row, ax_col]
        ax.set_ylabel(metric['label'])

        value_col = metric['id']
        error_col = metric['id'] + '_error'

        metric_df = df.pivot(columns='opt', values=value_col)
        error_df = df.pivot(columns='opt', values=error_col)

        # metric_df.plot(ax=ax, yerr=error_df, legend=False)
        metric_df.plot(ax=ax, legend=False)

        # if metric['id'] == 'overall_deadline_violation':
        #     ax.set_ylim(0.0, 0.2)

        # if metric['id'] == 'deadline_satisfaction':
        #     ax.set_ylim(0.0, 1.0)

    axes[0, 0].legend(ncol=2)
    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= nb_axes:
                axes[row, col].remove()

    fig.tight_layout()
    plt.show()


def plot_placement(scenario, optimizers, output_path, nb_runs):
    opts_df = load_opts_df(optimizers, output_path, 'placement.json', nb_runs)
    list_df = []
    for opt in optimizers:
        opt_df = opts_df[opt['id']]
        opt_df['place'] = opt_df['place'].astype(int)
        opt_df = opt_df.groupby(['time', 'app', 'run'])['place'].sum()
        opt_df = opt_df.reset_index(level=['run'])
        opt_df = calc_stats(opt_df, 'place', group_by=['time', 'app'])
        opt_df = opt_df.reset_index(level=['app'])
        opt_df['opt'] = opt['label']
        list_df.append(opt_df)

    df = pd.concat(list_df)
    df.sort_index(inplace=True)
    df = df.tz_convert(SF_TZ_STR)

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
        ax.set_ylabel('Number of instances')
        ax.set_title('App {} (id {})'.format(app.type, app.id))
        ax.set_yticks(range(len(scenario.network.nodes) + 1))

        app_df = df[df['app'] == app.id]
        place_df = app_df.pivot(columns='opt', values='place')
        error_df = app_df.pivot(columns='opt', values='place_error')

        place_df.plot(ax=ax, yerr=error_df, legend=False)
        # place_df.plot(ax=ax, legend=False)

    axes[0, 0].legend()
    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= nb_axes:
                axes[row, col].remove()

    fig.tight_layout()
    plt.show()


def plot_placement_total(optimizers, output_path, nb_runs):
    opts_df = load_opts_df(optimizers, output_path, 'placement.json', nb_runs)
    list_df = []
    for opt in optimizers:
        opt_df = opts_df[opt['id']]
        opt_df['place'] = opt_df['place'].astype(int)
        opt_df = opt_df.groupby(['time', 'run'])['place'].sum()
        opt_df = opt_df.reset_index(level=['run'])
        opt_df = calc_stats(opt_df, 'place')
        opt_df['opt'] = opt['label']
        list_df.append(opt_df)

    df = pd.concat(list_df)
    df.sort_index(inplace=True)
    df = df.tz_convert(SF_TZ_STR)

    fig, ax = plt.subplots(figsize=(16, 9))

    ax.set_ylabel('Number of instances')

    place_df = df.pivot(columns='opt', values='place')
    error_df = df.pivot(columns='opt', values='place_error')

    # place_df.plot(ax=ax, yerr=error_df, legend=False)
    place_df.plot(ax=ax, legend=False)

    ax.legend()
    fig.tight_layout()
    plt.show()


def main():
    scenario_filename = 'input/san_francisco/scenario.json'
    scenario = None
    # with open(scenario_filename) as json_file:
    #     data = json.load(json_file)
    #     scenario = Scenario.from_json(data)

    # output_path = 'output/san_francisco/exp/'
    # output_path = 'output/san_francisco/exp/a10_1211612400_1211698799/'
    # output_path = 'output/san_francisco/exp/a4_1211612400_1211698799/'
    # output_path = 'output/san_francisco/exp/a1_1211612400_1211698799/'
    # output_path = 'output/san_francisco/exp/a4_eyJuYl9hcHBzIjogNCwgInRpbWUiOiB7InN0ZXAiOiAzNjAwfX0='
    # output_path = 'output/san_francisco/exp/a4_eyJuYl9hcHBzIjogNCwgInRpbWUiOiB7InN0ZXAiOiAyNzAwfX0='
    # output_path = 'output/san_francisco/exp/a4_eyJuYl9hcHBzIjogNCwgInRpbWUiOiB7InN0ZXAiOiAxODAwfX0='
    # output_path = 'output/san_francisco/exp/a4_eyJuYl9hcHBzIjogNCwgInRpbWUiOiB7InN0ZXAiOiA5MDB9fQ=='
    # output_path = 'output/san_francisco/exp/a1_eyJuYl9hcHBzIjogMX0=/'
    # output_path = 'output/san_francisco/exp_2/a1_eyJuYl9hcHBzIjogMX0=/'
    # output_path = 'output/san_francisco/exp/a4_eyJuYl9hcHBzIjogNH0=/'
    # output_path = 'output/san_francisco/exp/a5_eyJuYl9hcHBzIjogNX0=/'
    # output_path = 'output/san_francisco/exp/a7_eyJuYl9hcHBzIjogN30=/'
    # output_path = 'output/san_francisco/exp/a10_eyJuYl9hcHBzIjogMTB9/'
    # output_path = 'output/san_francisco/exp/a200/'
    # output_path = 'output/san_francisco/exp/a100/'
    output_path = 'output/san_francisco/exp/a50/'
    # output_path = 'output/san_francisco/exp/a35/'
    # output_path = 'output/san_francisco/exp/a20/'
    # output_path = 'output/san_francisco/exp/a5/'
    optimizers = [
        # {'id': 'CloudOptimizer', 'label': 'Cloud'},
        # {'id': 'StaticOptimizer', 'label': 'Static'},
        {'id': 'SOHeuristicOptimizer', 'label': 'N+D'},
        {'id': 'SOHeuristicOptimizer_ld', 'label': 'L+D'},
        # {'id': 'OmittedMigrationOptimizer', 'label': 'Omit Migration'},
        {'id': 'MOGAOptimizer', 'label': 'H1'},
        # {'id': 'LLCOptimizer_ssga_w1', 'label': 'SS H=2'},
        # {'id': 'LLCOptimizer_sga_w1', 'label': 'GS H=2'},
    ]

    # run_dirs = glob(os.path.join(output_path, '[0-9]*/'))
    # nb_runs = len(run_dirs)
    nb_runs = 30

    plot_metrics(optimizers, output_path, nb_runs)
    # plot_placement_total(optimizers, output_path, nb_runs)
    # plot_placement(scenario, optimizers, output_path, nb_runs)


if __name__ == '__main__':
    main()
