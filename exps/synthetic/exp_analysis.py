from glob import glob
from itertools import cycle, islice
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import faulthandler
faulthandler.enable()


def s_to_ms(value):
    return 1000.0 * value


def to_percent(value):
    return 100.0 * value


def bool_to_int(value):
    return int(value)


def plot_metrics(optimizers, experiments, metrics, data_path, x_label):
    cloud_opt_id = 'CloudOptimizer'

    metrics_data = []
    for exp in experiments:
        exp_path = os.path.join(data_path, exp['path'], '[0-9]*')
        runs_path = glob(exp_path)
        for opt in optimizers:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt['id'], 'metrics.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')

                cloud_filename = os.path.join(run_path, cloud_opt_id, 'metrics.json')
                cloud_df = None
                if os.path.isfile(cloud_filename):
                    cloud_df = pd.read_json(cloud_filename, orient='records')

                data = {'opt': opt['label'], 'run': run, 'x': exp['x']}
                for metric in metrics:
                    metric_id = metric['id']
                    if metric_id not in df.columns:
                        continue

                    value = df[metric_id].mean()
                    cloud_value = cloud_df[metric_id].mean() if cloud_df is not None else 0.0
                    if 'func' in metric:
                        value = metric['func'](value)
                        cloud_value = metric['func'](cloud_value)
                    if 'normalize' in metric and metric['normalize'] and cloud_value > 0.0:
                        value = value / float(cloud_value)
                    data[metric_id] = value
                metrics_data.append(data)

    metrics_df = pd.DataFrame.from_records(metrics_data)

    sns.set()
    sns.set_context('paper', font_scale=2.0)
    sns.set_style('ticks', {'axes.grid': True, 'grid.linestyle': '--'})

    # metric_id = 'weighted_avg_deadline_violation'
    metric_id = 'weighted_migration_rate'
    print(metrics_df.groupby(['x', 'opt'])[metric_id].mean())
    exit()

    # sns.relplot(x='x', y=metric_id, hue='opt', kind='line', data=metrics_df)
    # sns.catplot(x='x', y=metric_id, hue='opt', kind='point', ci=None, data=metrics_df, facet_kws=dict(despine=False))
    # sns.pointplot(x='x', y=metric_id, hue='opt', ci=None, data=metrics_df)
    # sns.catplot(x='x', y=metric_id, hue='opt', kind='point', col='run', col_wrap=10, ci=None, data=metrics_df)
    # sns.catplot(x='x', y=metric_id, hue='opt', kind='bar', ci=95, data=metrics_df)
    # sns.boxplot(x='x', y=metric_id, hue='opt', notch=False, data=metrics_df)
    # print(sns.axes_style())
    # plt.show()

    markers_unique = ['o', 's', 'd', '^', 'v', '<']
    opt_count = metrics_df['opt'].nunique()
    markers = list(islice(cycle(markers_unique), opt_count))

    # for metric in metrics:
    #     metric_id = metric['id']
    #     ax = sns.pointplot(x='x', y=metric_id, hue='opt', kind='point', ci=None, data=metrics_df,
    #                        height=5, aspect=1.5, markers=markers)
    #     ax.xaxis.grid(True)
    #     ax.set_xlabel(x_label)
    #     ax.set_ylabel(metric['label'])
    #     if 'legend_pos' in metric:
    #         legend_pos = metric['legend_pos']
    #         ax.legend(loc='center', ncol=3, title=None,
    #                   bbox_to_anchor=legend_pos,
    #                   columnspacing=0.0, labelspacing=0.0, handletextpad=0.0)
    #     else:
    #         ax.legend(loc='best', ncol=3, title=None,
    #                   columnspacing=0.0, labelspacing=0.0, handletextpad=0.0)
    #     plt.subplots_adjust(bottom=0.14, top=0.995, left=0.14, right=0.995)
    #     if 'fig_file' in metric:
    #         # plt.savefig(metric['fig_file'], dpi=100, bbox_inches='tight')
    #         plt.savefig(metric['fig_file'], dpi=100)
    #         plt.clf()
    #     else:
    #         plt.show()


