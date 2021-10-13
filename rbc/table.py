import os

import numpy as np
import pandas as pd

from ._vocab import mid_col
from ._vocab import asgn_mid_col
from ._vocab import asgn_gid_col
from ._vocab import reason_col

__all__ = ['get_path', 'read', 'cache', 'gen']


def get_path(workdir: str) -> str:
    """
    Creates the path to the assign table based on the working directory provided

    Args:
        workdir: path to the working directory

    Returns:
        absolute path of the assign_table
    """
    return os.path.join(workdir, 'assign_table.csv')


def gen(workdir) -> pd.DataFrame:
    """
    Joins the drain_table.csv and gauge_table.csv to create the assign_table.csv

    Args:
        workdir: path to the working directory

    Returns:
        None
    """
    # read and merge the tables
    drain_df = pd.read_csv(os.path.join(workdir, 'gis_inputs', 'drain_table.csv'))
    gauge_df = pd.read_csv(os.path.join(workdir, 'gis_inputs', 'gauge_table.csv'))
    assign_table = pd.merge(drain_df, gauge_df, on=mid_col, how='outer')

    # create the new columns
    assign_table[asgn_mid_col] = np.nan
    assign_table[asgn_gid_col] = np.nan
    assign_table[reason_col] = np.nan

    return assign_table


def read(workdir: str) -> pd.DataFrame:
    """
    Reads the assign_table located in the provided directory

    Args:
        workdir: path to the working directory

    Returns:
        assign_table pandas.DataFrame
    """
    return pd.read_csv(get_path(workdir))


def cache(workdir: str, assign_table: pd.DataFrame) -> None:
    """
    Saves the pandas dataframe to a csv in the proper place in the project directory
    A shortcut for pd.DataFrame.to_csv so you don't have to code it all the time

    Args:
        workdir: the project directory path
        assign_table: the assign_table dataframe

    Returns:
        None
    """
    assign_table.to_csv(get_path(workdir), index=False)
    return

