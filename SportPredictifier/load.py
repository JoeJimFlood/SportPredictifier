import pandas as pd
import numpy as np
import os
import yaml

from .objects import *
from .util import *
from .validation import validate_score_tables

from . import calculate

from .weighting.spatial import get_spatial_weight

def __load_table(object, df, multithreaded = False, result_dict = None):
    """
    Reads a table from a `pandas.DataFrame` into either an `ObjectCollection` or a series of threads

    Parameters
    ----------
    object (class):
        Which object used in the SportPredictifier package to read in
    df (pandas.DataFrame):
        Data frame to read into object
    multithreaded (bool):
        If `True`, the objects will be put onto different threads for multithreading and a list of threads will be returned
        If `False`, an `ObjectCollection` will be returned
    result_dict (bool, optional):
        Dictionary to store results of games. Only needed if `multithreaded` is `True`

    Returns
    -------
    output (list or SportPredictifier.ObjectCollection):
        A list of threads if `multithreaded` is `True` and an `ObjectCollection` containing the data otherwise
    """
    if multithreaded:
        output = []
        for row in df.index:
            output.append(object(result_dict, **df.loc[row]))
            output[-1].start()
    else:
        output = ObjectCollection()
        for row in df.index:
            if 'code' in df.columns: # This is the index
                output[df.loc[row, 'code']] = object(**df.loc[row])
            else:
                output[row] = object(**df.loc[row])
    return output

def __load_stadia(fp):
    '''
    Load the stadia from the CSV file defining them into an `ObjectCollection`:

    Parameters
    ----------
    fp (str):
        CSV file giving the stadium attributes

    Returns
    -------
    stadia (SportPredictifier.ObjectCollection):
        Collection of stadia for use in the model
    '''
    print("Loading stadia")
    stadium_table = pd.read_csv(fp)
    return __load_table(Stadium, stadium_table)

def __load_teams(fp, stadia):
    '''
    Load the teams from the CSV file defining them into an `ObjectCollection`:

    Parameters
    ----------
    fp (str):
        CSV file giving the team attributes

    Returns
    -------
    teams (SportPredictifier.ObjectCollection):
        Collection of teams for use in the model
    '''
    print("Loading teams")
    team_table = pd.read_csv(fp)
    combine_colors(team_table, 'r1', 'g1', 'b1', 'color1')
    combine_colors(team_table, 'r2', 'g2', 'b2', 'color2')
    team_table['stadium'] = team_table['stadium'].map(stadia)
    
    return __load_table(Team, team_table)

def __load_score_settings(fp):
    '''
    Load the score settings from the CSV file defining them into an `ObjectCollection`:

    Parameters
    ----------
    fp (str):
        CSV file giving the score setting attributes

    Returns
    -------
    teams (SportPredictifier.ObjectCollection):
        Collection of score settings for use in the model
    '''
    print("Loading scoring settings")
    score_settings_table = pd.read_csv(fp)
    return __load_table(ScoreSettings, score_settings_table)

def __load_score_tables(score_table_path, query = None, drop_null_score_table_records = False):
    '''
    Loads each of the score tables into an `ObjectCollection` of `pandas.DataFrames`

    Parameters
    ----------
    score_table_path (str):
        Directory with score tables
    query (str, optional):
        Query used to filter each score table using the `pandas.DataFrame.query()` method
    drop_null_score_table_records (bool):
        If true, records with null values will be dropped from the score tables

    Returns
    -------
    score_tables (SportPredictifier.ObjectCollection):
        Collection of score tables stored as `pandas.DataFrame` objects
    '''
    score_tables = ObjectCollection()
    for score_table_file in os.listdir(score_table_path):
        print("Loading score table for {}".format(score_table_file[:-4]))
        if not score_table_file.endswith('.csv'): # Not a score table
            continue
        if query is None:
            score_tables[score_table_file[:-4]] = pd.read_csv(os.path.join(score_table_path, score_table_file))
        else:
            score_tables[score_table_file[:-4]] = pd.read_csv(os.path.join(score_table_path, score_table_file)).query(query)

    if drop_null_score_table_records:
        for team in score_tables:
            score_tables[team] = score_tables[team].dropna()

    return score_tables

def settings(settings_file):
    '''
    Loads a settings.yaml file into a dictionary containing the settings

    Parameters
    ----------
    settings_file (str):
        Filepath of settings file
    
    Returns
    -------
    data (dict):
        Dictionary containing settings
    '''
    with open(settings_file, 'r') as f:
        data = yaml.safe_load(f)
        f.close()
    return data

