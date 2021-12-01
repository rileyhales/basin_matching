import os
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd

from ._vocab import mid_col
from ._vocab import gid_col
from ._vocab import reason_col
from ._vocab import metric_nc_name_list

import matplotlib as mpl
import matplotlib.pyplot as plt
import contextily as cx

__all__ = ['generate_all', 'clip_by_assignment', 'clip_by_cluster', 'clip_by_unassigned', 'clip_by_ids',
           'validation_maps']


def generate_all(workdir: str, assign_table: pd.DataFrame, drain_shape: str, prefix: str = '',
                 id_column: str = mid_col) -> None:
    """
    Runs all the clip functions which create subsets of the drainage lines GIS dataset based on how they were assigned
    for bias correction.

    Args:
        workdir: the path to the working directory for the project
        assign_table: the assign_table dataframe
        drain_shape: path to a drainage line shapefile which can be clipped
        prefix: a prefix for names of the outputs to distinguish between data generated at separate instances
        id_column: name of the id column in the attributes of the shape table

    Returns:
        None
    """
    clip_by_assignment(workdir, assign_table, drain_shape, prefix, id_column)
    clip_by_cluster(workdir, assign_table, drain_shape, prefix, id_column)
    clip_by_unassigned(workdir, assign_table, drain_shape, prefix, id_column)
    return


def clip_by_assignment(workdir: str, assign_table: pd.DataFrame, drain_shape: str, prefix: str = '',
                       id_column: str = mid_col) -> None:
    """
    Creates geojsons (in workdir/gis_outputs) for each unique value in the assignment column

    Args:
        workdir: the path to the working directory for the project
        assign_table: the assign_table dataframe
        drain_shape: path to a drainage line shapefile which can be clipped
        prefix: a prefix for names of the outputs to distinguish between data generated at separate instances
        id_column: name of the id column in the attributes of the shape table

    Returns:
        None
    """
    # read the drainage line shapefile
    dl = gpd.read_file(drain_shape)
    save_dir = os.path.join(workdir, 'gis_outputs')

    # get the unique list of assignment reasons
    for reason in set(assign_table[reason_col].dropna().values):
        ids = assign_table[assign_table[reason_col] == reason][mid_col].values
        subset = dl[dl[id_column].isin(ids)]
        name = f'{prefix}{"_" if prefix else ""}assignments_{reason}.json'
        if subset.empty:
            continue
        else:
            subset.to_file(os.path.join(save_dir, name), driver='GeoJSON')
    return


def clip_by_cluster(workdir: str, assign_table: pd.DataFrame, drain_shape: str, prefix: str = '',
                    id_column: str = mid_col) -> None:
    """
    Creates GIS files (in workdir/gis_outputs) of the drainage lines based on which fdc cluster they were assigned to

    Args:
        workdir: the path to the working directory for the project
        assign_table: the assign_table dataframe
        drain_shape: path to a drainage line shapefile which can be clipped
        prefix: optional, a prefix to prepend to each created file's name
        id_column: name of the id column in the attributes of the shape table

    Returns:
        None
    """
    dl_gdf = gpd.read_file(drain_shape)
    cluster_types = [a for a in assign_table if 'cluster' in a]
    for ctype in cluster_types:
        for gnum in sorted(set(assign_table[ctype].dropna().values)):
            savepath = os.path.join(workdir, 'gis_outputs', f'{prefix}{"_" if prefix else ""}{ctype}-{int(gnum)}.json')
            ids = assign_table[assign_table[ctype] == gnum][mid_col].values
            if dl_gdf[dl_gdf[id_column].isin(ids)].empty:
                continue
            else:
                dl_gdf[dl_gdf[id_column].isin(ids)].to_file(savepath, driver='GeoJSON')
    return


def clip_by_unassigned(workdir: str, assign_table: pd.DataFrame, drain_shape: str, prefix: str = '',
                       id_column: str = mid_col) -> None:
    """
    Creates geojsons (in workdir/gis_outputs) of the drainage lines which haven't been assigned a gauge yet

    Args:
        workdir: the path to the working directory for the project
        assign_table: the assign_table dataframe
        drain_shape: path to a drainage line shapefile which can be clipped
        prefix: optional, a prefix to prepend to each created file's name
        id_column: name of the id column in the attributes of the shape table

    Returns:
        None
    """
    dl_gdf = gpd.read_file(drain_shape)
    ids = assign_table[assign_table[reason_col].isna()][mid_col].values
    subset = dl_gdf[dl_gdf[id_column].isin(ids)]
    if subset.empty:
        warnings.warn('Empty filter: No streams are unassigned')
        return
    savepath = os.path.join(workdir, 'gis_outputs', f'{prefix}{"_" if prefix else ""}assignments_unassigned.json')
    subset.to_file(savepath, driver='GeoJSON')
    return


