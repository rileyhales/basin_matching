import glob
import json
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from tslearn.clustering import TimeSeriesKMeans

data0 = '/Users/riley/code/basin_matching/data_0_inputs'
data1 = '/Users/riley/code/basin_matching/data_1_historical_csv'
data2 = '/Users/riley/code/basin_matching/data_2_clusters'
data3 = '/Users/riley/code/basin_matching/data_3_pairbasins'


def pair_basins(monavg_pickle: str, fdc_pickle: str, name_prefix: str):
    print('Creatings matched csv and jsons')
    # read the label results of the kmeans model previously stored as pickle
    ma_labels = TimeSeriesKMeans.from_pickle(monavg_pickle).labels_.tolist()
    fdc_labels = TimeSeriesKMeans.from_pickle(fdc_pickle).labels_.tolist()
    # create a dataframe showing the comid and assigned cluster number
    ids = pd.read_csv(os.path.join(data1, f'{name_prefix}_fdc_normalized.csv'), index_col=0).dropna(axis=1).columns.tolist()
    df = pd.DataFrame(np.transpose([ids, fdc_labels, ma_labels]), columns=('ID', 'fdc_cluster', 'ma_cluster'))
    df.to_csv(os.path.join(data3, f'{name_prefix}_clusters.csv'), index=False)
    # create a json of the paired simulation comids
    df['ma_cluster'] = df['ma_cluster'].astype(int)
    clusters = set(sorted(df['ma_cluster'].values.tolist()))
    pairs = {}
    for i in clusters:
        pairs[i] = df[df['ma_cluster'] == i]['ID'].values.tolist()
    with open(os.path.join(data3, f'{name_prefix}_pairs.json'), 'w') as j:
        j.write(json.dumps(pairs))

    print('Deleting Old GeoJSONs')
    for old in glob.glob(os.path.join(data3, f'{name_prefix}*.geojson')):
        os.remove(old)

    print('Creating GeoJSONs')
    if name_prefix == 'simulated':
        gdf = gpd.read_file(os.path.join(data0, 'south_america-geoglows-catchment', 'south_america-geoglows-catchment.shp'))
        # gdf = gpd.read_file(os.path.join(data0, 'south_america-geoglows-drainagline', 'south_america-geoglows-drainagline.shp'))
        for cluster_number in pairs:
            savepath = os.path.join(data3, f'{name_prefix}_cluster_{cluster_number}.geojson')
            gdf[gdf['COMID'].isin(pairs[cluster_number])].to_file(savepath, driver='GeoJSON')
    else:
        gdf = gpd.read_file(os.path.join(data0, 'ideam_stations.json'))
        for cluster_number in pairs:
            savepath = os.path.join(data3, f'{name_prefix}_cluster_{cluster_number}.geojson')
            gdf[gdf['ID'].isin(pairs[cluster_number])].to_file(savepath, driver='GeoJSON')
    return


sim_monavg = glob.glob(os.path.join(data2, 'sim_monavg*.pickle'))[0]
sim_fdc = glob.glob(os.path.join(data2, 'sim_fdc*.pickle'))[0]
obs_monavg = glob.glob(os.path.join(data2, 'obs_monavg*.pickle'))[0]
obs_fdc = glob.glob(os.path.join(data2, 'obs_fdc*.pickle'))[0]

print('Simulated Data')
pair_basins(sim_monavg, sim_fdc, 'simulated')
print('Observed Data')
pair_basins(obs_monavg, obs_fdc, 'observed')