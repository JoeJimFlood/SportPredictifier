import pandas as pd
import numpy as np
import os
import yaml

from .objects import *
from .util import *
from .validation import validate_score_tables

from .weighting.spatial import get_spatial_weight

def __load_table(object, df, multithreaded = False, result_dict = None):
    """
    Reads table from data frame into dictionary of objects
    """
    if multithreaded:
        output = []
        for row in df.index:
            output.append(object(result_dict, **df.loc[row]))
            output[-1].start()
    else:
        output = ObjectCollection()
        for row in df.index:
            if 'code' in df.columns:
                output[df.loc[row, 'code']] = object(**df.loc[row])
            else:
                output[row] = object(**df.loc[row])
    return output

def __load_stadia(fp):
    print("Loading stadia")
    stadium_table = pd.read_csv(fp)
    return __load_table(Stadium, stadium_table)

def __load_teams(fp, stadia):
    print("Loading teams")
    team_table = pd.read_csv(fp)
    combine_colors(team_table, 'r1', 'g1', 'b1', 'color1')
    combine_colors(team_table, 'r2', 'g2', 'b2', 'color2')
    team_table['stadium'] = team_table['stadium'].map(stadia)
    
    return __load_table(Team, team_table)

def __load_score_settings(fp):
    print("Loading scoring settings")
    score_settings_table = pd.read_csv(fp)
    return __load_table(ScoreSettings, score_settings_table)

def __load_score_tables(score_table_path, query = None, drop_null_score_table_records = False):
    '''
    score_table_path (str):
        Directory with score tables
    '''
    score_tables = ObjectCollection()
    for score_table_file in os.listdir(score_table_path):
        print("Loading score table for {}".format(score_table_file[:-4]))
        if not score_table_file.endswith('.csv'):
            continue
        if query is None:
            score_tables[score_table_file[:-4]] = pd.read_csv(os.path.join(score_table_path, score_table_file))
        else:
            score_tables[score_table_file[:-4]] = pd.read_csv(os.path.join(score_table_path, score_table_file)).query(query)

    if drop_null_score_table_records:
        for team in score_tables:
            score_tables[team] = score_tables[team].dropna()

    return score_tables

def __calculate_spatial_weights(score_tables, teams, stadia):
    print("Calculating spatial weights")
    for team in score_tables:
        for stadium in stadia:
            def __get_stadium_specific_weight(location):
                return get_spatial_weight(stadia[location], teams[team].stadium, stadia[stadium])
            score_tables[team]['spatial_weight_{}'.format(stadium)] = score_tables[team]['VENUE'].apply(__get_stadium_specific_weight)

def __calculate_stat(stats, team, direction, score_settings, score_type, score_tables, reference_location = None):

    if reference_location is not None:
        weights = score_tables[team]['spatial_weight_{}'.format(reference_location)]
    else:
        weights = score_tables[team]['weight']

    if score_settings[score_type].prob:
        condition = score_settings[score_type].condition.replace('{F}', direction).replace('{A}', compliment_direction(direction))
        if score_tables[team].eval(condition).sum() == 0:
            stats[direction][score_type] = score_settings[score_type].base
        else:
            stats[direction][score_type] = (score_tables[team][score_type + '_' + direction]*score_tables[team]['weight']).sum() / (score_tables[team].eval(condition)*score_tables[team]['weight']).sum()
                        
    else:
        if score_settings[score_type].opp_effect:
            stats[direction][score_type] = np.average(
                score_tables[team][score_type + '_' + direction],
                weights = weights
            )
        else: # Calculating the weighted variance here since no residual stats will be relevant if opp_effect is False
            stats[direction][score_type] = (np.average(
                score_tables[team][score_type + '_' + direction],
                weights = weights
            ),
                                            weighted_variance(
                score_tables[team][score_type + '_' + direction],
                weights = weights
                ))

def __get_team_stats(teams, score_settings, score_tables, game_locations = None):
    print("Calculating team statistics")
    assert all(team in score_tables for team in teams), "All teams must have a score table"
    for team in teams:

        stats = {}
        for direction in directions:
            stats[direction] = {}
            for score_type in score_settings:
                if game_locations is not None and team in game_locations: # Team is not playing if latter is False
                    __calculate_stat(stats, team, direction, score_settings, score_type, score_tables, game_locations[team])
                else:
                    __calculate_stat(stats, team, direction, score_settings, score_type, score_tables)
 
        teams[team].stats = stats

