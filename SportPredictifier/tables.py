import orca
import pandas as pd
import os

def __int2hex(n):
    n = hex(n)
    return (4-len(n))*'0' + n[2:]

def __combine_colours(df, r, g, b, out_field, cleanup = True):
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

@orca.table
def teams(teams_table_file):
    teams = pd.read_csv(teams_table_file)
    
    #Combine team colors into hex codes
    for i in range(1, 3):
        teams_table['color%d'%(i)] = teams_table[['r%d'%(i), 'g%d'%(i), 'b%d'%(i)]].apply(__combine_colours)

    return teams_table

@orca.table
def stadia(stadia_table_file):
    return pd.read_csv(stadia_table_file)

@orca.table
def score_settings(score_settings_table):
    return pd.read_csv(score_settings_table)

@orca.injectable
def score_tables(score_table_directory):
    tables = {}
    for f in os.listdir(score_table_directory):
        tables[f[:-4]] = pd.read_csv(os.path.join(score_table_directory, f + '.csv'))