def data(settings, round_number = None, score_table_query = None, drop_null_score_table_records = False, initializing_season = False):
    '''
    Loads data on the stadia, teams, and score settings into memory. `ObjectCollection` objects containing those objects are returned.
    Spatial weights, team statistics, and opponent statitics are calculated upon loading.

    Parameters
    ----------
    settings (dict):
        Dictionary containing the settings of the competition to be modeled
    round_number (int):
        The round number that will be modeled. Required if spatial weights are being used
    score_table_query (str):
        Query to use when loading the score tables (must work when running `pandas.DataFrame.query()`)
    drop_null_score_table_records (bool):
        Indicates whether or not records containing null values in score tables should be dropped
    initializing_season (bool):
        If initializing the season, calculations aren't performed as the data doesn't yet exist

    Returns
    -------
    stadia (SportPredictifier.ObjectCollection):
        Collection of stadia to be used in the competition
    teams (SportPredictifier.ObjectCollection):
        Collection of teams competing in the competition
    score_settings (SportPredictifier.ObjectCollection):
        Collection of score_settings to be used in the competition
    '''
    stadia = __load_stadia(settings['stadia_file'])
    teams = __load_teams(settings['teams_file'], stadia)
    score_settings = __load_score_settings(settings['score_settings_file'])
    score_tables = __load_score_tables(settings['score_table_path'], score_table_query, drop_null_score_table_records)

    # If initializing season, no data yet exist to perform calculations on
    if not initializing_season:
        validate_score_tables(score_tables, score_settings, teams, stadia, settings)

        if settings['use_spatial_weights']:
            assert round_number is not None, "A round number is needed if calculating spatial weights"
            schedule = pd.read_csv(settings['schedule_file'])
            game_locations = {}
            for _, row in schedule.iterrows():
                game_locations[row['team1']] = row['venue']
                game_locations[row['team2']] = row['venue']
            calculate.spatial_weights(score_tables, teams, stadia)
            calculate.team_stats(teams, score_settings, score_tables, game_locations)
            calculate.opponent_stats(teams, score_settings, score_tables, True)

        else:
            calculate.team_stats(teams, score_settings, score_tables)
            calculate.opponent_stats(teams, score_settings, score_tables)

        calculate.residual_stats(teams, score_settings, score_tables)

    return stadia, teams, score_settings

def schedule(settings, teams, stadia, score_settings, round_number = None, multithreaded = False, result_dict = None, schedule_override = None):
    '''
    Loads the competition schedule from a CSV (or input data frame) into an `ObjectCollection` containing each of the games onto different threads
    so they can be simulated in parallel.

    Parameters
    ----------
    settings (dict):
        Settings for the competition
    teams (SportPredictifier.ObjectCollection):
        Collection of teams competing in the competition
    stadia (SportPredictifier.ObjectCollection):
        Collection of stadia used in the competition
    score_settings (SportPredictifier.ObjectCollection):
        Collection of score settings used in the competision
    round_number (int, optional):
        If not `None`, only that rounds games will be loaded
    multithreaded (bool):
        If true, each game will be loaded onto a different thread and run in parallel
    result_dict (dict):
        Dictionary containing results of games. Required if `multithreaded` is `True`
    schedule_override (pandas.DataFrame):
        Schedule table to override the schedule file if not reading from a CSV
    '''
    print("Loading schedule")

    if schedule_override is None: # Read in schedule from CSV file defined in settings file
        if round_number is None:
            schedule_table = pd.read_csv(settings['schedule_file'])
        else:
            schedule_table = pd.read_csv(settings['schedule_file']).query('round_number == @round_number')
    else: # Override schedule with input data frame
        schedule_table = schedule_override.copy()

    # Add schedule attributes
    schedule_table['n_simulations'] = settings['n_simulations']
    schedule_table['date'] = pd.to_datetime(schedule_table[["year", "month", "day"]])
    schedule_table['score_settings'] = schedule_table.shape[0]*[score_settings]
    del schedule_table['year'], schedule_table['month'], schedule_table['day']

    schedule_table['team1'] = schedule_table['team1'].map(teams)
    schedule_table['team2'] = schedule_table['team2'].map(teams)
    schedule_table['venue'] = schedule_table['venue'].map(stadia)

    schedule_table['store_results'] = settings['store_simulation_results']*np.ones(len(schedule_table), bool)
    schedule_table['min_expected_mean'] = settings['min_expected_mean']*np.ones(len(schedule_table))

    return __load_table(Game, schedule_table, multithreaded, result_dict)