from datetime import datetime
from pytz import timezone
from glob import glob
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)


def s_to_ms(value):
    return 1000.0 * value


def to_percent(value):
    return 100.0 * value


def bool_to_int(value):
    return int(value)


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
            # df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
            # df = df[df['time'] <= stop_time]
            opt_df.append(df)

        opt_df = pd.concat(opt_df)
        # opt_df.set_index(['time'], inplace=True)
        # opt_df.sort_index(inplace=True)
        opts_df[opt['id']] = opt_df

    return opts_df


def plot_metrics(optimizers, experiments, output_path):
    metrics = [
        {'id': 'valid', 'label': 'valid', 'func': bool_to_int},
        {'id': 'max_deadline_violation', 'label': 'max. deadline violation - ms', 'func': s_to_ms},
        {'id': 'deadline_satisfaction', 'label': 'deadline satisfaction - %', 'func': to_percent},
        {'id': 'migration_rate', 'label': 'migration rate - %', 'func': to_percent},
        {'id': 'elapsed_time', 'label': 'exec time - s'},
        {'id': 'overall_deadline_violation', 'label': 'overall deadline violation - ms', 'func': s_to_ms},
        {'id': 'overall_cost', 'label': 'allocation cost'},
        {'id': 'overall_migration_cost', 'label': 'migration cost'},
        {'id': 'overall_response_time', 'label': 'overall response time - ms', 'func': s_to_ms},
        {'id': 'avg_deadline_violation', 'label': 'avg deadline violation - ms', 'func': s_to_ms},
        {'id': 'avg_only_violated_deadline', 'label': 'avg deadline violation 2 - ms', 'func': s_to_ms},
        {'id': 'avg_response_time', 'label': 'avg response time - ms', 'func': s_to_ms},
        {'id': 'avg_migration_cost', 'label': 'avg migration cost'},
        {'id': 'weighted_avg_response_time', 'label': 'avg response time - ms', 'func': s_to_ms},
        {'id': 'weighted_avg_deadline_violation', 'label': 'avg deadline violation - ms', 'func': s_to_ms},
        {'id': 'weighted_migration_rate', 'label': 'migration rate - %', 'func': to_percent},
    ]
    metrics_id = [m['id'] for m in metrics]
    cloud_opt_id = 'CloudOptimizer'

    metrics_data = []

    for exp in experiments:
        exp_path = os.path.join(output_path, exp['path'], '[0-9]*')
        runs_path = glob(exp_path)
        for opt in optimizers:
            for (run, run_path) in enumerate(runs_path):
                filename = os.path.join(run_path, opt['id'], 'metrics.json')
                if not os.path.isfile(filename):
                    continue
                df = pd.read_json(filename, orient='records')

                cloud_filename = os.path.join(run_path, cloud_opt_id, 'metrics.json')
                cloud_df = None
                # if os.path.isfile(cloud_filename):
                #     cloud_df = pd.read_json(cloud_filename, orient='records')

                data = {'opt': opt['label'], 'run': run, 'x': exp['x']}
                for metric in metrics:
                    metric_id = metric['id']
                    if metric_id not in df.columns:
                        continue

                    value = df[metric_id].mean()
                    cloud_value = cloud_df[metric_id].mean() if cloud_df is not None else 0.0
                    # value = df[metric_id].sum()
                    # cloud_value = cloud_df[metric_id].sum() if cloud_df is not None else 0.0
                    if 'func' in metric:
                        value = metric['func'](value)
                        cloud_value = metric['func'](cloud_value)
                    if cloud_value > 0.0:
                        data[metric_id] = value / float(cloud_value)
                    else:
                        data[metric_id] = value
                metrics_data.append(data)

    metrics_df = pd.DataFrame.from_records(metrics_data)
    sns.set()
    sns.set_context("paper")
    # sns.relplot(x='x', y='weighted_avg_deadline_violation', hue='opt', kind='line', data=metrics_df)
    # sns.catplot(x='x', y='weighted_avg_deadline_violation', hue='opt', kind='point', ci=None, data=metrics_df)
    sns.catplot(x='x', y='weighted_avg_deadline_violation', hue='opt', kind='bar', ci=95, data=metrics_df)
    # sns.boxplot(x='x', y='weighted_avg_deadline_violation', hue='opt', notch=False, data=metrics_df)
    plt.show()

    # metrics_df = metrics_df.melt(id_vars=['opt', 'run', 'x'], var_name='metric', value_name='y')
    # sns.set()
    # sns.catplot(x='x', y='y', col='metric', hue='opt', kind='bar', data=metrics_df)
    # plt.show()


def main():
    output_path = 'output/san_francisco/exp/'
    # output_path = 'output/san_francisco/exp_2/'
    optimizers = [
        {'id': 'CloudOptimizer', 'label': 'Cloud'},
        {'id': 'StaticOptimizer', 'label': 'Static'},
        {'id': 'SOHeuristicOptimizer', 'label': 'N+D'},
        # {'id': 'OmittedMigrationOptimizer', 'label': 'Omit Migration'},
        {'id': 'MOGAOptimizer', 'label': 'H=1'},
        {'id': 'LLCOptimizer_ssga_w1', 'label': 'SS H=2'},
        {'id': 'LLCOptimizer_sga_w1', 'label': 'GS H=2'},
    ]
    # experiments = [
    #     {'path': '1_a1_1211612400_1211698799', 'x': '1-1'},
    #     {'path': '2_a1_1211612400_1211698799', 'x': '1-2'},
    #     {'path': '1_a4_1211612400_1211698799', 'x': '4-1'},
    #     {'path': '2_a4_1211612400_1211698799', 'x': '4-2'},
    #     {'path': 'a10_1211612400_1211698799', 'x': '10-1'},
    # ]
    # experiments = [
    #     {'path': 'a4_eyJuYl9hcHBzIjogNCwgInRpbWUiOiB7InN0ZXAiOiA5MDB9fQ==', 'x': '15'},
    #     {'path': 'a4_eyJuYl9hcHBzIjogNCwgInRpbWUiOiB7InN0ZXAiOiAxODAwfX0=', 'x': '30'},
    #     {'path': 'a4_eyJuYl9hcHBzIjogNCwgInRpbWUiOiB7InN0ZXAiOiAyNzAwfX0=', 'x': '45'},
    #     {'path': 'a4_eyJuYl9hcHBzIjogNCwgInRpbWUiOiB7InN0ZXAiOiAzNjAwfX0=', 'x': '60'},
    # ]
    # experiments = [
    #     # {'path': 'a1_eyJuYl9hcHBzIjogMX0=', 'x': '01'},
    #     {'path': 'a4_eyJuYl9hcHBzIjogNH0=', 'x': '04'},
    #     # {'path': 'a5_eyJuYl9hcHBzIjogNX0=', 'x': '05'},
    #     {'path': 'a7_eyJuYl9hcHBzIjogN30=', 'x': '07'},
    #     {'path': 'a10_eyJuYl9hcHBzIjogMTB9', 'x': '10'},
    # ]
    experiments = [
        {'path': 'a50', 'x': 50},
    ]
    plot_metrics(optimizers, experiments, output_path)


if __name__ == '__main__':
    main()
