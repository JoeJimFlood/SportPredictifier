import pandas as pd
import numpy as np
import os
from collections import OrderedDict

from .objects import *

def __int2hex(n):
    n = hex(n)
    return (4-len(n))*'0' + n[2:]

def __combine_colors(df, r, g, b, out_field, cleanup = True):
    """
    Combines rgb coordinates into a single hex

    Parameters
    ----------

    """
    df[out_field] = '#' + df[r].apply(__int2hex) + df[g].apply(__int2hex) + df[b].apply(__int2hex)
    if cleanup:
        del df[r]
        del df[g]
        del df[b]

def __compliment_direction(direction):
    if direction == 'F':
        return 'A'
    elif direction == 'A':
        return 'F'
    else:
        raise IOError('{} is an invalid direction. Must be "F" or "A"'.format(direction))

__directions = ['F', 'A']

def __load_table(object, df):
    """
    Reads table from data frame into dictionary of objects
    """
    output = OrderedDict()
    df.index = df["code"]
    for row in df.index:
        output[row] = object(**df.loc[row])
    return output

def stadia(fp):
    stadium_table = pd.read_csv(fp)
    return __load_table(Stadium, stadium_table)

def teams(fp, stadia):
    team_table = pd.read_csv(fp)
    __combine_colors(team_table, 'r1', 'g1', 'b1', 'color1')
    __combine_colors(team_table, 'r2', 'g2', 'b2', 'color2')
    team_table['stadium'] = team_table['stadium'].map(stadia)
    
    return __load_table(Team, team_table)

def score_settings(fp):
    score_settings_table = pd.read_csv(fp)
    return __load_table(ScoreSettings, score_settings_table)

def score_tables(score_table_path):
    score_tables = OrderedDict()
    for score_table_file in os.listdir(score_table_path):
        score_tables[score_table_file[:-4]] = pd.read_csv(os.path.join(score_table_path, score_table_file))
    return score_tables

def get_team_stats(teams, score_settings, score_tables):
    assert all(team in score_tables for team in teams), "All teams must have a score table"
    for team in teams:
        stats = {}
        for direction in __directions:
            stats[direction] = {}
            for score_type in score_settings:
                stats[direction][score_type] = np.average(
                    score_tables[team][score_type + '_' + direction],
                    weights = score_tables[team]['weight']
                )
        teams[team].stats = stats

def get_opponent_stats(teams, score_settings, score_tables):
    statmaps = {}
    for direction in __directions:
        statmaps[direction] = {}
        for score_type in score_settings:
            statmaps[direction][score_type] = {}
            for team in teams:
                statmaps[direction][score_type][team] = teams[team].stats[direction][score_type]

    for team in score_tables:
        for direction in __directions:
            for score_type in score_settings:
                score_tables[team]['_'.join(['OPP', score_type, direction])] = score_tables[team]['OPP'].map(statmaps[__compliment_direction(direction)][score_type])

def get_residual_stats(teams, score_settings, score_tables):
    for team in score_tables:
        for direction in __directions:
            for score_type in score_settings:
                score_tables[team]['_'.join(['RES', score_type, direction])] = score_tables[team]['_'.join([score_type, direction])] - score_tables[team]['_'.join(['OPP', score_type, __compliment_direction(direction)])]

    for team in teams:
        for direction in __directions:
            for score_type in score_settings:
                teams[team].stats[direction]['RES_' + score_type] = np.average(score_tables[team]['_'.join(['RES', score_type, direction])],
                                                                               weights = score_tables[team]['weight'])