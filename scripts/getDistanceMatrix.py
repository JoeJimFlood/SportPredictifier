import pandas as pd
import numpy as np
from SportPredictifier.weighting.spatial import geodesic_distance
import sys
from subprocess import Popen

stadia_file = sys.argv[1]
outfile = sys.argv[2]
if len(sys.argv) > 3:
    units = sys.argv[3]
    assert units in ["mi", "km"], "Units must be km or mi"
    mult_map = {
        "mi": 12450,
        "km": 20037.5
    }
    unit_mult = mult_map[units]
else:
    unit_mult = 1

stadia = pd.read_csv(
    stadia_file
)

N = len(stadia)
matrix = pd.DataFrame(
    np.zeros(
        (N, N),
        float
    ),
    index = stadia["code"],
    columns = stadia["code"]
)

for oix, orow in stadia.iterrows():
    for dix, drow in stadia.iterrows():
        matrix.loc[orow["code"], drow["code"]] = unit_mult*geodesic_distance(
            orow["lat"],
            orow["lon"],
            drow["lat"],
            drow["lon"]
        )

matrix.to_csv(outfile)
Popen(outfile, shell = True)