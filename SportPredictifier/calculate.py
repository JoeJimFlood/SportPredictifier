import numpy as np

def spatial_weights(score_tables, teams, stadia):
    print("Calculating spatial weights")
    for team in score_tables:
        for stadium in stadia:
            def __get_stadium_specific_weight(location):
                return get_spatial_weight(stadia[location], teams[team].stadium, stadia[stadium])
            score_tables[team]['spatial_weight_{}'.format(stadium)] = score_tables[team]['VENUE'].apply(__get_stadium_specific_weight)

def stat(stats, team, direction, score_settings, score_type, score_tables, reference_location = None):

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

def team_stats(teams, score_settings, score_tables, game_locations = None):
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
                        stat(stats, opponent, direction, score_settings, score_type, score_tables, venue)
                        return stats[direction][score_type]
                    score_tables[team]['_'.join(['OPP', score_type, direction])] = score_tables[team]['OPP'].apply(__get_opponent_stat)
                else:
                    score_tables[team]['_'.join(['OPP', score_type, direction])] = score_tables[team]['OPP'].map(statmaps[direction][score_type])
                    
def residual_stats(teams, score_settings, score_tables):
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
    print("Calculating hype for each game")
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