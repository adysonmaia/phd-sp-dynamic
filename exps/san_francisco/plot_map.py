from future.utils import iteritems
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pmdarima as pm


def main():
    crs = "EPSG:4326"
    sf_shape_file = 'input/san_francisco/shapefile/bay_area_zip_codes/' \
                    'geo_export_2defef9a-b2e1-4ddd-84f6-1a131dd80410.shp'

    map_bbox = {'lon': [-122.5160063624, -122.3754337591], 'lat': [37.7093, 37.8112472822]}
    # nodes_bbox = {'lon': [-122.452, -122.3754337591], 'lat': [37.7315, 37.8112472822]}
    nodes_bbox = {'lon': [-122.5160063624, -122.3754337591], 'lat': [37.7093, 37.8112472822]}

    map_gdf = gpd.read_file(sf_shape_file)
    map_gdf = map_gdf.to_crs(crs)

    map_gdf = map_gdf.cx[map_bbox['lon'][0]:map_bbox['lon'][1], map_bbox['lat'][0]:map_bbox['lat'][1]]
    centroids = map_gdf.centroid.cx[nodes_bbox['lon'][0]:nodes_bbox['lon'][1],
                                    nodes_bbox['lat'][0]:nodes_bbox['lat'][1]]

    area_with_nodes_gdf = map_gdf.loc[centroids.index]
    area_without_nodes_gdf = map_gdf.loc[~map_gdf.index.isin(centroids.index)]

    # fig, ax = plt.subplots(figsize=(16, 9))
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    if len(area_without_nodes_gdf) > 0:
        area_without_nodes_gdf.plot(ax=ax, color='#FFFFFF00', edgecolor='black', zorder=1)
    if len(area_with_nodes_gdf) > 0:
        map_color = '#FFFFFF00' if len(area_without_nodes_gdf) == 0 else 'whitesmoke'
        area_with_nodes_gdf.plot(ax=ax, color=map_color, edgecolor='black', zorder=1)
        area_with_nodes_gdf.centroid.plot(ax=ax, color='blue', zorder=2, label='Edge Computing Nodes')

    for (index, row) in area_with_nodes_gdf.iterrows():
        centroid = row.geometry.centroid
        neighbors_gdf = area_with_nodes_gdf[area_with_nodes_gdf.touches(row.geometry)]
        for (neighbor_index, neighbor) in neighbors_gdf.iterrows():
            neighbor_centroid = neighbor.geometry.centroid
            ax.plot([centroid.x, neighbor_centroid.x], [centroid.y, neighbor_centroid.y],
                    color='blue', linewidth=1.0, zorder=1)

    # ax.set_ylabel('Latitude')
    # ax.set_xlabel('Longitude')
    # ax.legend(loc='upper right')
    plt.axis('off')
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()
