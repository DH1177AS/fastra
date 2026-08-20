EPSILON_LENGTH   = 1e-6
EPSILON_AREA     = 1e-6
EPSILON_VOLUME   = 1e-9
EPSILON_ANGLE    = 1e-9
EPSILON_CURRENCY = 0.5
EPSILON_DEFAULT  = 1e-6

def approximately_equal(a, b, epsilon=EPSILON_DEFAULT):
    return abs(a - b) <= epsilon

def approximately_greater(a, b, epsilon=EPSILON_DEFAULT):
    return a > b - epsilon

def approximately_less(a, b, epsilon=EPSILON_DEFAULT):
    return a < b + epsilon
