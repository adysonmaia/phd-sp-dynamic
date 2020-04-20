from sp.core.model import Scenario
from sp.core.lib import forecasting_metrics
from sp.simulator import Simulator, Monitor
from sp.system_controller.predictor import DefaultEnvironmentPredictor
from datetime import datetime
from pytz import timezone
import json
import time
import pandas as pd
import matplotlib.pyplot as plt

UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)


class EnvMonitor(Monitor):
    def __init__(self, valid_load_filename, predicted_load_filename):
        Monitor.__init__(self)
        self.valid_load_filename = valid_load_filename
        self.predicted_load_filename = predicted_load_filename
        self.valid_data = None
        self.predicted_data = None
        self.env_predictor = DefaultEnvironmentPredictor()
        self.prediction_window = 10

    def on_sim_started(self, sim_time):
        self.valid_data = []
        self.predicted_data = []
        self.env_predictor.init_params()

    def on_env_ctrl_ended(self, sim_time, system, environment_input):
        print(datetime.fromtimestamp(sim_time, tz=UTC_TZ).astimezone(SF_TZ))

        self.env_predictor.update(system, environment_input)
        predictions = self.env_predictor.predict(self.prediction_window)

        for app in system.apps:
            for node in system.nodes:
                load = environment_input.get_generated_load(app.id, node.id)
                datum = {'time': sim_time, 'app': app.id, 'node': node.id, 'load': load}
                self.valid_data.append(datum)

                for (pred_index, pred_env) in enumerate(predictions):
                    pred_time = system.time + (pred_index + 1) * system.sampling_time
                    pred_load = pred_env.get_generated_load(app.id, node.id)
                    datum = {'time': sim_time, 'app': app.id, 'node': node.id,
                             'prediction': pred_load, 'prediction_time': pred_time}
                    self.predicted_data.append(datum)

    def on_sim_ended(self, sim_time):
        with open(self.valid_load_filename, 'w') as file:
            json.dump(self.valid_data, file, indent=2)

        with open(self.predicted_load_filename, 'w') as file:
            json.dump(self.predicted_data, file, indent=2)


def plot_error(scenario, valid_df, predicted_df):
    accuracy_metrics = ['mae', 'rmse', 'smape', 'umbrae']
    accuracy_data = []
    time_series = valid_df.index.unique().tolist()
    time_series = time_series[1:]
    for t in time_series:
        print(t.astimezone(SF_TZ))
        l_df = predicted_df.loc[t].set_index(['prediction_time', 'app', 'node']).sort_index()
        l_df.index.names = ['time', 'app', 'node']

        r_df = valid_df.set_index(['app', 'node'], append=True).sort_index()
        join_df = l_df.join(r_df, how='inner')

        if not join_df.empty:
            time_ds = join_df.index.unique(level='time').tolist()
            for (pred_index, pred_t) in enumerate(time_ds):
                filtered_df = join_df.loc[:pred_t]
                metric_results = forecasting_metrics.evaluate(filtered_df['load'], filtered_df['prediction'],
                                                              metrics=accuracy_metrics)
                datum = {'time': t, 'window': pred_index + 1}
                datum.update(metric_results)
                accuracy_data.append(datum)

    accuracy_df = pd.DataFrame.from_records(accuracy_data)
    accuracy_df.set_index(['time'], inplace=True)
    accuracy_df.sort_index(inplace=True)
    accuracy_df = accuracy_df.tz_convert(SF_TZ_STR)

    grouped_df = accuracy_df.groupby('window')
    nb_cols = 2
    nb_rows = len(accuracy_metrics) // nb_cols
    if nb_rows * nb_cols < len(accuracy_metrics):
        nb_rows += 1
    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))

    for (metric_index, metric) in enumerate(accuracy_metrics):
        ax_row = metric_index // nb_cols
        ax_col = metric_index % nb_cols
        ax = axes[ax_row, ax_col]
        grouped_df[metric].plot(ax=ax)
        ax.set_ylabel(metric)

    axes[0, 0].legend(ncol=5, loc='upper right')

    # if nb_rows * nb_cols > len(accuracy_metrics):
    #     legend_pos = axes[nb_rows-1, nb_cols-1].get_position()
    #     legend = axes[0, 0].get_legend_handles_labels()
    #     fig.legend(*legend, loc='upper left', ncol=5, bbox_to_anchor=legend_pos)
    # else:
    #     axes[0, 0].legend(ncol=5)

    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= len(accuracy_metrics):
                axes[row, col].remove()

    # fig.tight_layout(pad=0.1)
    fig.tight_layout()
    plt.show()


