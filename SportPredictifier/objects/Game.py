import threading
import pandas as pd
import numpy as np

from ..util import *
from ..simulate import simulate_game

class Game(threading.Thread):
    '''
    The `Game` object is used to simulate a game. An `ObjectCollection` of them are created in memory when the schedule table is loaded.
    Each game is assigned to it's own thread, and then the simulation of the games is multi-threaded. Expected scores are calculated upon
    initialization, and then each game is simulated `n_simulations` times, with a summary of the results being stored in `result_dict`.

    Parameters
    ----------
    result_dict (dict):
        Dictionary to store results in
    round_number (int):
        Round number of the game
    date (datetime.date):
        Date of game
    team1 (SportPredictifier.Team):
        Team #1 that is playing in the game
    team2 (SportPredictifier.Team):
        Team #2 that is playing in the game
    venue (SportPredictifier.Team):
        Venue of game
    knockout (bool):
        If set to `False`, a draw is possible
    n_simulations (int):
        Number of simulations to run when simulating the game
    '''

    def __init__(self, result_dict, round_number, date, team1, team2, venue, knockout, score_settings, n_simulations):
        
        threading.Thread.__init__(self)

        self.round_number = round_number
        self.date = date
        self.team1 = team1
        self.team2 = team2
        self.venue = venue
        self.score_settings = score_settings
        self.knockout = knockout
        self.result_dict = result_dict
        self.n_simulations = n_simulations
        
        # Initialize expected scores
        self.expected_scores = {
            team1.code: {},
            team2.code: {}
        }

        # Set oppponents for each team
        self.team1.opp = team2
        self.team2.opp = team1

        # Calculate expected scores
        self.__get_expected_scores()
        
    def __get_expected_scores(self):
        '''
        Calculates the expected scores for each team by adding each team's residual statistics to the opposition's typical performance.
        '''
        for score_type in self.score_settings:
            for team in [self.team1, self.team2]:

                # For probabilistic score types, calculate the probabilities of that score being successful
                if self.score_settings[score_type].prob:

                    # If the opposition has an effect on the score type, average the team's expected attack and the opposition's expected defense
                    if self.score_settings[score_type].opp_effect:
                        self.expected_scores[team.code][score_type] = np.average([team.stats['F']['RES_' + score_type] + team.opp.stats['A'][score_type],
                                                                                  team.opp.stats['A']['RES_' + score_type] + team.stats['F'][score_type]])
                    else:
                        self.expected_scores[team.code][score_type] = team.stats['F'][score_type]

                    # Set the probability at the allowed maximimum and minimum set in the score type table
                    self.expected_scores[team.code][score_type] = cap_probability(self.expected_scores[team.code][score_type])

                # For non-probabilistic score types, just calculate an expected value
                else:

                    # If the opposition has an effect on the score type, average the team's expected attack and the opposition's expected defense
                    if self.score_settings[score_type].opp_effect:
                        self.expected_scores[team.code][score_type] = (np.average([team.stats['F']['RES_' + score_type][0] + team.opp.stats['A'][score_type],
                                                                                   team.opp.stats['A']['RES_' + score_type][0] + team.stats['F'][score_type]]),
                                                                       0.25*(team.stats['F']['RES_' + score_type][1] + team.opp.stats['A']['RES_' + score_type][1])
                        )

                    # Set the probability at the allowed maximimum and minimum set in the score type table
                    else:
                        self.expected_scores[team.code][score_type] = (team.stats['F'][score_type][0], team.stats['F'][score_type][1])

    def run(self):
        '''
        Runs the simulation of the game
        '''
        print('Simulating game on {} in round {} between {} and {} at {}'.format(self.date.strftime('%D'),
                                                                                 self.round_number,
                                                                                 self.team1.name,
                                                                                 self.team2.name,
                                                                                 self.venue.name))
        print(self.expected_scores) # TODO: Possibly make this optional? Though I've always liked seeing it when running it

        # Update `result_dict` with the results of the simulation
        self.result_dict['{0}v{1}'.format(self.team1.code, self.team2.code)] = simulate_game(self.n_simulations, self.expected_scores, self.score_settings, self.venue, self.knockout)