import pandas as pd
import numpy as np
import os

base_path = os.path.dirname(__file__)
scoring = pd.read_csv(os.path.join(base_path, 'scoring.csv'))

n_sim = 10000

expected_scores = {
    'TD_1': 2.5,
    'OTTD_1': 0.1,
    'FG_1': 1.5,
    'S_1': 0.1,
    'GOFOR2_1': 0.15,
    'PAT1_1': 0.95,
    'PAT2_1': 0.5,
    'D2PC_1': 0.05,
    'TD_2': 1.5,
    'OTTD_2': 0.5,
    'FG_2': 2,
    'S_2': 0.1,
    'GOFOR2_2': 0.15,
    'PAT1_2': 0.95,
    'PAT2_2': 0.5,
    'D2PC_2': 0.05,
}

results = pd.DataFrame(index = range(n_sim))
scores_1 = pd.DataFrame(index = range(n_sim))
scores_2 = scores_1.copy()

for index, row in scoring.iterrows():
    for teamno in [1, 2]:
        key = '{0}_{1}'.format(row['score_type'], teamno)
        if row['type'] == 'num':
            results[key] = np.random.poisson(expected_scores[key], n_sim)
        elif row['type'] == 'prob':
            condition = row['condition'].replace('{F}', str(teamno)).replace('{A}', str(3-teamno))
            results[key] = np.random.binomial(results.eval(condition), expected_scores[key])
        else:
            raise KeyError("Invalid type")

    scores_1[row['score_type']] = results['{}_1'.format(row['score_type'])]
    scores_2[row['score_type']] = results['{}_2'.format(row['score_type'])]

scores_1 = scores_1.dot(scoring['points'].values)
scores_2 = scores_2.dot(scoring['points'].values)

win1 = scores_1 > scores_2
win2 = scores_1 < scores_2
draw = scores_1 == scores_2


print('Go')