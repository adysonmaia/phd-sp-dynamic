from glob import glob
from itertools import cycle, islice
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl


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
    mpl.rcParams['hatch.linewidth'] = 0.5

    # metric_id = 'weighted_avg_deadline_violation'
    # metric_id = 'overall_cost'
    # # metric_id = 'weighted_migration_rate'
    # print(metrics_df.groupby(['x', 'opt'])[metric_id].mean())
    # exit()

    # # sns.relplot(x='x', y=metric_id, hue='opt', kind='line', data=metrics_df)
    # # sns.catplot(x='x', y=metric_id, hue='opt', kind='point', ci=None, data=metrics_df, facet_kws=dict(despine=False))
    # # sns.catplot(x='x', y=metric_id, hue='opt', kind='point', col='run', col_wrap=10, ci=None, data=metrics_df)
    # sns.catplot(x='x', y=metric_id, hue='opt', kind='bar', ci=95, data=metrics_df)
    # # sns.boxplot(x='x', y=metric_id, hue='opt', notch=False, data=metrics_df)
    # # print(sns.axes_style())
    # plt.show()

    markers_unique = ['o', 's', 'd', '^', 'v', '<']
    opt_count = metrics_df['opt'].nunique()
    x_count = metrics_df['x'].nunique()
    markers = list(islice(cycle(markers_unique), opt_count))

    hatches_unique = ['/', '\\', '-', 'x', '+', '*', 'o']
    hatches = list(islice(cycle(hatches_unique), opt_count))

    for metric in metrics:
        metric_id = metric['id']
        # ax = sns.pointplot(x='x', y=metric_id, hue='opt', kind='point', ci=None, data=metrics_df,
        #                    height=5, aspect=1.5, markers=markers)
        ax = sns.barplot(x='x', y=metric_id, hue='opt', ci=None, data=metrics_df)
        ax.xaxis.grid(True)
        ax.set_xlabel(x_label)
        ax.set_ylabel(metric['label'])

        if 'y_limit' in metric:
            ax.set_ylim(*metric['y_limit'])

        hatch_index = -1
        for (index, patch) in enumerate(ax.patches):
            # Loop iterates an opt throughout x-axes, then it advances to the next opt
            if index % x_count == 0:
                hatch_index += 1
            hatch = hatches[hatch_index]
            patch.set_hatch(hatch)

            if patch.get_height() == 0:
                ax.annotate(format(patch.get_height(), '.1f'),
                            (patch.get_x() + patch.get_width() / 2., patch.get_height()),
                            color=patch.get_facecolor(),
                            ha='center', va='center',
                            size=15,
                            xytext=(0, 9),
                            textcoords='offset points')

        ax.legend(loc='upper center', bbox_to_anchor=(0.44, -0.15),
                  ncol=3, title=None,
                  handlelength=1.6, columnspacing=0.5, labelspacing=0.0, handletextpad=0.0)
        plt.subplots_adjust(bottom=0.29, top=0.992, left=0.14, right=0.995)

        # if 'legend_pos' in metric:
        #     legend_pos = metric['legend_pos']
        #     ax.legend(loc='center', ncol=3, title=None,
        #               bbox_to_anchor=legend_pos,
        #               columnspacing=0.0, labelspacing=0.0, handletextpad=0.0)
        # else:
        #     ax.legend(loc='best', ncol=3, title=None,
        #               columnspacing=0.0, labelspacing=0.0, handletextpad=0.0)
        # plt.subplots_adjust(bottom=0.14, top=0.995, left=0.14, right=0.995)
        if 'fig_file' in metric:
            # plt.savefig(metric['fig_file'], dpi=100, bbox_inches='tight')
            plt.savefig(metric['fig_file'], dpi=100)
            plt.clf()
        else:
            plt.show()


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
    # metric_id = 'weighted_avg_deadline_violation'
    # metric_id = 'avg_deadline_violation'
    # metric_id = 'max_deadline_violation'
    # metric_id = 'overall_cost'
    # metric_id = 'weighted_migration_rate'
    # metric_id = 'overall_migration_cost'
    metric_id = 'migration_rate'
    # metric_id = 'max_migration_cost'
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
    # sns.catplot(x='exp', y='place_per_app', hue='opt', kind='point', ci=None, data=place_df)
    # sns.catplot(x='exp', y='place', hue='opt', kind='point', ci=None, data=place_df)
    sns.catplot(x='exp', y='place', hue='opt', kind='bar', ci=95, data=place_df)
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

                last_node_id = df['node'].max()
                # df = df[df['node'] == last_node_id]
                # df = df[df['node'] == last_node_id - 1]
                df = df[df['node'] < last_node_id - 1]

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

    sns.relplot(x='time', y='place', hue='opt', col="exp", col_wrap=2, kind='line', ci=None, data=place_df)
    # sns.relplot(x='time', y='place_per_app', hue='opt', col="exp", col_wrap=2, kind='line', ci=None, data=place_df)
    plt.show()


