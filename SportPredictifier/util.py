import numpy as np

directions = ['F', 'A']

def compliment_direction(direction):
    if direction == 'F':
        return 'A'
    elif direction == 'A':
        return 'F'
    else:
        raise IOError('{} is an invalid direction. Must be "F" or "A"'.format(direction))

def cap_probability(p): #Maybe make enpoints configurable
    return np.minimum(
        np.maximum(
            p, 0),
        1)