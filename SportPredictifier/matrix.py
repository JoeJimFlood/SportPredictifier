import pandas as pd
import numpy as np

def __get_team_list(matrix_settings):
    teams = []
    for group in matrix_settings['teams']:
        teams += matrix_settings['teams'][group]
    return teams

def __assign_venue(team1, team2, matrix_settings):
    for group in matrix_settings['teams']:
        if team1 in matrix_settings['teams'][group] and team2 in matrix_settings['teams'][group]:
            if matrix_settings['teams'][group].index(team1) < matrix_settings['teams'][group].index(team2):
                return team1
            else:
                return team2

    return list(matrix_settings['neutral_venues'].keys())[0] # TODO: Make this more flexible

def __get_matchup_list(team_list, matrix_settings):
    matchups = []
    N = len(team_list)
    for i in range(N):
        for j in range(i+1, N):
            matchups.append((team_list[i], team_list[j], __assign_venue(team_list[i], team_list[j], matrix_settings)))
    return matchups

def __get_allocated_teams(matchups):
    allocated_teams = []
    for matchup in matchups:
        allocated_teams.append(matchup[0])
        allocated_teams.append(matchup[1])
    return allocated_teams

def __allocate_matchups(matchups, roundno = 0):

    matchups_by_round = {}
    while len(matchups) > 0:
        matchups_by_round[roundno] = []
        for matchup in matchups:
            allocated_teams = __get_allocated_teams(matchups_by_round[roundno])
            if matchup[0] in allocated_teams or matchup[1] in allocated_teams:
                continue
            matchups_by_round[roundno].append(matchup)
        
        for matchup in matchups_by_round[roundno]:
            matchups.remove(matchup)

        roundno += 1

    return matchups_by_round

def generate_schedule(matrix_settings):
    print('Generating Matrix Schedule')
    #matchups
    #for group in matrix_settings['teams']:
    #    matchups += __get_matchup_list(matrix_settings['teams'][group])

    #if 'neutral_venues' in matrix_settings:
    #    for venue in matrix_settings['neutral_venues']:
    #        for team1 in matrix_settings['teams'][matrix_settings['neutral_venues'][venue][0]]:
    #            for team2 in matrix_settings['teams'][matrix_settings['neutral_venues'][venue][1]]:
    #                matchups.append((team1, team2, venue))

    teams = __get_team_list(matrix_settings)
    matchups = __get_matchup_list(teams, matrix_settings)
    matchups_by_round = __allocate_matchups(matchups, matrix_settings['round_number'])

    matrix_schedule = pd.DataFrame(columns = ['round_number',
                                              'year',
                                              'month',
                                              'day',
                                              'team1',
                                              'team2',
                                              'venue',
                                              'knockout'])

    ix = 0
    #roundno = matrix_settings['round_number']
    #for matchup in matchups:
    #    matrix_schedule.loc[ix] = [roundno, 2023, 1, 1] + list(matchup) + [True]
    #    ix += 1
    #    roundno += 1
    
    for roundno in matchups_by_round:
        for matchup in matchups_by_round[roundno]:
            matrix_schedule.loc[ix] = [roundno, 2023, 1, 1] + list(matchup) + [True]
            ix += 1

    return matrix_schedule

def write_matrix(matrix_settings, results, outfile):
    teams = __get_team_list(matrix_settings)
    N = len(teams)
    matrix = pd.DataFrame(np.empty((N, N), float),
                          index = teams,
                          columns = teams)

    for team in teams:
        matrix.loc[team, team] = np.nan

    for matchup in results:
        chances = results[matchup]['chances']
        (team1, team2) = chances.keys()
        matrix.loc[team1, team2] = chances[team1]
        matrix.loc[team2, team1] = chances[team2]

    matrix.to_csv(outfile)