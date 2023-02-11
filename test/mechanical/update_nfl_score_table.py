import pandas as pd
import os
import numpy as np

base_path = os.path.dirname(__file__)
score_table_path = os.path.join(base_path, 'ScoreTables')

recode_dict = {'TDF': 'TD_F',
               'FGF': 'FG_F',
               'SFF': 'S_F',
               'TDA': 'TD_A',
               'FGA': 'FG_A',
               'SFA': 'S_A',
               'PAT1FS': 'PAT1_F',
               'PAT2FS': 'PAT2_F',
               'PAT1AS': 'PAT1_A',
               'PAT2AS': 'PAT2_A',
               'PAT2FA': 'GOFOR2_F',
               'PAT2AA': 'GOFOR2_A',
               'D2CF': 'D2PC_F',
               'D2CA': 'D2PC_A'}

for f in os.listdir(score_table_path):
    fp = os.path.join(score_table_path, f)
    print(fp)
    df = pd.read_csv(fp)
    df = df.rename(columns = recode_dict)
    df['weight'] = np.ones_like(df.index)
    df.to_csv(fp)
print('Done')