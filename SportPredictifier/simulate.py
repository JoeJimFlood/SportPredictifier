import pandas as pd
import numpy as np
from numpy.random import poisson, binomial, negative_binomial
from pandas._libs.tslibs import timestamps

def __sim_poisson(mean, n_sim):
    '''
    Simulates from a Poisson distribution when the mean is equal to the variance

    Parameters
    ----------
    mean (float):
        Mean of the Poisson distribution to sample from
    n_sim (int):
        Number of simulations to run

    Returns
    -------
    simulation_results (array of floats):
        An array of length-`n_sim` with results of each simulation
    '''
    return poisson(mean, n_sim)

def __sim_negative_binomial(mean, var, n_sim):
    '''
    Simulates from a negative binomial distribution when the mean is less than the variance

    Parameters
    ----------
    mean (float):
        Mean of the negative binomial distribution to sample from
    var (float):
        Variance of the negative binomial distribution to sample from
    n_sim (int):
        Number of simulations to run

    Returns
    -------
    simulation_results (array of floats):
        An array of length-`n_sim` with results of each simulation
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
    Simulates from a binomial distribution when the mean is greater than the variance

    Parameters
    ----------
    mean (float):
        Mean of the binomial distribution to sample from
    var (float):
        Variance of the binomial distribution to sample from
    n_sim (int):
        Number of simulations to run

    Returns
    -------
    simulation_results (array of floats):
        An array of length-`n_sim` with results of each simulation
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
    '''
    Runs the simulation. The Poisson, binomial, or negative binomial distributions will be used depending on the values of the mean and the variance.

    Parameters
    ----------
    mean (float):
        Mean of the distribution to be sampled from
    var (float):
        Variance of the distribution to be sampled from
    n_sim (int):
        Number of simulations to run

    Returns
    -------
    simulation_results (array of floats):
        An array of length-`n_sim` with results of each simulation
    '''
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
    Creates empty data frame before simulation to put scores into

    Parameters
    ----------
    n_simulations (int):
        Number of simulations to run
    teams (SportPredictifier.ObjectCollection):
        Collection of teams competing int the competition
    score_settings (SportPredictifier.ObjectCollection):
        Collection of score settings for the competition

    Returns
    -------
    score_matrix (pandas.DataFrame):
        Empty data frame to put results of simulations in
    '''
    columns = []
    for team in teams:
        for score_type in score_settings:
            columns.append('{0}_{1}'.format(score_type, team))
    return pd.DataFrame(np.empty((n_simulations, 2*len(score_settings)), np.ushort), columns = columns)

def __calculate_score(scores, score_array):
    '''
    Takes the number of scores of each time for a simulation and calculates the final score of each individual simulation using a matrix product

    Parameters
    ----------
    scores (pandas.DataFrame):
        2D-array with the number of scores for each score type
    score_array (pandas.Series):
        Series with the point value for each score type

    Returns
    -------
    final_scores (numpy.array):
        1D-array with the point values for each simulated game
    '''
    return scores.values.dot(score_array.values)

def __eval_results(scores, knockout = False):
    '''
    Evaluates the results of the games based on the simulated scores, returning the number of wins for each teams (as well as draws if applicable)

    Parameters
    ----------
    scores (pandas.DataFrame):
        Data frame containing the scores for each team in every simulation (the teams are the columns)
    knockout (bool):
        Flag indicating if there has to be a winner for the game. If `True`, each team will be given a half win in the case of a draw

    Returns
    -------
    team_1_wins (numpy.array):
        Array with the games that were won by team 1
    team_2_wins (numpy.array):
        Array with the games that were won by team 2
    draws (numpyarray):
        Array with the games that ended in a draw
    '''
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

#def eval_try_bonus(team_1_tries, team_2_tries, req_diff):
#    team_1_bp = (team_1_tries - team_2_tries >= req_diff).astype(int)
#    team_2_bp = (team_2_tries - team_1_tries >= req_diff).astype(int)
#    return team_1_bp, team_2_bp

#def eval_losing_bonus(team_1_score, team_2_score, req_diff):
#    diff = team_1_score - team_2_score
#    team_1_bp = ((diff < 0)*(diff >= -req_diff)).astype(int)
#    team_2_bp = ((diff > 0)*(diff <= req_diff)).astype(int)
#    return team_1_bp, team_2_bp

def simulate_game(n_simulations, expected_scores, score_settings, venue, knockout, return_scores):
    '''
    Simulates a game based on the input `expected_scores` among other settings

    Parameters
    ----------
    n_simulations (int):
        Number of simulations to run
    expected_scores (dict):
        Dictionary with the expected number of scores of each type for each team
    score_settings (SportPredictifier.ObjectCollection):
        Collection of score settings for the competition
    venue (SportPredictifier.stadium):
        Venue of game being simulated
    knockout (bool):
        Flag indicating if there has to be a winner for the game. If `True`, each team will be given a half win in the case of a draw
    return_scores (bool):
        Flag indicating if all of the scores from the simulations should be returned

    Returns
    -------
    results (dict):
        Dictionary containing the chances of each team winning along with the distribution of final scores
    '''
    scores = pd.DataFrame(np.empty((n_simulations, 2),
                                   dtype = np.uint8),
                          columns = expected_scores.keys())
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

    if return_scores:
        for team in scores:
            score_matrix['SCORE_' + team] = scores[team]
        score_matrix.index.name = 'SIMULATION'
        results['scores'] = score_matrix

    return results