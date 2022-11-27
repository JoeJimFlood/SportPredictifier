import pandas as pd

from objects import *

def table(object, fp):
    """
    Reads table from file
    """
    df = pd.read_csv(fp, index_col = 0)
    output = {}
    for row in df.index:
        output[row] = object(**df.loc[row])
    return output