def plot_metrics_over_time(optimizers, experiments, metrics, output_path):
    data = []
    for exp in experiments:
        exp_path = os.path.join(output_path, exp['path'], '[0-9]*')
        runs_path = glob(exp_path)
        for opt in optimizers:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt['id'], 'metrics.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')

                for (index, row) in df.iterrows():
                    for metric in metrics:
                        metric_id = metric['id']
                        if metric_id not in df.columns:
                            continue

                        value = row[metric_id]
                        if 'func' in metric:
                            value = metric['func'](value)

                        datum = {
                            'time': row['time'],
                            'exp': exp['x'],
                            'opt': opt['label'],
                            'run': run,
                            'metric': metric_id,
                            'y': value
                        }
                        data.append(datum)

    metrics_df = pd.DataFrame.from_records(data)
    metric_id = 'weighted_avg_deadline_violation'
    # metric_id = 'avg_deadline_violation'
    # metric_id = 'max_deadline_violation'
    # metric_id = 'overall_cost'
    # metric_id = 'weighted_migration_rate'
    # metric_id = 'migration_rate'
    df = metrics_df[metrics_df['metric'] == metric_id]

    sns.set()
    # sns.set_context("paper")
    sns.set_context("notebook")
    sns.set_style("whitegrid")
    sns.relplot(x='time', y='y', hue='opt', col="exp", col_wrap=2, kind='line', ci=None, data=df)
    plt.show()


def plot_placement(optimizers, experiments, output_path):
    data = []
    for exp in experiments:
        exp_path = os.path.join(output_path, exp['path'], '[0-9]*')
        runs_path = glob(exp_path)
        for opt in optimizers:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt['id'], 'placement.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')
                df['place'] = df['place'].astype(int)
                ts = df.groupby(['time'])['place'].sum()

                nb_apps = df['app'].nunique()

                for (time, place) in ts.iteritems():
                    place_per_app = place / float(nb_apps)
                    datum = {'time': time, 'exp': exp['x'], 'opt': opt['label'], 'run': run,
                             'place': place, 'place_per_app': place_per_app}
                    data.append(datum)

    place_df = pd.DataFrame.from_records(data)
    sns.set()
    # sns.set_context("paper")
    sns.set_context("notebook")
    sns.set_style("whitegrid")

    # sns.relplot(x='exp', y='place_per_app', hue='opt', kind='line', ci=None, data=place_df)
    sns.catplot(x='exp', y='place_per_app', hue='opt', kind='point', ci=None, data=place_df)
    # sns.catplot(x='exp', y='place', hue='opt', kind='point', ci=None, data=place_df)
    plt.show()


def plot_placement_over_time(optimizers, experiments, output_path):
    data = []
    for exp in experiments:
        exp_path = os.path.join(output_path, exp['path'], '[0-9]*')
        runs_path = glob(exp_path)
        for opt in optimizers:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt['id'], 'placement.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')
                df['place'] = df['place'].astype(int)
                ts = df.groupby(['time'])['place'].sum()

                nb_apps = df['app'].nunique()

                for (time, place) in ts.iteritems():
                    place_per_app = place / float(nb_apps)
                    datum = {'time': time, 'exp': exp['x'], 'opt': opt['label'], 'run': run,
                             'place': place, 'place_per_app': place_per_app}
                    data.append(datum)

    place_df = pd.DataFrame.from_records(data)
    sns.set()
    # sns.set_context("paper")
    sns.set_context("notebook")
    sns.set_style("whitegrid")

    # sns.relplot(x='time', y='place', hue='opt', col="exp", col_wrap=2, kind='line', ci=None, data=place_df)
    sns.relplot(x='time', y='place_per_app', hue='opt', col="exp", col_wrap=2, kind='line', ci=None, data=place_df)
    plt.show()


