directions = ['F', 'A']

def compliment_direction(direction):
    if direction == 'F':
        return 'A'
    elif direction == 'A':
        return 'F'
    else:
        raise IOError('{} is an invalid direction. Must be "F" or "A"'.format(direction))