def plot_placement_per_node(optimizers, experiments, output_path):
    data = []
    for exp in experiments:
        exp_path = os.path.join(output_path, exp['path'], '[0-9]*')
        runs_path = glob(exp_path)
        runs_path = [runs_path[7]]
        for opt in optimizers:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt['id'], 'placement.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')
                df['place'] = df['place'].astype(int)

                df = df[df['app'] == 0]

                ts = df.groupby(['time', 'node'])['place'].sum()
                # nb_apps = df['app'].nunique()

                for (index, place) in ts.iteritems():
                    time = index[0]
                    node = index[1]
                    datum = {'time': time, 'exp': exp['x'], 'opt': opt['label'], 'run': run,
                             'node': node, 'place': place}
                    data.append(datum)

    place_df = pd.DataFrame.from_records(data)
    sns.set()
    sns.set_context("notebook")
    sns.set_style("whitegrid")

    sns.relplot(x='time', y='place', hue='opt', col="node", row='exp', kind='line', ci=None, data=place_df)
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
                df = df[df['node'] < last_node_id]
                # df = df[df['node'] < last_node_id - 1]
                # df = df[df['node'] == last_node_id]

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
    # sns.catplot(x='exp', y='alloc_per_app', hue='opt', col="resource", kind='point', ci=None, data=alloc_df)
    # sns.catplot(x='exp', y='alloc_per_rep', hue='opt', col="resource", kind='point', ci=None, data=alloc_df)
    sns.catplot(x='exp', y='alloc', hue='opt', col="resource", kind='bar', ci=95, data=alloc_df)
    plt.show()


def plot_load(optimizers, experiments, output_path, x_label):
    data = []
    for exp in experiments:
        exp_path = os.path.join(output_path, exp['path'], '[0-9]*')
        runs_path = glob(exp_path)
        for opt in optimizers:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt['id'], 'load_distribution.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')

                nodes_id = df['dst_node'].unique()
                last_node_id = df['dst_node'].max()

                df = df[df['src_node'] != df['dst_node']]

                df['load'] = df['load'] * df['ld']
                load_ts = df.groupby(['dst_node'])['load'].mean()

                total_load = load_ts.sum()
                load_per_node_type = [
                    ('Cloud', load_ts[last_node_id]),
                    ('Core', load_ts[last_node_id - 1]),
                    ('Base Stations', load_ts[load_ts.index < last_node_id - 1].sum()),
                    # ('Cloud & Core', load_ts[load_ts.index >= last_node_id - 1].sum())
                ]
                for (node_type, load) in load_per_node_type:
                    load_percent = load / float(total_load) if total_load > 0.0 else 0.0
                    load_percent *= 100.0
                    datum = {'x': exp['x'], 'opt': opt['label'], 'run': run,
                             'node': node_type, 'load': load, 'load_percent': load_percent
                             }
                    data.append(datum)

                # load_ts = load_ts[load_ts.index == last_node_id]
                # for (node_id, load) in load_ts.iteritems():
                #     load_percent = load / float(total_load) if total_load > 0.0 else 0.0
                #     datum = {'exp': exp['x'], 'opt': opt['label'], 'run': run,
                #              'node': node_id, 'load': load, 'load_percent': load_percent
                #              }
                #     data.append(datum)

    load_df = pd.DataFrame.from_records(data)

    opt_count = load_df['opt'].nunique()
    x_count = load_df['x'].nunique()

    hatches_unique = ['/', '\\', '-', 'x', '+', '*', 'o']
    hatches = list(islice(cycle(hatches_unique), opt_count))

    sns.set()
    sns.set_context('paper', font_scale=2.0)
    sns.set_style('ticks', {'axes.grid': True, 'grid.linestyle': '--'})
    mpl.rcParams['hatch.linewidth'] = 0.5

    y_label = 'Incoming Load (%)'
    # fg = sns.catplot(x='x', y='load_percent', hue='opt', col="node", kind='bar', ci=None, data=load_df,
    #                  legend=False)
    fg = sns.catplot(x='x', y='load', hue='opt', col="node", kind='bar', ci=None, data=load_df,
                     legend=False)
    fg.set_axis_labels(x_label, y_label)
    fg.set_titles(col_template="{col_name}")

    for ax in fg.axes[0]:
        hatch_index = -1
        for (index, patch) in enumerate(ax.patches):
            # Loop iterates an opt throughout x-axes, then it advances to the next opt
            if index % x_count == 0:
                hatch_index += 1
            hatch = hatches[hatch_index]
            patch.set_hatch(hatch)

            if patch.get_height() == 0:
                ax.annotate(format(patch.get_height(), '.1f'),
                            (patch.get_x() + patch.get_width() / 2., patch.get_height()),
                            color=patch.get_facecolor(),
                            ha='center', va='center',
                            size=15,
                            xytext=(0, 9),
                            textcoords='offset points')

    ax = fg.axes[0][1]
    # ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.17),
    #           ncol=opt_count, title=None,
    #           handlelength=1.5, columnspacing=0.5, labelspacing=0.0, handletextpad=0.0)
    # plt.subplots_adjust(bottom=0.24, top=0.92, left=0.06, right=0.995)
    ax.legend(loc='upper center', bbox_to_anchor=(0.42, -0.15),
              ncol=3, title=None,
              handlelength=1.6, columnspacing=0.5, labelspacing=0.0, handletextpad=0.0)
    plt.subplots_adjust(bottom=0.29, top=0.992, left=0.14, right=0.995)
    plt.show()


