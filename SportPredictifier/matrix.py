import pandas as pd
import numpy as np

def __get_matchup_list(team_list):
    matchups = []
    N = len(team_list)
    for i in range(N):
        for j in range(i+1, N):
            matchups.append((team_list[i], team_list[j], team_list[i]))
    return matchups

def generate_schedule(matrix_settings):
    print('Generating Matrix Schedule')
    matchups = []
    for group in matrix_settings['teams']:
        matchups += __get_matchup_list(matrix_settings['teams'][group])

    if 'neutral_venues' in matrix_settings:
        for venue in matrix_settings['neutral_venues']:
            for team1 in matrix_settings['teams'][matrix_settings['neutral_venues'][venue][0]]:
                for team2 in matrix_settings['teams'][matrix_settings['neutral_venues'][venue][1]]:
                    matchups.append((team1, team2, venue))

    matrix_schedule = pd.DataFrame(columns = ['round_number',
                                              'year',
                                              'month',
                                              'day',
                                              'team1',
                                              'team2',
                                              'venue',
                                              'knockout'])

    ix = 0
    roundno = matrix_settings['round_number']
    for matchup in matchups:
        matrix_schedule.loc[ix] = [roundno, 2023, 1, 1] + list(matchup) + [True]
        ix += 1
        roundno += 1

    return matrix_schedule