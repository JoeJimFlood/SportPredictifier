import threading
import pandas as pd
import numpy as np

from ..util import *
from ..simulate import simulate_game

N_SIMULATIONS = 5000000 #TODO: Add to settings

class Game(threading.Thread):

    def __init__(self, result_dict, round_number, date, team1, team2, venue, knockout, score_settings):
        '''
        Game object!

        Parameters
        ----------
        date (datetime.date):
            Date of game
        team1 (SportPredictifier.Team):
            Team #1 that is playing in the game
        team2 (SportPredictifier.Team):
            Team #2 that is playing in the game
        venue (SportPredictifier.Team):
            Venue of game
        '''
        threading.Thread.__init__(self)

        self.round_number = round_number
        self.date = date
        self.team1 = team1
        self.team2 = team2
        self.venue = venue
        self.score_settings = score_settings
        self.knockout = knockout
        self.expected_scores = {team1.code: {},
                                team2.code: {}
        }
        self.result_dict = result_dict

        #Set oppponents for each team
        self.team1.opp = team2
        self.team2.opp = team1

        self.__get_expected_scores()
        
    def __get_expected_scores(self):
        for score_type in self.score_settings:
            for team in [self.team1, self.team2]:
                if self.score_settings[score_type].prob:
                    if self.score_settings[score_type].opp_effect:
                        self.expected_scores[team.code][score_type] = np.average([team.stats['F']['RES_' + score_type] + team.opp.stats['A'][score_type],
                                                                                  team.opp.stats['A']['RES_' + score_type] + team.stats['F'][score_type]])
                    else:
                        self.expected_scores[team.code][score_type] = team.stats['F'][score_type]

                    self.expected_scores[team.code][score_type] = cap_probability(self.expected_scores[team.code][score_type])

                else:
                    if self.score_settings[score_type].opp_effect:
                        self.expected_scores[team.code][score_type] = (np.average([team.stats['F']['RES_' + score_type][0] + team.opp.stats['A'][score_type],
                                                                                   team.opp.stats['A']['RES_' + score_type][0] + team.stats['F'][score_type]]),
                                                                       0.25*(team.stats['F']['RES_' + score_type][1] + team.opp.stats['A']['RES_' + score_type][1])
                        )
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

        self.result_dict['{0}v{1}'.format(self.team1.code, self.team2.code)] = simulate_game(N_SIMULATIONS, self.expected_scores, self.score_settings, self.venue, self.knockout)
        #print(results)