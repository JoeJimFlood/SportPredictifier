import pandas as pd
import numpy as np
import os
from math import log2
from scipy.stats import entropy

directions = ['F', 'A']

def compliment_direction(direction):
    if direction == 'F':
        return 'A'
    elif direction == 'A':
        return 'F'
    else:
        raise IOError('{} is an invalid direction. Must be "F" or "A"'.format(direction))

def cap_probability(p): #Maybe make enpoints configurable
    return np.minimum(
        np.maximum(
            p, 0),
        1)

def create_score_table(directory, team, schedule, score_settings):
    columns = ['ROUND', 'OPP', 'VENUE']
    for direction in directions:
        for score_type in score_settings:
            columns.append('{}_{}'.format(score_type, direction))
    columns.append('weight')

    score_table = pd.DataFrame(columns = columns)

    team_schedule = schedule.query('team1 == @team or team2 == @team')

    score_table['ROUND'] = team_schedule['round_number']
    score_table['OPP'] = np.where(team_schedule['team1'] == team, team_schedule['team2'], team_schedule['team1'])
    score_table['VENUE'] = team_schedule['venue']

    score_table.to_csv(os.path.join(directory, team + '.csv'), index = False)

def create_score_tables(settings, teams, stadia, score_settings):

    schedule = pd.read_csv(settings['schedule_file'])
    score_table_path = settings['score_table_path']

    # Assure that all teams and venues are in memory
    invalid_teams = []
    invalid_venues = []

    def check_team(team):
        if team not in teams:
            invalid_teams.append(team)

    def check_venue(venue):
        if venue not in stadia:
            invalid_venues.append(venue)

    schedule['check'] = schedule['team1'].apply(check_team)
    schedule['check'] = schedule['team2'].apply(check_team)
    schedule['check'] = schedule['venue'].apply(check_venue)
    del schedule['check']

    if len(invalid_teams) > 0:
        raise IOError(', '.join(invalid_teams) + ' not defined in teams file')
    if len(invalid_venues) > 0:
        raise IOError(', '.join(invalid_venues) + ' not defined in stadia file')

    for team in teams:
        create_score_table(score_table_path, team, schedule, score_settings)

def calculate_hype(season_settings, results, round_number):
    rankings = pd.read_csv(
        os.path.join(
            season_settings["ranking_directory"],
            season_settings["ranking_filename"] + '.csv').format(round_number),
        index_col = 0
        )

    for result in results:
        results[result]["quality"] = rankings["Quantile"].loc[results[result]["chances"].keys()].mean()
        results[result]["entropy"] = entropy(
            list(
                results[result]["chances"].values()
                ),
            base = 2
            )
        results[result]["hype"] = 100*results[result]["quality"]*results[result]["entropy"]