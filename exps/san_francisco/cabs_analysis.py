from glob import glob
from future.utils import iteritems
import pandas as pd
import matplotlib.pyplot as plt
import pmdarima as pm


def main():
    files = glob('input/san_francisco/cabs/new_*.txt')
    cabs_df = [pd.read_csv(file, sep=' ', header=None, names=['latitude', 'longitude', 'free', 'time'])
               for file in files]
    for (index, df) in enumerate(cabs_df):
        df['cab'] = index

    df = pd.concat(cabs_df)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.drop(columns='free', inplace=True)
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)

    bbox = {'longitude': [-122.5160063624, -122.3754337591], 'latitude': [37.7072272217, 37.8112472822]}
    for (key, value) in iteritems(bbox):
        df = df[df[key].between(*value)]

    # plt.figure()
    # df['cab'].resample('10min').nunique().plot()
    # plt.show()

    # count_df = df['cab'].resample('10min').nunique()
    count_df = df['cab'].resample('1H').nunique()
    # train_df = count_df['2008-05-24 00:00:00':'2008-05-24 23:59:59']
    train_df = count_df[:'2008-05-24 23:59:59']
    valid_df = count_df['2008-05-24 23:59:59':'2008-05-26 23:59:59']

    seasonal_frequency = len(count_df['2008-05-24 00:00:00':'2008-05-24 23:59:59'])
    seasonal_model = pm.auto_arima(train_df,
                                   seasonal=True, m=seasonal_frequency, stepwise=True,
                                   error_action='ignore', suppress_warnings=True, trace=True)
    print(seasonal_model.summary())
    seasonal_forecast = seasonal_model.predict(n_periods=len(valid_df))
    seasonal_forecast_df = pd.DataFrame(seasonal_forecast, index=valid_df.index, columns=['cab'])

    model = pm.auto_arima(train_df, error_action='ignore', suppress_warnings=True, trace=True)
    print(model.summary())
    forecast = model.predict(n_periods=len(valid_df))
    forecast_df = pd.DataFrame(forecast, index=valid_df.index, columns=['cab'])

    plt.figure()
    plt.plot(train_df, label='Train')
    plt.plot(valid_df, label='Valid')
    plt.plot(seasonal_forecast_df, label='Seasonal Prediction')
    plt.plot(forecast_df, label='Prediction')
    plt.ylabel('Number of Cabs')
    plt.xlabel('time')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    main()
