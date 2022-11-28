import pandas as pd

from .objects import *

def __int2hex(n):
    n = hex(n)
    return (4-len(n))*'0' + n[2:]

def __combine_colors(df, r, g, b, out_field, cleanup = True):
    """
    Combines rgb coordinates into a single hex

    Parameters
    ----------

    """
    df[out_field] = '#' + df[r].apply(__int2hex) + df[g].apply(__int2hex) + df[b].apply(__int2hex)
    if cleanup:
        del df[r]
        del df[g]
        del df[b]

def __load_table(object, df):
    """
    Reads table from data frame
    """
    output = {}
    df.index = df["code"]
    for row in df.index:
        output[row] = object(**df.loc[row])
    return output

def stadia(fp):
    stadium_table = pd.read_csv(fp)
    return __load_table(Stadium, stadium_table)

def teams(fp, stadia):
    team_table = pd.read_csv(fp)
    __combine_colors(team_table, 'r1', 'g1', 'b1', 'color1')
    __combine_colors(team_table, 'r2', 'g2', 'b2', 'color2')
    team_table['stadium'] = team_table['stadium'].map(stadia)
    
    return __load_table(Team, team_table)