import pandas as pd
import numpy as np

from objects import *

def weighted_variance(data, weights):
    assert len(data) == len(weights), 'Data and weights must be same length'
    weighted_average = np.average(data, weights = weights)
    v1 = weights.sum()
    v2 = np.square(weights).sum()
    return (weights*np.square(data - weighted_average)).sum() / (v1 - (v2/v1))