def plot_placement_per_node_type(optimizers, experiments, output_path, x_label):
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

                nodes_id = df['node'].unique()
                last_node_id = df['node'].max()

                place_df = df.groupby(['node', 'time'])['place'].sum().reset_index()
                place_ts = place_df.groupby(['node'])['place'].mean()
                # place_ts = df.groupby(['node'])['place'].mean()

                total_place = place_ts.sum()
                load_per_node_type = [
                    ('cloud', place_ts[last_node_id]),
                    ('core', place_ts[last_node_id - 1]),
                    ('bs', place_ts[place_ts.index < last_node_id - 1].sum()),
                    ('non_bs', place_ts[place_ts.index >= last_node_id - 1].sum()),
                    ('all', place_ts.sum())
                ]
                for (node_type, place) in load_per_node_type:
                    place_percent = place / float(total_place) if total_place > 0.0 else 0.0
                    place_percent *= 100.0
                    datum = {'x': exp['x'], 'opt': opt['label'], 'run': run,
                             'node': node_type, 'place': place, 'place_percent': place_percent
                             }
                    data.append(datum)

    place_df = pd.DataFrame.from_records(data)

    opt_count = place_df['opt'].nunique()
    x_count = place_df['x'].nunique()

    hatches_unique = ['/', '\\', '-', 'x', '+', '*', 'o']
    hatches = list(islice(cycle(hatches_unique), opt_count))

    node_types = [
        # {'id': 'cloud', 'title': 'Cloud'},
        # {'id': 'core', 'title': 'Core'},
        {'id': 'non_bs', 'title': 'Cloud and Core'},
        {'id': 'bs', 'title': 'Base Stations (RAN)'},
    ]

    sns.set()
    sns.set_context('paper', font_scale=2.0)
    sns.set_style('ticks', {'axes.grid': True, 'grid.linestyle': '--'})
    mpl.rcParams['hatch.linewidth'] = 0.5

    nodes_id = [item['id'] for item in node_types]
    nodes_title = {item['id']: item['title'] for item in node_types}
    nodes_order = [item['title'] for item in node_types]
    df = place_df[place_df['node'].isin(nodes_id)].replace(nodes_title)
    # df['node'].replace(nodes_title, inplace=True)
    # df.replace(nodes_title, inplace=True)

    fg = sns.catplot(x='x', y='place', hue='opt', col="node", kind='bar', ci=None, data=df,
                     col_order=nodes_order, legend=False)
    y_label = 'Number of App. Replicas'
    fg.set_axis_labels(x_label, y_label)
    fg.set_titles(col_template="{col_name}")

    for ax in fg.axes[0]:
        hatch_index = -1
        for (index, patch) in enumerate(ax.patches):
            # Loop iterates an opt throughout x-axes, then it advances to the next opt
            if index % x_count == 0:
                hatch_index += 1
            hatch = hatches[hatch_index]
            patch.set_hatch(hatch)

            if patch.get_height() == 0:
                ax.annotate(format(patch.get_height(), '.1f'),
                            (patch.get_x() + patch.get_width() / 2., patch.get_height()),
                            color=patch.get_facecolor(),
                            ha='center', va='center',
                            size=15,
                            xytext=(0, 9),
                            textcoords='offset points')

    ax = fg.axes[0][0]
    ax.legend(loc='upper center', bbox_to_anchor=(1.05, -0.17),
              ncol=opt_count, title=None,
              handlelength=1.6, columnspacing=0.5, labelspacing=0.0, handletextpad=0.0)
    plt.subplots_adjust(bottom=0.24, top=0.92, left=0.07, right=0.995)
    plt.show()

    # y_label = 'Number of App. Replicas (%)'
    # for node_type in node_types:
    #     df = place_df[place_df['node'] == node_type['id']]
    #
    #     ax = sns.barplot(x='x', y='place_percent', hue='opt', ci=None, data=df)
    #     # ax = sns.barplot(x='x', y='place', hue='opt', ci=None, data=df)
    #     ax.xaxis.grid(True)
    #     ax.set_xlabel(x_label)
    #     ax.set_ylabel(y_label)
    #     # ax.set_ylim(0, 100)
    #     ax.set_title(node_type['title'])
    #
    #     hatch_index = -1
    #     for (index, patch) in enumerate(ax.patches):
    #         # Loop iterates an opt throughout x-axes, then it advances to the next opt
    #         if index % x_count == 0:
    #             hatch_index += 1
    #         hatch = hatches[hatch_index]
    #         patch.set_hatch(hatch)
    #
    #         if patch.get_height() == 0:
    #             ax.annotate(format(patch.get_height(), '.1f'),
    #                         (patch.get_x() + patch.get_width() / 2., patch.get_height()),
    #                         color=patch.get_facecolor(),
    #                         ha='center', va='center',
    #                         size=15,
    #                         xytext=(0, 9),
    #                         textcoords='offset points')
    #
    #     ax.legend(loc='upper center', bbox_to_anchor=(0.42, -0.17),
    #               ncol=3, title=None,
    #               handlelength=1.6, columnspacing=0.5, labelspacing=0.0, handletextpad=0.0)
    #     plt.subplots_adjust(bottom=0.3, top=0.93, left=0.14, right=0.995)
    #     plt.show()

    # df = place_df[place_df['node'] == 'all']
    # ax = sns.barplot(x='x', y='place', hue='opt', ci=None, data=df)
    # plt.show()

    # fg = sns.catplot(x='x', y='place_percent', hue='opt', col="node", kind='bar', ci=None, data=place_df,
    #                  legend=False)
    # fg.set_axis_labels(x_label, y_label)
    # fg.set_titles(col_template="{col_name}")
    # # fg.add_legend()
    # # fg.tight_layout()
    # # print(fg.legend)
    #



