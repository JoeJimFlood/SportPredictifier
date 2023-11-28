import pandas as pd
import numpy as np
import statsmodels.api as sm
import os
from scipy.special import expit, logit

infile = 'WinLogitData8+.csv'
data = pd.read_csv(infile).dropna()
data['LogOdds'] = logit(data['HomeChance'])
data['Intercept'] = np.ones_like(data.index)

print(data)

X = data[['LogOdds', 'Intercept']]
y = data['HomeWin']

reg = sm.Logit(y, X)
res = reg.fit()
print(res.summary())