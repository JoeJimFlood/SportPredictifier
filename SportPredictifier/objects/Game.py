import threading
import pandas as pd
import numpy as np

N_SIMULATIONS = 5000000

class Game(threading.Thread):

    def __init__(self, round_number, date, team1, team2, venue, score_settings):
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
        self.expected_scores = {team1.code: {},
                                team2.code: {}
        }

        #Set oppponents for each team
        self.team1.opp = team2
        self.team2.opp = team1

        self.__get_expected_scores()
        
    def __get_expected_scores(self):
        for score_type in self.score_settings:
            for team in [self.team1, self.team2]:
                if self.score_settings[score_type].opp_effect:       
                    self.expected_scores[team.code] = np.average([team.stats['F']['RES_' + score_type] + team.opp.stats['A'][score_type],
                                                                  team.stats['A']['RES_' + score_type] + team.opp.stats['F'][score_type]])
                else:
                    self.expected_scores[team.code] = team.stats['F'][score_type]

    def run(self):
        '''
        Runs the simulation of the game
        '''
        print('Simulating game on {} in round {} between {} and {} at {}'.format(self.date.strftime('%D'),
                                                                                 self.round_number,
                                                                                 self.team1.name,
                                                                                 self.team2.name,
                                                                                 self.venue.name))
        #team_1_results = pd.DataFrame(
        #    np.zeros(
        #        (N_SIMULATIONS, len(self.score_settings))
        #    ),
        #    columns = self.score_settings.keys()
        #)
        #team_2_results = team_1_results.copy()

        #for score_type in self.score_types:
        #    if self.score_types[score_type].prob:
        #        pass
        #    else:
        #        pass        