import pandas as pd
import numpy as np
import os
from math import log2

directions = ['F', 'A']

def compliment_direction(direction):
    '''
    Returns the opposite direction between "F" (for) and "A" (against)

    Parameters
    ----------
    direction (str):
        Ether "F" for "for" or "A" for "against"
    
    Returns
    -------
    compliment_direction (str):
        Opposite of input direction
    '''
    if direction == 'F':
        return 'A'
    elif direction == 'A':
        return 'F'
    else:
        raise IOError('{} is an invalid direction. Must be "F" or "A"'.format(direction))

def __int2hex(n):
    '''
    Converts an integer to a 2-digit hexidecimal number

    Parameters
    ----------
    n (int):
        Base-10 integer to convert to hexadecimal
    
    Returns
    -------
    hex (str):
        String of 2-digit hexadecimal number
    '''
    n = hex(n)
    return (4-len(n))*'0' + n[2:]

def combine_colors(df, r, g, b, out_field, cleanup = True):
    """
    Combines rgb coordinates into a single hex string. This is done in place for a data frame

    Parameters
    ----------
    df (pandas.DataFrame):
        Data frame containing columns with r, g, and b values
    r (str):
        Column of `df` with the amount of red
    g (str):
        Column of `df` with the amount of green
    b (str):
        Column of `df` with the amount of blue
    out_field (str):
        Name of new column to be added with the result
    Cleanup (bool):
        If `True`, the `r`, `g`, and `b` columns will be deleted from memory
    """
    df[out_field] = '#' + df[r].apply(__int2hex) + df[g].apply(__int2hex) + df[b].apply(__int2hex)
    if cleanup:
        del df[r]
        del df[g]
        del df[b]

def cap_probability(p): #Maybe make enpoints configurable
    '''
    Caps the probability at 0 or 1 if it is outside that range

    Parameters
    ----------
    p (float):
        Probability value
    
    Returns
    -------
    capped_prob (float):
        `p` capped at 0 if lower than that or 1 if higher than that
    '''
    return np.minimum(
        np.maximum(
            p, 0),
        1)

def run_multithreaded_games(games):
    '''
    Runs simulations of multiple games on different threads

    Parameters
    ----------
    games (SportPredictifier.ObjectCollection):
        Collection of games to simulate
    '''
    for game in games:
        game.join()

def create_score_table(directory, team, schedule, score_settings):
    '''
    Creates a blank score table when initializing a season based on the schedule and score_settings

    Parameters
    ----------
    directory (str):
        Directory to write score table to
    team (str):
        Code of team to create score table for
    schedule (pandas.DataFrame):
        Schedule of entire competition
    score_settings (SportPredictifier.ObjectCollection):
        Collection of score settings for the competition
    '''
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
    '''
    Creates empty score tables for every team when initializing a season

    Parameters
    ----------
    settings (dict):
        Settings for the competition
    teams (SportPredictifier.ObjectCollection):
        Collection of teams competing in the competition
    stadia (SportPredictifier.ObjectCollection):
        Collection of stadia used in the competition
    score_settings (SportPredictifier.ObjectCollection):
         Collection of score settings for the competition
    '''
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

def get_plot_shape(n_games):
    '''
    Obtains the plot shape based on the number of games within a group when plotting the pie charts

    Parameters
    ----------
    n_games (int):
        Number of games ranging from 1 to 9

    Returns
    -------
    plot_size (tuple):
        A shape of plots that can be an argument to matplotlib.pyplot.subplot()
    '''
    plot_sizes = {
        1: (1, 1),
        2: (1, 2),
        3: (2, 2),
        4: (2, 2),
        5: (2, 3),
        6: (2, 3),
        7: (3, 3),
        8: (3, 3),
        9: (3, 3),
        }
    return plot_sizes[n_games]

def get_font_size(n_games):
    '''
    Returns the font size to be used in pie charts based on the number of games

    Parameters
    ----------
    n_games (int):
        Number of games ranging from 1 to 9
    
    Returns
    -------
    font_size (int):
        Size of font to used for text in plots
    '''
    if n_games == 1:
        return 48
    elif n_games < 5:
        return 18
    else:
        return 12