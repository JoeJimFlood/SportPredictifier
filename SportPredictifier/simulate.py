import pandas as pd
from pandas._libs.tslibs import timestamps
import numpy as np

'''
Utility functions for SportPredictifier Simulation
'''
import numpy as np
from numpy.random import poisson, binomial, negative_binomial

def __sim_poisson(mean, n_sim):
    '''
    Simulates Poisson for when mean is equal to variance
    '''
    return poisson(mean, n_sim)

def __sim_negative_binomial(mean, var, n_sim):
    '''
    Simulates negative binomial for when mean is less than variance
    '''
    p = mean / var
    n = mean * p / (1-p)
    try:
        return negative_binomial(n, p, n_sim)
    except ValueError:
        print(mean, var)
        print(n, p)
        raise Exception

def __sim_binomial(mean, var, n_sim):
    '''
    Simulates binomial for when mean is greater than variance
    '''
    p = 1 - (var/mean)
    n = (mean / p)
    floor_n = int(n)
    high_prob = n - floor_n
    ns = floor_n + binomial(1, high_prob, n_sim)
    try:
        return binomial(ns, p)
    except ValueError:
        print(mean, var, p)

def __sim(mean, var, n_sim):
    #Check if there's a negative mean or variance. If so, set one to the other so a Poisson distribution can be used.
    if mean < 0:
        mean = var
    if var < 0:
        var = mean

    if mean > var:
        return __sim_binomial(mean, var, n_sim)
    elif mean < var:
        return __sim_negative_binomial(mean, var, n_sim)
    else:
        return __sim_poisson(mean, n_sim)

def __initialize_score_matrix(n_simulations, teams, score_settings):
    '''
    Creates empty data frame to put scores in
    '''
    columns = []
    for team in teams:
        for score_type in score_settings:
            columns.append('{0}_{1}'.format(score_type, team))
    return pd.DataFrame(np.empty((n_simulations, 2*len(score_settings)), np.ushort), columns = columns)


#############################################################################################################################
def __calculate_score(scores, score_array):
    #assert len(scores) == len(score_array), 'Score array and scores must have same length'
    #score_array = np.array(score_array)
    return scores.values.dot(score_array.values)

def __eval_results(scores, knockout = False):
    team1 = scores.columns[0]
    team2 = scores.columns[1]
    team1_wins = (scores[team1] > scores[team2]).astype(float)
    team2_wins = (scores[team1] < scores[team2]).astype(float)
    draws = (scores[team1] == scores[team2]).astype(float)
    if knockout:
        team1_wins += (0.5*draws)
        team2_wins += (0.5*draws)
        draws = np.zeros_like(team1_wins)
        return team1_wins, team2_wins, draws
    else:
        return team1_wins, team2_wins, draws

#def eval_try_bonus(team_1_tries, team_2_tries, req_diff):
#    team_1_bp = (team_1_tries - team_2_tries >= req_diff).astype(int)
#    team_2_bp = (team_2_tries - team_1_tries >= req_diff).astype(int)
#    return team_1_bp, team_2_bp

#def eval_losing_bonus(team_1_score, team_2_score, req_diff):
#    diff = team_1_score - team_2_score
#    team_1_bp = ((diff < 0)*(diff >= -req_diff)).astype(int)
#    team_2_bp = ((diff > 0)*(diff <= req_diff)).astype(int)
#    return team_1_bp, team_2_bp

def simulate_game(n_simulations, expected_scores, score_settings, venue, knockout):
    '''
    Simulate a game
    '''
    scores = pd.DataFrame(np.empty((n_simulations, 2)),
                          columns = expected_scores.keys())
    #for team in expected_scores:
    score_matrix = __initialize_score_matrix(n_simulations,
                                                expected_scores.keys(),
                                                score_settings)
    for score_type in score_settings:
        if score_settings[score_type].prob:
            for team in expected_scores:
                teams = list(expected_scores.keys())
                teams.remove(team)
                opp = teams[0]
                condition = score_settings[score_type].condition.replace('{F}', team).replace('{A}', opp)
                score_matrix['{0}_{1}'.format(score_type, team)] = np.random.binomial(score_matrix.eval(condition),
                                                                                      expected_scores[team][score_type])
        else:
            for team in expected_scores:
                score_matrix['{0}_{1}'.format(score_type, team)] = __sim(expected_scores[team][score_type][0],
                                                                         expected_scores[team][score_type][1],
                                                                         n_simulations)

    scores = pd.DataFrame(np.empty((n_simulations, 2)), columns = expected_scores.keys())
    for team in expected_scores:
        team_columns = []
        for col in score_matrix.columns:
            if team in col:
                team_columns.append(col)
        scores[team] = __calculate_score(score_matrix[team_columns],
                                         score_settings.extract_attribute('points'))

    (team1_wins, team2_wins, draws) = __eval_results(scores)

    if knockout:
        team1_wins += 0.5*draws
        team2_wins += 0.5*draws

    results = {}
    results['venue'] = venue
    results['chances'] = {scores.columns[0]: team1_wins.mean(),
                          scores.columns[1]: team2_wins.mean()}

    percentiles = np.arange(0.05, 1, 0.05)
    results['score_distributions'] = scores.describe(percentiles)

    return results