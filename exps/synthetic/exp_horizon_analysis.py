from glob import glob
from itertools import cycle, islice
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def s_to_ms(value):
    return 1000.0 * value


def to_percent(value):
    return 100.0 * value


def bool_to_int(value):
    return int(value)


def plot_metrics(optimizers, metrics, data_path, x_label):
    cloud_opt_id = 'CloudOptimizer'

    metrics_data = []

    exp_path = os.path.join(data_path, '[0-9]*')
    runs_path = glob(exp_path)
    for opt in optimizers:
        for opt_x in opt['x']:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt_x['id'], 'metrics.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')

                cloud_filename = os.path.join(run_path, cloud_opt_id, 'metrics.json')
                cloud_df = None
                if os.path.isfile(cloud_filename):
                    cloud_df = pd.read_json(cloud_filename, orient='records')

                data = {'opt': opt['label'], 'run': run, 'x': opt_x['x']}
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
    # metric_id = 'overall_cost'
    # metric_id = 'weighted_migration_rate'
    metric_id = 'elapsed_time'
    print(metrics_df.groupby(['x', 'opt'])[metric_id].mean())
    # exit()

    # sns.relplot(x='x', y=metric_id, hue='opt', kind='line', data=metrics_df)
    # sns.catplot(x='x', y=metric_id, hue='opt', kind='point', ci=None, data=metrics_df, facet_kws=dict(despine=False))
    sns.pointplot(x='x', y=metric_id, hue='opt', ci=None, data=metrics_df)
    # sns.catplot(x='x', y=metric_id, hue='opt', kind='point', col='run', col_wrap=10, ci=None, data=metrics_df)
    # sns.catplot(x='x', y=metric_id, hue='opt', kind='bar', ci=95, data=metrics_df)
    # sns.boxplot(x='x', y=metric_id, hue='opt', notch=False, data=metrics_df)
    # print(sns.axes_style())
    plt.show()
    exit()

    markers_unique = ['o', 's', 'd', '^', 'v', '<']
    opt_count = metrics_df['opt'].nunique()
    markers = list(islice(cycle(markers_unique), opt_count))

    for metric in metrics:
        metric_id = metric['id']
        ax = sns.pointplot(x='x', y=metric_id, hue='opt', kind='point', ci=None, data=metrics_df,
                           height=5, aspect=1.5, markers=markers)
        ax.xaxis.grid(True)
        ax.set_xlabel(x_label)
        ax.set_ylabel(metric['label'])

        if 'y_limit' in metric:
            ax.set_ylim(*metric['y_limit'])

        use_legend = True
        if 'legend' in metric:
            use_legend = bool(metric['legend'])

        if use_legend:
            if 'legend_pos' in metric:
                legend_pos = metric['legend_pos']
                ax.legend(loc='center', ncol=3, title=None,
                          bbox_to_anchor=legend_pos,
                          columnspacing=0.0, labelspacing=0.0, handletextpad=0.0)
            else:
                ax.legend(loc='best', ncol=3, title=None,
                          columnspacing=0.0, labelspacing=0.0, handletextpad=0.0)
        else:
            ax.legend().set_visible(False)

        plt.subplots_adjust(bottom=0.14, top=0.995, left=0.14, right=0.995)
        if 'fig_file' in metric:
            # plt.savefig(metric['fig_file'], dpi=100, bbox_inches='tight')
            plt.savefig(metric['fig_file'], dpi=100)
            plt.clf()
        else:
            plt.show()


def main():
    fig_path = 'output/synthetic/figs/exp_horizon/'
    try:
        os.makedirs(fig_path)
    except OSError:
        pass

    data_path = 'output/synthetic/exp_horizon/n9_a10_u10000/'

    optimizers = [
        # {'label': 'Cloud', 'x': [
        #     {'id': 'CloudOptimizer', 'x': 2},
        #     {'id': 'CloudOptimizer', 'x': 3},
        #     {'id': 'CloudOptimizer', 'x': 4},
        # ]},
        {'label': 'GS', 'x': [
            {'id': 'LLCOptimizer_sga_w2', 'x': 2},
            {'id': 'LLCOptimizer_sga_w3', 'x': 3},
            {'id': 'LLCOptimizer_sga_w4', 'x': 4},
        ]},
        {'label': 'SS', 'x': [
            {'id': 'LLCOptimizer_ssga_w2', 'x': 2},
            {'id': 'LLCOptimizer_ssga_w2', 'x': 3},
            {'id': 'LLCOptimizer_ssga_w2', 'x': 4},
        ]},
    ]

    # x_label = 'Load chunk'
    x_label = r'Prediction Horizon $H$'
    metrics = [
        {'id': 'weighted_avg_deadline_violation',
         'label': 'Normalized Deadline Violation',
         'normalize': True,
         'y_limit': (0.0, 1.05),
         # 'legend': False,
         # 'legend_pos': (0.5, 0.5),
         'fig_file': os.path.join(fig_path, 'fig_horizon_dv.png')
         },
        {'id': 'overall_cost',
         'label': 'Operational Cost',
         'y_limit': (200.0, 405.0),
         # 'legend': False,
         # 'legend_pos': (0.5, 0.3),
         'fig_file': os.path.join(fig_path, 'fig_horizon_oc.png')
         },
        {'id': 'weighted_migration_rate',
         'label': 'Migration Cost (%)',
         # 'y_limit': (-0.05, 1.05),
         'y_limit': (0.0, 1.05),
         'func': to_percent,
         # 'legend': False,
         # 'legend_pos': (0.5, 0.2),
         'fig_file': os.path.join(fig_path, 'fig_horizon_mc.png')
         },
        {'id': 'elapsed_time',
         'label': 'Execution Time (s)',
         'y_limit': (0.0, 72.00),
         # 'legend': False,
         # 'legend_pos': (0.5, 0.2),
         'fig_file': os.path.join(fig_path, 'fig_horizon_et.png')
         },
    ]
    plot_metrics(optimizers, metrics, data_path, x_label)


if __name__ == '__main__':
    main()
