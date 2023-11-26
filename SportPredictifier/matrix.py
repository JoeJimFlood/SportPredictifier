import pandas as pd
import numpy as np

def __get_team_list(matrix_settings):
    '''
    Obtains a list of all teams given in the matrix settings. It does not separate them by group.

    Parameters
    ----------
    matrix_settings (dict):
        Dictionary of settings for the matrix analysis
    
    Returns
    -------
    teams (list):
        List of teams within matrix analysis
    '''
    teams = []
    for group in matrix_settings['teams']:
        teams += matrix_settings['teams'][group]
    return teams

def __assign_venue(team1, team2, matrix_settings, teams):
    '''
    Assigns the venue to a game based on the two teams playing and the matrix settings. If a matchup is specified to be in a neutral venue, the game will
    be assigned to be at said venue. Otherwise the home of the higher-ranked team (according to the order given in the matrix settings) will be selected.

    Parameters
    ----------
    team1 (str):
        Code of team 1 in the matchup
    team2 (str):
        Code of team 2 in the matchup
    matrix_settings (dict):
        Dictionary of settings for the matrix analysis
    teams (SportPredictifier.ObjectCollection):
        Collection of teams in the competition
    '''
    for group in matrix_settings['teams']:
        if team1 in matrix_settings['teams'][group] and team2 in matrix_settings['teams'][group]:
            if matrix_settings['teams'][group].index(team1) < matrix_settings['teams'][group].index(team2):
                return teams[team1].stadium.code
            else:
                return teams[team2].stadium.code

    return list(matrix_settings['neutral_venues'].keys())[0] # TODO: Make this more flexible

def __get_matchup_list(team_list, matrix_settings, teams):
    '''
    Obtains the list of matchups that will be used in the matrix analysis. A list of every possible matchup and the appropriate venue is returned.

    Parameters
    ----------
    team_list (list):
        List of teams in the matrix analysis
    matrix_settings (dict):
        Dictionary of settings for the matrix analysis
    teams (SportPredictifier.ObjectCollection):
        Collection of teams in the competition

    Returns
    -------
    matchups (list):
        List of all possible matchups to be placed into a schedule. Every element is a length-4 tuple containing the codes for each team,
        the venue, and the collection of all teams in the competition.
    '''
    matchups = []
    N = len(team_list)
    for i in range(N):
        for j in range(i+1, N):
            matchups.append((team_list[i], team_list[j], __assign_venue(team_list[i], team_list[j], matrix_settings, teams)))
    return matchups

def __get_allocated_teams(matchups):
    '''
    Obtains list of teams within matchups. This is used to prevent matchups with the same team from being allocated into the round.

    Parameters
    ----------
    matchups (list):
        List of length-4 tuples indicating each team, the venue, and a collection of all teams

    Returns
    -------
    allocated_teams (list):
        List of codes for teams that are present in the matchup
    '''
    allocated_teams = []
    for matchup in matchups:
        allocated_teams.append(matchup[0])
        allocated_teams.append(matchup[1])
    return allocated_teams

def __allocate_matchups(matchups, roundno = 0):
    '''
    Allocates the matchups to different rounds so that games can be simulated in parallel, but one team won't be in multiple simulations in the same round.

    Paramters
    ---------
    matchups (list):
        List of length-4 tuples indicating each team, the venue, and a collection of all teams
    roundno (int):
        Round number to start labeling at

    Returns
    -------
    matchups_by_round (dict):
        A dictionary where the key is the round number and the values are a list of matchups allocated to that round
    '''
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

def generate_schedule(matrix_settings, teams):
    '''
    Generates a schedule to be used in the matrix analysis. Each round of the schedule will then be simulated in parallel until every team has played each other once.

    Parameters
    ----------
    matrix_settings (dict):
        Dictionary of settings for the matrix analysis
    teams (SportPredictifier.ObjectCollection):
        Collection of teams in the competition
        
    Returns
    -------
    matrix_schedule (pandas.DataFrame):
        Data frame with the schedule to be used in the matrix analysis
    '''
    print('Generating Matrix Schedule')
    team_list = __get_team_list(matrix_settings)
    matchups = __get_matchup_list(team_list, matrix_settings, teams)
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
    
    for roundno in matchups_by_round:
        for matchup in matchups_by_round[roundno]:
            matrix_schedule.loc[ix] = [roundno, 2023, 1, 1] + list(matchup) + [True]
            ix += 1

    return matrix_schedule

def write_matrix(matrix_settings, results, outfile):
    '''
    Writes the results of the matrix analysis to a CSV file where each cell value is the estimated chance of [row label] defeating [column label]

    Parameters
    ----------
    matrix_settings (dict):
        Dictionary of settings for the matrix analysis
    results (dict):
        Dictionary with the results of each simulated matchup
    outfile (str):
        Outfile to write matrix to
    '''
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