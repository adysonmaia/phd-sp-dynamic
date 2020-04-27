from future.utils import iteritems
from datetime import datetime, timedelta
from pytz import timezone
import os
import xml.etree.ElementTree as ET
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


UTC_TZ = timezone('UTC')
SF_TZ_STR = 'US/Pacific'
SF_TZ = timezone(SF_TZ_STR)
SF_SHAPE_FILE = 'input/san_francisco/shapefile/bay_area_zip_codes/geo_export_2defef9a-b2e1-4ddd-84f6-1a131dd80410.shp'
DATA_PATH = 'input/sumo/'


def plot_count(df):
    df = df.tz_convert(SF_TZ_STR)
    # count_ds = df['user'].resample('10min').nunique()
    count_ds = df['user'].resample('1H').nunique()

    fig, axes = plt.subplots(nrows=1, ncols=1, squeeze=False, figsize=(16, 9))
    y_label = 'Number of Users'

    ax = axes[0, 0]
    count_ds.plot()
    ax.set_ylabel(y_label)

    fig.tight_layout()
    plt.show()


def plot_on_map(df):
    hours = range(0, 23, 4)
    time_series = [SF_TZ.localize(datetime(2008, 5, 24, hour, 0, 0)) for hour in hours]
    time_series.sort()

    crs = "EPSG:4326"
    bbox = [df['lon'].min(), df['lat'].min(), df['lon'].max(), df['lat'].max()]
    map_gdf = gpd.read_file(SF_SHAPE_FILE)
    map_gdf = map_gdf.to_crs(crs)
    map_gdf = map_gdf.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    map_bbox = map_gdf.total_bounds.tolist()

    time_delta = timedelta(minutes=10)
    start_time = time_series[0]
    end_time = time_series[-1] + time_delta
    df = df.tz_convert(SF_TZ_STR)
    df = df[start_time:end_time]
    cabs_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['lon'], df['lat']), crs=crs)

    nb_cols = 3
    nb_rows = len(time_series) // nb_cols
    if nb_rows * nb_cols < len(time_series):
        nb_rows += 1
    fig, axes = plt.subplots(nrows=nb_rows, ncols=nb_cols, squeeze=False, figsize=(16, 9))

    for (t_index, t) in enumerate(time_series):
        start_t = t
        end_t = start_t + time_delta
        t_cabs_gdf = cabs_gdf[start_t:end_t].drop_duplicates(subset='user')

        ax_row = t_index // nb_cols
        ax_col = t_index % nb_cols
        ax = axes[ax_row, ax_col]
        ax.set_aspect('equal')

        ax.set_title(t)
        map_gdf.plot(ax=ax, color='#FFFFFF00', edgecolor='black', zorder=1)
        map_gdf.centroid.plot(ax=ax, color='blue', zorder=1, label='centroid')
        t_cabs_gdf.plot(ax=ax, color='red', markersize=1, zorder=0, label='user')

        ax.text(map_bbox[0], map_bbox[3]-0.01, 'Points: {}'.format(len(t_cabs_gdf)), color='k', fontsize=10)

    for row in range(nb_rows):
        for col in range(nb_cols):
            index = row * nb_cols + col
            if index >= len(time_series):
                axes[row, col].remove()

    axes[0, 0].legend(loc='upper right')
    fig.tight_layout()
    plt.show()


def main():
    base_time = SF_TZ.localize(datetime(2008, 5, 24, 0, 0, 0)).timestamp()
    gpx_filename = os.path.join(DATA_PATH, 'osm', 'gpx_output.gpx')
    gpx_xml = ET.parse(gpx_filename)
    tracks = gpx_xml.getroot().findall('trk')

    records = []
    for (track_index, track) in enumerate(tracks):
        name = track.find('name').text
        for point in track.iter('trkpt'):
            lon = float(point.attrib['lon'])
            lat = float(point.attrib['lat'])
            time = float(point.find('time').text)
            row = {'user': name, 'lon': lon, 'lat': lat, 'time': time + base_time}
            records.append(row)

    df = pd.DataFrame.from_records(records)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)

    bbox = {'lon': [-122.5160063624, -122.3754337591], 'lat': [37.7093, 37.8112472822]}
    for (key, value) in iteritems(bbox):
        df = df[df[key].between(*value)]

    plot_count(df)
    # plot_on_map(df)


if __name__ == '__main__':
    main()