def main():
    fig_path = 'output/hierarchical/figs/'
    try:
        os.makedirs(fig_path)
    except OSError:
        pass

    data_path = 'output/hierarchical/exp/'
    # data_path = 'output/hierarchical/11_clusters/exp/'
    # data_path = 'output/hierarchical/5_clusters/exp/'
    # data_path = 'output/hierarchical/3_clusters/exp/'
    optimizers = [
        {'id': 'CloudOptimizer', 'label': 'Cloud'},
        # {'id': 'StaticOptimizer', 'label': 'Static'},
        # {'id': 'SOHeuristicOptimizer', 'label': 'N+D'},
        # {'id': 'MOGAOptimizer', 'label': 'H1'},
        # {'id': 'LLCOptimizer_ssga_w1', 'label': 'SS'},
        {'id': 'LLCOptimizer_sga_w1', 'label': 'Centralized'},

        {'id': 'GlobalMOGAOptimizer_GeneralClusterLLGAOperator_w1_i0', 'label': 'Non-Coop'},
        {'id': 'GlobalMOGAOptimizer_GeneralClusterLLGAOperator_w1_i1', 'label': r'Coop $it_{\mathrm{max}}=1$'},
        {'id': 'GlobalMOGAOptimizer_GeneralClusterLLGAOperator_w1_i2', 'label': r'Coop $it_{\mathrm{max}}=2$'},
    ]
    experiments = [
        {'path': 'n9_a10_u10000_c03', 'x': 3},
        {'path': 'n9_a10_u10000_c05', 'x': 5},
        {'path': 'n9_a10_u10000_c11', 'x': 11},
    ]
    x_label = 'Number of Subsystems'
    metrics = [
        {'id': 'weighted_avg_deadline_violation',
         'label': 'N. Deadline Violation',
         'normalize': True,
         'fig_file': os.path.join(fig_path, 'fig_dv.png')
         },
        {'id': 'overall_cost',
         'label': 'Operational Cost',
         'fig_file': os.path.join(fig_path, 'fig_oc.png')
         },
        {'id': 'weighted_migration_rate',
         'label': 'Migration Cost (%)',
         'func': to_percent,
         'y_limit': (0.0, 0.45),
         'fig_file': os.path.join(fig_path, 'fig_mc.png')
         },
        {'id': 'migration_rate',
         'func': to_percent,
         'title': 'migration'}
    ]
    # plot_metrics(optimizers, experiments, metrics, data_path, x_label)

    # plot_metrics_over_time(optimizers, experiments, metrics, data_path)
    # plot_placement(optimizers, experiments, data_path)
    # plot_placement_over_time(optimizers, experiments, data_path)
    # plot_placement_per_node(optimizers, experiments, data_path)
    # plot_alloc(optimizers, experiments, data_path)
    plot_load(optimizers, experiments, data_path, x_label)
    # plot_placement_per_node_type(optimizers, experiments, data_path, x_label)


if __name__ == '__main__':
    main()
