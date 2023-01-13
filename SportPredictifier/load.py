import pandas as pd
import numpy as np
import os
import yaml

from .objects import *
from .util import *

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
    output = ObjectCollection()
    for row in df.index:
        if 'code' in df.columns:
            output[df.loc[row, 'code']] = object(**df.loc[row])
        else:
            output[row] = object(**df.loc[row])
    return output

def __load_stadia(fp):
    stadium_table = pd.read_csv(fp)
    return __load_table(Stadium, stadium_table)

def __load_teams(fp, stadia):
    team_table = pd.read_csv(fp)
    __combine_colors(team_table, 'r1', 'g1', 'b1', 'color1')
    __combine_colors(team_table, 'r2', 'g2', 'b2', 'color2')
    team_table['stadium'] = team_table['stadium'].map(stadia)
    
    return __load_table(Team, team_table)

def __load_score_settings(fp):
    score_settings_table = pd.read_csv(fp)
    return __load_table(ScoreSettings, score_settings_table)

def __load_score_tables(score_table_path):
    score_tables = ObjectCollection()
    for score_table_file in os.listdir(score_table_path):
        score_tables[score_table_file[:-4]] = pd.read_csv(os.path.join(score_table_path, score_table_file))
    return score_tables

def __get_team_stats(teams, score_settings, score_tables):
    assert all(team in score_tables for team in teams), "All teams must have a score table"
    for team in teams:
        stats = {}
        for direction in directions:
            stats[direction] = {}
            for score_type in score_settings:
                stats[direction][score_type] = np.average(
                    score_tables[team][score_type + '_' + direction],
                    weights = score_tables[team]['weight']
                )
        teams[team].stats = stats

def __get_opponent_stats(teams, score_settings, score_tables):
    statmaps = {}
    for direction in directions:
        statmaps[direction] = {}
        for score_type in score_settings:
            statmaps[direction][score_type] = {}
            for team in teams:
                statmaps[direction][score_type][team] = teams[team].stats[direction][score_type]

    for team in score_tables:
        for direction in directions:
            for score_type in score_settings:
                score_tables[team]['_'.join(['OPP', score_type, direction])] = score_tables[team]['OPP'].map(statmaps[compliment_direction(direction)][score_type])

def __get_residual_stats(teams, score_settings, score_tables):
    for team in score_tables:
        for direction in directions:
            for score_type in score_settings:
                score_tables[team]['_'.join(['RES', score_type, direction])] = score_tables[team]['_'.join([score_type, direction])] - score_tables[team]['_'.join(['OPP', score_type, compliment_direction(direction)])]

    for team in teams:
        for direction in directions:
            for score_type in score_settings:
                teams[team].stats[direction]['RES_' + score_type] = np.average(score_tables[team]['_'.join(['RES', score_type, direction])],
                                                                               weights = score_tables[team]['weight'])

def settings(settings_file):
    with open(settings_file, 'r') as f:
        data = yaml.safe_load(f)
        f.close()
    return data

def data(settings):
    stadia = __load_stadia(settings['stadia_file'])
    teams = __load_teams(settings['teams_file'], stadia)
    score_settings = __load_score_settings(settings['score_settings_file'])
    score_tables = __load_score_tables(settings['score_table_path'])

    __get_team_stats(teams, score_settings, score_tables)
    __get_opponent_stats(teams, score_settings, score_tables)
    __get_residual_stats(teams, score_settings, score_tables)

    return stadia, teams, score_settings

def schedule(settings, teams, stadia, score_settings):
    schedule_table = pd.read_csv(settings['schedule_file'])
    schedule_table['date'] = pd.to_datetime(schedule_table[["year", "month", "day"]])
    schedule_table['score_settings'] = schedule_table.shape[0]*[score_settings]
    del schedule_table['year'], schedule_table['month'], schedule_table['day']

    schedule_table['team1'] = schedule_table['team1'].map(teams)
    schedule_table['team2'] = schedule_table['team2'].map(teams)
    schedule_table['venue'] = schedule_table['venue'].map(stadia)

    return __load_table(Game, schedule_table)