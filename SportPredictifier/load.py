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
        for direction in ['F', 'A']:
            for score_type in score_settings:
                col = score_type + '_' + direction
                stats[col] = np.average(
                    score_tables[team][col],
                    weights = score_tables[team]['weight']
                )
        teams[team].stats = stats