import pandas as pd
import numpy as np
import os
from scipy.stats.distributions import norm

def rank(score_table_path, ranking_filepath, score_settings):

    pf = {}
    pa = {}

    score_array = score_settings.extract_attribute('points')
    score_types_f = []
    score_types_a = []
    for score_type in score_settings:
        score_types_f.append(score_type + '_F')
        score_types_a.append(score_type + '_A')

    for team in os.listdir(score_table_path):
        data = pd.read_csv(os.path.join(score_table_path, team))
        pf[team[:-4]] = np.dot(data[score_types_f], score_array).mean()
        pa[team[:-4]] = np.dot(data[score_types_a], score_array).mean()

    results = pd.DataFrame(index = pf.keys(), columns = ['Attack', 'Defense', 'Overall'])

    for team in os.listdir(score_table_path):
        data = pd.read_csv(os.path.join(score_table_path, team))
        data['For'] = np.dot(data[score_types_f], score_array)
        data['Against'] = np.dot(data[score_types_a], score_array)
        data['OppFor'] = data['OPP'].map(pf)
        data['OppAgainst'] = data['OPP'].map(pa)
        data['Attack'] = data['For'] - data['OppAgainst']
        data['Defense'] = data['Against'] - data['OppFor']
        data['Overall'] = data['Attack'] - data['Defense']
    
        results.loc[team[:-4]] = data[results.columns].mean()

    results['Standardised'] = (results['Overall'] - results['Overall'].mean())/results['Overall'].std()
    
    results['Quantile'] = norm.cdf(results['Standardised'].astype(float))
    
    results.sort_values('Overall', ascending = False).to_csv(ranking_filepath)
    return results