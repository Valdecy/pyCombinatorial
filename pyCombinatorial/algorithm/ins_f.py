############################################################################
# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com

# Lesson: pyCombinatorial - Farthest Insertion
 
# GitHub Repository: <https://github.com/Valdecy> 

############################################################################

import copy
import numpy as np

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0]) - 1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k] - 1, city_tour[0][m] - 1]
    return distance

############################################################################

# Function: 2_opt
def local_search_2_opt(distance_matrix, city_tour, recursive_seeding = -1, verbose = True):
    if (recursive_seeding < 0):
        count = -2
    else:
        count = 0
    city_list = copy.deepcopy(city_tour)
    distance  = city_list[1] * 2
    iteration = 0
    while (count < recursive_seeding):
        if (verbose == True):
            print('Iteration = ', iteration, 'Distance = ', round(city_list[1], 2))
        best_route = copy.deepcopy(city_list)
        seed       = copy.deepcopy(city_list)
        for i in range(0, len(city_list[0]) - 2):
            for j in range(i + 1, len(city_list[0]) - 1):
                best_route[0][i:j + 1] = list(reversed(best_route[0][i:j + 1]))
                best_route[0][-1]      = best_route[0][0]
                best_route[1]          = distance_calc(distance_matrix, best_route)
                if (city_list[1] > best_route[1]):
                    city_list = copy.deepcopy(best_route)
                best_route = copy.deepcopy(seed)
        count     = count + 1
        iteration = iteration + 1
        if (distance > city_list[1] and recursive_seeding < 0):
            distance          = city_list[1]
            count             = -2
            recursive_seeding = -1
        elif (city_list[1] >= distance and recursive_seeding < 0):
            count             = -1
            recursive_seeding = -2
    return city_list[0], city_list[1]

############################################################################

# Function: Cheapest insertion Position 
def best_insertion(distance_matrix, temp):
    if len(temp) <= 2:
        return temp
    new_node    = temp[-1]
    base        = temp[:-1]
    base_closed = base + [base[0]]
    best_pos    = None
    best_delta  = float('+inf')
    for i in range(0, len(base)): 
        a = base_closed[i]
        b = base_closed[i + 1]
        delta = (distance_matrix[a, new_node] + distance_matrix[new_node, b] - distance_matrix[a, b])
        if delta < best_delta:
            best_delta = delta
            best_pos   = i + 1
    out = base[:]
    out.insert(best_pos, new_node)
    return out

############################################################################

# Function: Farthest Insertion
def farthest_insertion(distance_matrix, local_search = True, verbose = True):
    best_val         = float('+inf')
    best_route       = []
    n                = distance_matrix.shape[0]
    initial_location = -1
    for i1 in range(0, n):
        if (initial_location != -1):
            i1 = initial_location - 1
        dist    = np.copy(distance_matrix).astype(float)
        np.fill_diagonal(dist, float('-inf'))
        idx     = dist[i1, :].argmax()
        temp    = [i1, idx] 
        in_tour = set(temp)
        for _ in range(0, n - 2):
            remaining  = [u for u in range(0, n) if u not in in_tour]
            best_u     = None
            best_score = float('-inf')
            for u in remaining:
                score = min(distance_matrix[u, t] for t in temp)
                if score > best_score:
                    best_score = score
                    best_u     = u
            temp.append(best_u)
            in_tour.add(best_u)
            temp = best_insertion(distance_matrix, temp)
        route = temp + [temp[0]]
        route = [x + 1 for x in route]
        val   = distance_calc(distance_matrix, [route, 1])
        if local_search:
            seed         = [route, val]
            route2, val2 = local_search_2_opt(distance_matrix, seed, -1, False)
            route, val   = route2, val2
        if (val < best_val):
            best_val   = val
            best_route = [item for item in route]
        if (verbose == True):
            print('Node = ', i1 + 1, 'Distance = ', round(best_val, 2))
        if (initial_location != -1):
            break
    return best_route, best_val

############################################################################
