import pandas as pd
import numpy as np
import os

out_df = pd.DataFrame(columns = [
    "Round",
    "Team",
    "Expected Score",
    "5%",
    "25%",
    "50%",
    "75%",
    "95%",
    "Actual Score",
])

c = 0
for r in range(4, 29):
    print('Extracting Round %d'%(r))
    fp = r'forecasts\ReportRound%d.xlsx'%(r)
    in_df = pd.read_excel(fp, "Forecasts", index_col = 0)

    for team in in_df:
        if team.startswith("Unnamed"):
            continue
        expected_score = in_df.loc["Expected Score", team]
        pct = {}
        for p in [5, 25, 50, 75, 95]:
            pct[p] = in_df.loc["%dth Percentile Score"%(p), team]
        out_df.loc[c] = [
            r,
            team,
            expected_score,
            pct[5],
            pct[25],
            pct[50],
            pct[75],
            pct[95],
            np.nan
        ]

        c += 1

print('Writing')
out_df.to_csv(r'Validation\ValidationDataRaw.csv', index = False)
print('Done')