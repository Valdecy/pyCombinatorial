############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Bellman-Held-Karp Exact Algorithm
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import itertools

############################################################################

# Function: Bellman-Held-Karp Exact Algorithm  (adapted from https://github.com/CarlEkerot/held-karp)
def bellman_held_karp_exact_algorithm(distance_matrix, verbose = True):
    n = distance_matrix.shape[0]
    C = {}
    for k in range(1, n):
        C[(2**k, k)] = (distance_matrix[0, k], 0)
    for j in range(2, n):
        combinations = list(itertools.combinations(range(1, n), j))
        for i in combinations:
            bits = 0
            for bit in i:
                bits = bits + 2**bit
            for k in i:
                prev = bits - 2**k
                res = []
                for m in i:
                    if( m == 0 or m == k):
                        continue
                    res.append((C[(prev, m)][0] + distance_matrix[m, k], m))
                C[(bits, k)] = min(res)
        if (verbose == True):
            print('Iteration: ', j, ' of ', n-1, ' Analysed Combinations: ', len(combinations))
    bits = (2**n - 1) - 1
    res  = []
    for k in range(1, n):
        res.append((C[(bits, k)][0] + distance_matrix[k, 0], k))
    distance, parent = min(res)
    route            = []
    for i in range(n - 1):
        route.append(parent)
        bits_     = bits - 2**parent
        _, parent = C[(bits, parent)]
        bits      = bits_
    route = [0] + route + [0]
    route = [item + 1 for item in route]
    return route, distance

############################################################################