def plot_prediction(scenario, valid_df, predicted_df):
    bs_nodes = scenario.network.bs_nodes
    nb_axes = len(bs_nodes)
    nb_cols = 5
    nb_rows = nb_axes // nb_cols
    if nb_rows * nb_cols < nb_axes:
        nb_rows += 1
    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))

    load_min, load_max = valid_df['load'].min(), valid_df['load'].max()
    for (node_index, node) in enumerate(bs_nodes):
        ax_row = node_index // nb_cols
        ax_col = node_index % nb_cols
        ax = axes[ax_row, ax_col]
        ax.set_ylabel('Load')

        ax.set_title('Node {}'.format(node.id))
        ax.set_ylim(load_min, load_max)

        app = scenario.apps[0]
        df = valid_df[(valid_df['node'] == node.id) & (valid_df['app'] == app.id)]
        df['load'].plot(ax=ax, legend=False)

        df = predicted_df[(predicted_df['node'] == node.id) & (predicted_df['app'] == app.id)]
        df = df.groupby(['time', 'app', 'node']).first().reset_index()
        df = df.set_index('prediction_time', append=False).sort_index()
        df.drop(columns='time', inplace=True)
        df.index.names = ['time']
        df['prediction'].plot(ax=ax, legend=False)

    axes[0, 0].legend()
    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= nb_axes:
                axes[row, col].remove()

    for ax in fig.get_axes():
        ax.label_outer()
    fig.tight_layout()
    plt.show()


def run_sim(scenario, valid_load_filename, predicted_load_filename):
    # Set simulation time based on San Francisco timezone
    start_time = SF_TZ.localize(datetime(2008, 5, 24, 0, 0, 0)).timestamp()
    stop_time = SF_TZ.localize(datetime(2008, 5, 24, 23, 59, 59)).timestamp()
    # step_time = 10 * 60  # seconds or 10 min
    step_time = 60 * 60  # seconds or 1H
    # step_time = 30 * 60  # seconds or 30 min

    # Set simulation parameters
    sim = Simulator(scenario=scenario)
    sim.set_time(stop=stop_time, start=start_time, step=step_time)
    sim.monitor = EnvMonitor(valid_load_filename, predicted_load_filename)

    # Run simulation
    start_count = time.perf_counter()
    sim.run()
    end_count = time.perf_counter()
    print('sim exec time: {}s'.format(end_count - start_count))


def data_analysis(scenario, valid_load_filename, predicted_load_filename):
    valid_df = pd.read_json(valid_load_filename, orient='records')
    valid_df['time'] = pd.to_datetime(valid_df['time'], unit='s', utc=True)
    valid_df.set_index(['time'], inplace=True)
    valid_df.sort_index(inplace=True)

    predicted_df = pd.read_json(predicted_load_filename, orient='records')
    predicted_df['time'] = pd.to_datetime(predicted_df['time'], unit='s', utc=True)
    predicted_df['prediction_time'] = pd.to_datetime(predicted_df['prediction_time'], unit='s', utc=True)
    predicted_df.set_index(['time'], inplace=True)
    predicted_df.sort_index(inplace=True)

    # plot_error(scenario, valid_df, predicted_df)
    plot_prediction(scenario, valid_df, predicted_df)


def main():
    valid_load_filename = 'output/san_francisco/forecasting_analysis/load_valid.json'
    predicted_load_filename = 'output/san_francisco/forecasting_analysis/load_predicted.json'

    scenario_filename = 'input/san_francisco/scenario.json'
    scenario = None
    with open(scenario_filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)

    # run_sim(scenario, valid_load_filename, predicted_load_filename)
    data_analysis(scenario, valid_load_filename, predicted_load_filename)


if __name__ == '__main__':
    main()
