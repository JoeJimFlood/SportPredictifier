import numpy as np
from scipy.stats import entropy

from .util import *
from .weighting.spatial import get_spatial_weight

global compliment_direction

def weighted_variance(data, weights):
    '''
    Computes a weighted variance of data.

    Parameters
    ----------
    data (array-like):
        Data to compute variance of
    weights (array-like):
        Weights to use when computing variance

    Returns
    -------
    weighted_variance (float):
        Weighted variance of `data`
    '''
    assert len(data) == len(weights), 'Data and weights must be same length'
    weighted_average = np.average(data, weights = weights)
    v1 = weights.sum()
    v2 = np.square(weights).sum()
    return (weights*np.square(data - weighted_average)).sum() / (v1 - (v2/v1))

def spatial_weights(score_tables, teams, stadia):
    '''
    Calculates sptial weights to be used in score tables for calculation. For each score table stored in memory, a spatial weight field is
    added in place for each stadium used in the competition.

    Parameters
    ----------
    score_tables (SportPredictifier.ObjectCollection):
        Collection of score tables for every team in the competition
    teams (SportPredictifier.ObjectCollection):
        Collection of teams playing in the competition
    stadia (SportPredictifier.ObjectCollection):
        Collection of teams competing in the competition
    '''
    print("Calculating spatial weights")
    for team in score_tables:
        for stadium in stadia:
            def __get_stadium_specific_weight(location):
                return get_spatial_weight(stadia[location], teams[team].stadium, stadia[stadium])
            score_tables[team]['spatial_weight_{}'.format(stadium)] = score_tables[team]['VENUE'].apply(__get_stadium_specific_weight)

def stat(stats, team, direction, score_settings, score_type, score_tables, reference_location = None):
    '''
    Calculates a stat for a specific score type for each team. A dictionary called `stats` is updated in place.

    Parameters
    ----------
    stats (dict):
        Dictionary to keep track of stats for each team
    team (str):
        Code of the team to calculate the stat of
    direction (str):
        Equal to "F" if for and "A" if against
    score_settings (SportPredictifier.ObjectCollection):
        Score settings for the competition
    score_type (str):
        Score type to calculate the stat of
    score_tables (SportPredictifier.ObjectCollection):
        Collection of score tables for each team
    reference_location (str):
        Code of stadium to be used as reference location for calculating spatial weights
    '''
    # Apply spatial weights if a reference location is given, otherwise use default weights
    if reference_location is not None:
        weights = score_tables[team]['spatial_weight_{}'.format(reference_location)]
    else:
        weights = score_tables[team]['weight']

    # For probabilistic score types, divide the number of scores by its condition
    if score_settings[score_type].prob:
        condition = score_settings[score_type].condition.replace('{F}', direction).replace('{A}', compliment_direction(direction))
        if score_tables[team].eval(condition).sum() == 0: # If the condition hasn't been met, use the base probability
            stats[direction][score_type] = score_settings[score_type].base
        else:
            stats[direction][score_type] = (score_tables[team][score_type + '_' + direction]*weights).sum() / (score_tables[team].eval(condition)*weights).sum()
                        
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

def team_stats(teams, score_settings, score_tables, game_locations = None):
    '''
    Calculates the statistics for each team in the competition. These are updated as a dictionary that is an attribute of the `Team` object.

    Parameters
    ----------
    teams (SportPredictifier.ObjectCollection):
        Collection of teams competing in the competition
    score_settings (SportPredictifier.ObjectCollection):
        Collection of score settings used in the competition
    score_tables (SportPredictifier.ObjectCollection):
        Collection of score tables from the comptision
    game_locations (dict, optional):
        Dictionary that says which statium each team is playing in for the round
    '''
    print("Calculating team statistics")
    assert all(team in score_tables for team in teams), "All teams must have a score table"
    for team in teams:

        stats = {}
        for direction in directions:
            stats[direction] = {}
            for score_type in score_settings:
                if game_locations is not None and team in game_locations: # Team is not playing if latter is False
                    stat(stats, team, direction, score_settings, score_type, score_tables, game_locations[team])
                else:
                    stat(stats, team, direction, score_settings, score_type, score_tables)
 
        teams[team].stats = stats

def opponent_stats(teams, score_settings, score_tables, use_spatial_weights = False):
    '''
    Obtains the stats for each opponent of each team and adds them in place to the score tables in the rounds in which they played against them

    Parameters
    ----------
    teams (SportPredictifier.ObjectCollection):
        Collection of teams competing in the competition
    score_settings (SportPredictifier.ObjectCollection):
        Collection of score settings used in the competition
    score_tables (SportPredictifier.ObjectCollection):
        Collection of score tables from the comptision
    use_spatial_weights (bool):
        If set to `True`, spatial weights will be used when calculating opponent statistics
    '''
    print("Calculating opponent statistics")

    # Creating maps to easily map a team's code to their statistics
    statmaps = {}
    for direction in directions:
        statmaps[direction] = {}
        for score_type in score_settings:
            statmaps[direction][score_type] = {}
            for team in teams:
                statmaps[direction][score_type][team] = teams[team].stats[direction][score_type]

    # For each score type, map the opponent's average scores (in the opposing direction) to 
    for team in score_tables:
        for direction in directions:
            for score_type in score_settings:
                if use_spatial_weights:
                    def __get_opponent_stat(opponent):
                        stats = {direction: {}}
                        venue = score_tables[team].query('OPP == @opponent').iloc[0]['VENUE']
                        stat(stats, opponent, direction, score_settings, score_type, score_tables, venue)
                        return stats[direction][score_type]
                    score_tables[team]['_'.join(['OPP', score_type, direction])] = score_tables[team]['OPP'].apply(__get_opponent_stat)
                else:
                    score_tables[team]['_'.join(['OPP', score_type, direction])] = score_tables[team]['OPP'].map(statmaps[direction][score_type])
                    
def residual_stats(teams, score_settings, score_tables):
    '''
    Calculates residual statistics (how each team does relative to their opponents' typical performances).
    These are updated as part of an attribute of the `Team` object.

    Parameters
    ----------
    teams (SportPredictifier.ObjectCollection):
        Collection of teams competing in the competition
    score_settings (SportPredictifier.ObjectCollection):
        Collection of score settings used in the competition
    score_tables (SportPredictifier.ObjectCollection):
        Collection of score tables from the comptision
    '''
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

def hype(season_settings, results, round_number):
    '''
    Calculates the hype of each game, which is a combination of the quality of each team and the uncertainty of the result of the game

    Parameters
    ----------
    season_settings (dict):
        Dictionary of settings for the competition
    results (dict):
        Dictionary of results. This will be edited in place
    round_number (int):
        Round number of the game
    '''
    print("Calculating hype for each game")

    # Read in rankings
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