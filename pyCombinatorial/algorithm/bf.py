############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Brute Force
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import itertools

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

############################################################################

# Function: BF
def brute_force_analysis(distance_matrix):
    n          = distance_matrix.shape[1]
    candidates = []
    for p in itertools.permutations(range(2, n+1)):
        if (p <= p[::-1]):
            candidates.append(list(p))
    routes    = [ [1] + item + [1] for item in candidates ]
    distances = [ distance_calc(distance_matrix, [item, 1]) for item in routes ]
    idx       = distances.index(min(distances))
    route     = routes[idx]
    distance  = distances[idx]
    return route, distance

############################################################################