def plot_alloc(optimizers, experiments, output_path):
    resources = ['CPU', 'RAM', 'DISK']
    data = []
    for exp in experiments:
        exp_path = os.path.join(output_path, exp['path'], '[0-9]*')
        runs_path = glob(exp_path)
        for opt in optimizers:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt['id'], 'allocation.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')

                last_node_id = df['node'].max()
                # df = df[df['node'] < last_node_id]
                df = df[df['node'] == last_node_id]

                gdf = df.groupby(['time'])
                r_ts = {r: gdf[r].sum() for r in resources}
                nb_apps = df['app'].nunique()

                place_filename = os.path.join(run_path, opt['id'], 'placement.json')
                if not os.path.isfile(place_filename):
                    continue
                place_df = pd.read_json(place_filename, orient='records')
                place_df['place'] = place_df['place'].astype(int)
                place_ts = place_df.groupby(['time'])['place'].sum()

                for r in resources:
                    ts = r_ts[r]
                    for (time, alloc) in ts.iteritems():
                        alloc_per_app = alloc / float(nb_apps)
                        alloc_per_rep = alloc / float(place_ts[time])
                        datum = {'time': time, 'exp': exp['x'], 'opt': opt['label'], 'run': run,
                                 'resource': r, 'alloc': alloc, 'alloc_per_app': alloc_per_app,
                                 'alloc_per_rep': alloc_per_rep}
                        data.append(datum)

    alloc_df = pd.DataFrame.from_records(data)
    sns.set()
    # sns.set_context("paper")
    sns.set_context("notebook")
    sns.set_style("whitegrid")

    # sns.catplot(x='exp', y='alloc', hue='opt', col="resource", kind='point', ci=None, data=alloc_df)
    sns.catplot(x='exp', y='alloc_per_app', hue='opt', col="resource", kind='point', ci=None, data=alloc_df)
    # sns.catplot(x='exp', y='alloc_per_rep', hue='opt', col="resource", kind='point', ci=None, data=alloc_df)
    plt.show()


def main():
    fig_path = 'output/synthetic/figs/'
    try:
        os.makedirs(fig_path)
    except OSError:
        pass

    # data_path = 'output/synthetic/exp_apps/'
    data_path = 'output/synthetic/exp_comp/exp_apps'
    # data_path = 'output/synthetic/exp_2020_08_31/apps_2'
    optimizers = [
        {'id': 'CloudOptimizer', 'label': 'Cloud'},
        {'id': 'StaticOptimizer', 'label': 'Static'},
        {'id': 'SOHeuristicOptimizer', 'label': 'N+D'},
        {'id': 'MOGAOptimizer', 'label': 'H1'},
        {'id': 'LLCOptimizer_ssga_w1', 'label': 'SS'},
        {'id': 'LLCOptimizer_sga_w1', 'label': 'GS'},
    ]
    experiments = [
        {'path': 'n9_a5_u10000', 'x': 5},
        {'path': 'n9_a10_u10000', 'x': 10},
        {'path': 'n9_a15_u10000', 'x': 15},
        {'path': 'n9_a20_u10000', 'x': 20},
    ]
    x_label = 'Number of Applications'
    metrics = [
        {'id': 'weighted_avg_deadline_violation',
         'label': 'Normalized Deadline Violation',
         'normalize': True,
         'legend_pos': (0.5, 0.5),
         # 'fig_file': os.path.join(fig_path, 'apps_dv.png')
         },
        # {'id': 'overall_cost',
        #  'label': 'Operational Cost',
        #  'legend_pos': (0.5, 0.3),
        #  'fig_file': os.path.join(fig_path, 'apps_oc.png')
        #  },
        {'id': 'weighted_migration_rate',
         'label': 'Migration Cost (%)',
         'func': to_percent,
         'legend_pos': (0.5, 0.2),
         # 'fig_file': os.path.join(fig_path, 'apps_mc.png')
         }
    ]
    # plot_metrics(optimizers, experiments, metrics, data_path, x_label)

    # data_path = 'output/synthetic/exp_users/'
    data_path = 'output/synthetic/exp_comp/exp_users'
    experiments = [
        {'path': 'n9_a5_u5000', 'x': 5000},
        {'path': 'n9_a5_u10000', 'x': 10000},
        {'path': 'n9_a5_u15000', 'x': 15000},
        {'path': 'n9_a5_u20000', 'x': 20000},
    ]
    x_label = 'Number of Users'
    metrics = [
        # {'id': 'weighted_avg_deadline_violation',
        #  'label': 'Normalized Deadline Violation',
        #  'normalize': True,
        #  # 'fig_file': os.path.join(fig_path, 'users_dv.png')
        #  },
        # {'id': 'overall_cost',
        #  'label': 'Operational Cost',
        #  'fig_file': os.path.join(fig_path, 'users_oc.png')
        #  },
        {'id': 'weighted_migration_rate',
         'label': 'Migration Cost (%)',
         'func': to_percent,
         'legend_pos': (0.3, 0.2),
         # 'fig_file': os.path.join(fig_path, 'users_mc.png')
         }
    ]
    plot_metrics(optimizers, experiments, metrics, data_path, x_label)


if __name__ == '__main__':
    main()