def __get_opponent_stats(teams, score_settings, score_tables, use_spatial_weights = False):
    print("Calculating opponent statistics")
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
                if use_spatial_weights:
                    def __get_opponent_stat(opponent):
                        stats = {direction: {}}
                        venue = score_tables[team].query('OPP == @opponent').iloc[0]['VENUE']
                        __calculate_stat(stats, opponent, direction, score_settings, score_type, score_tables, venue)
                        return stats[direction][score_type]
                    score_tables[team]['_'.join(['OPP', score_type, direction])] = score_tables[team]['OPP'].apply(__get_opponent_stat)
                else:
                    score_tables[team]['_'.join(['OPP', score_type, direction])] = score_tables[team]['OPP'].map(statmaps[direction][score_type])

def __get_residual_stats(teams, score_settings, score_tables):
    print("Calculating residual statistics")
    for team in score_tables:
        for direction in directions:
            for score_type in score_settings:
                if score_settings[score_type].prob:
                    condition = score_settings[score_type].condition.replace('{F}', direction).replace('{A}', compliment_direction(direction))
                    score_tables[team]['_'.join(['RES', score_type, direction])] = score_tables[team]['_'.join([score_type, direction])]/score_tables[team].eval(condition) - score_tables[team]['_'.join(['OPP', score_type, compliment_direction(direction)])]
                else:
                    score_tables[team]['_'.join(['RES', score_type, direction])] = score_tables[team]['_'.join([score_type, direction])] - score_tables[team]['_'.join(['OPP', score_type, compliment_direction(direction)])]

    for team in teams:
        for direction in directions:
            for score_type in score_settings:
                if score_settings[score_type].prob:
                    condition = score_settings[score_type].condition.replace('{F}', direction).replace('{A}', compliment_direction(direction))
                    try:
                        values = score_tables[team]['_'.join(['RES', score_type, direction])].values
                        weights = (score_tables[team].eval(condition) * score_tables[team]['weight'])
                        to_use = ~np.isnan(values)
                        teams[team].stats[direction]['RES_' + score_type] = np.average(
                            values[to_use],
                            weights = weights[to_use]
                            )
                    except ZeroDivisionError:
                        teams[team].stats[direction]['RES_' + score_type] = 0
                else:
                    teams[team].stats[direction]['RES_' + score_type] = (
                        np.average(
                            score_tables[team]['_'.join(['RES', score_type, direction])],
                            weights = score_tables[team]['weight']
                            ),
                        weighted_variance(
                            score_tables[team]['_'.join(['RES', score_type, direction])],
                            weights = score_tables[team]['weight']
                            )
                    )

def settings(settings_file):
    with open(settings_file, 'r') as f:
        data = yaml.safe_load(f)
        f.close()
    return data

def data(settings, round_number = None, score_table_query = None, drop_null_score_table_records = False, initializing_season = False):
    stadia = __load_stadia(settings['stadia_file'])
    teams = __load_teams(settings['teams_file'], stadia)
    score_settings = __load_score_settings(settings['score_settings_file'])
    score_tables = __load_score_tables(settings['score_table_path'], score_table_query, drop_null_score_table_records)

    if not initializing_season:
        validate_score_tables(score_tables, score_settings, teams, stadia, settings)

    if not initializing_season:
        if settings['use_spatial_weights']:
            assert round_number is not None, "A round number is needed if calculating travel weights"
            schedule = pd.read_csv(settings['schedule_file'])
            game_locations = {}
            for _, row in schedule.iterrows():
                game_locations[row['team1']] = row['venue']
                game_locations[row['team2']] = row['venue']
            __calculate_spatial_weights(score_tables, teams, stadia)
            __get_team_stats(teams, score_settings, score_tables, game_locations)
            __get_opponent_stats(teams, score_settings, score_tables, True)

        else:
            __get_team_stats(teams, score_settings, score_tables)
            __get_opponent_stats(teams, score_settings, score_tables)

        __get_residual_stats(teams, score_settings, score_tables)

    return stadia, teams, score_settings

def schedule(settings, teams, stadia, score_settings, round_number = None, multithreaded = False, result_dict = None, schedule_override = None):
    print("Loading schedule")
    if schedule_override is None:
        if round_number is None:
            schedule_table = pd.read_csv(settings['schedule_file'])
        else:
            schedule_table = pd.read_csv(settings['schedule_file']).query('round_number == @round_number')
    else:
        schedule_table = schedule_override.copy()

    schedule_table['n_simulations'] = settings['n_simulations']
    schedule_table['date'] = pd.to_datetime(schedule_table[["year", "month", "day"]])
    schedule_table['score_settings'] = schedule_table.shape[0]*[score_settings]
    del schedule_table['year'], schedule_table['month'], schedule_table['day']

    schedule_table['team1'] = schedule_table['team1'].map(teams)
    schedule_table['team2'] = schedule_table['team2'].map(teams)
    schedule_table['venue'] = schedule_table['venue'].map(stadia)

    #schedule_table['result_dict'] = result_dict

    return __load_table(Game, schedule_table, multithreaded, result_dict)