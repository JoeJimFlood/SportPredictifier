'''
SCRIPT UNDER CONSTRUCTION
'''
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from numpy.polynomial import Polynomial

class TemporalWeightingFunction:

    def __init__(self, coefs):
        self.coefs = np.array(coefs)

    def eval(self, x):
        return np.exp(Polynomial(np.hstack((0, -np.maximum(0, self.coefs))))(x))

    def __call__(self, x):
        self.eval(x)

def __apply_temporal_function_to_score_table(score_table, weighting_function):
    score_table['weight'] *= score_table['DaysSince'].apply(weighting_function)

def __get_days_since(score_table, reference_date):
    score_table['DaysSince'] = reference_date - pd.to_datetime(score_table[['YEAR', 'MONTH', 'DAY']])

def __get_reference_dates(schedule, teams, settings, roundno):
    round_games = schedule.query('{0} == {1}'.format(settings['round_name'].upper(), roundno))
    round_games['date'] = pd.to_datetime(round_games[['year', 'month', 'day']])
    
    reference_dates = {}
    for team in teams:
        for ix, row in round_games.iterrows():
            if row['team1'] == team or row['team2'] == team:
                reference_dates[team] = row['date']
                break
            break