def clip_by_ids(workdir: str, ids: list, drain_shape: str, prefix: str = '',
                id_column: str = mid_col) -> None:
    """
    Creates geojsons (in workdir/gis_outputs) of the subset of 'drain_shape' with an ID in the specified list

    Args:
        workdir: path to the project directory
        ids: any iterable containing a series of model_ids
        drain_shape: path to the drainage shapefile to be clipped
        prefix: optional, a prefix to prepend to each created file's name
        id_column: name of the id column in the attributes of the shape table

    Returns:
        None
    """
    dl = gpd.read_file(drain_shape)
    save_dir = os.path.join(workdir, 'gis_outputs')
    name = f'{prefix}{"_" if prefix else ""}id_subset.json'
    dl[dl[id_column].isin(ids)].to_file(os.path.join(save_dir, name), driver='GeoJSON')
    return


def validation_maps(workdir: str, gauge_shape: str, val_table: pd.DataFrame = None, prefix: str = '') -> None:
    """
    Creates geojsons (in workdir/gis_outputs) of subsets of the gauge_shape.
    1 is the fill gauge shape with added attribute columns for all the computed stats. There are 2 for each of the 5
    validation groups; 1 which shows the gauges included in the validation set and 1 which shows gauges that were
    excluded from the validation set.

    Args:
        workdir: path to the project directory
        val_table: the validation table produced by hbc.validate
        gauge_shape: path to the gauge locations shapefile
        prefix: optional, a prefix to prepend to each created file's name

    Returns:
        None
    """
    if val_table is None:
        val_table = pd.read_csv(os.path.join(workdir, 'validation_runs', 'val_table.csv'))
    save_dir = os.path.join(workdir, 'gis_outputs')

    # merge gauge table with the validation table
    gdf = gpd.read_file(gauge_shape)
    gdf = gdf.merge(val_table, on=gid_col, how='inner')
    gdf.to_file(os.path.join(save_dir, 'gauges_with_validation_stats.json'), driver='GeoJSON')

    core_columns = [mid_col, gid_col, 'geometry']

    # generate gis files by validation run, by stat, and by included/excluded
    for val_set in ('50', '60', '70', '80', '90'):
        for metric in metric_nc_name_list:
            # select only columns for the validation run we're iterating on - too complex for filter/regex
            cols_to_select = core_columns + [val_set, f'{metric}_{val_set}']
            gdf_sub = gdf[cols_to_select]
            gdf_sub = gdf_sub.rename(columns={f'{metric}_{val_set}': metric})

            name = f'{prefix}{"_" if prefix else ""}valset_{val_set}_{metric}_included.json'
            gdf_sub[gdf_sub[val_set] == 1].to_file(os.path.join(save_dir, name), driver='GeoJSON')

            name = f'{prefix}{"_" if prefix else ""}valset_{val_set}_{metric}_excluded.json'
            exc = gdf_sub[gdf_sub[val_set] == 0]
            exc.to_file(os.path.join(save_dir, name), driver='GeoJSON')
            if metric == 'KGE2012':
                histomaps(exc, metric, val_set, workdir)

    return


def histomaps(gdf: gpd.GeoDataFrame, metric: str, prct: str, workdir: str) -> None:
    core_columns = [mid_col, gid_col, 'geometry']
    # world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    # world.plot(ax=axm, color='white', edgecolor='black')

    colors = ['#dc112e', '#d6db12', '#da9707', '#13c208', '#0824c2']
    bins = [-10, 0, 0.25, 0.5, 0.75, 1]
    cmap = mpl.colors.ListedColormap(colors)
    norm = mpl.colors.BoundaryNorm(boundaries=bins, ncolors=len(cmap.colors))
    title = metric.replace('KGE2012', 'Kling Gupta Efficiency 2012 - ') + f' {prct}% Gauges Excluded'

    hist_groups = []
    hist_colors = []
    categorize_by = [-np.inf, 0, 0.25, 0.5, 0.75, 1]
    for idx in range(len(categorize_by) - 1):
        gdfsub = gdf[gdf[metric] >= categorize_by[idx]]
        gdfsub = gdfsub[gdfsub[metric] < categorize_by[idx + 1]]
        if not gdfsub.empty:
            hist_groups.append(gdfsub[metric].values)
            hist_colors.append(colors[idx])

    fig, (axh, axm) = plt.subplots(
        1, 2, tight_layout=True, figsize=(9, 5), dpi=400, gridspec_kw={'width_ratios': [1, 1]})
    fig.suptitle(title, fontsize=20)

    median = round(gdf[metric].median(), 2)
    axh.set_title(f'Histogram (Median = {median})')
    axh.set_ylabel('Count')
    axh.set_xlabel('KGE 2012')
    axh.hist(hist_groups, color=hist_colors, bins=25, histtype='barstacked', edgecolor='black')
    axh.axvline(median, color='k', linestyle='dashed', linewidth=3)

    axm.set_title('Gauge Map')
    axm.set_ylabel('Latitude')
    axm.set_xlabel('Longitude')
    axm.set_xticks([])
    axm.set_yticks([])
    gdf[core_columns + [metric, ]].to_crs(epsg=3857).plot(
        metric, ax=axm, cmap=cmap, norm=norm, legend=True, markersize=10)
    cx.add_basemap(ax=axm, zoom=9, source=cx.providers.Esri.WorldTopoMap, attribution='')

    fig.show()
    fig.savefig(os.path.join(workdir, 'gis_outputs', f'{metric}_{prct}.png'))
    return