############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Bitonic Tour
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy as np

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

# Function: 2_opt
def local_search_2_opt(distance_matrix, city_tour, recursive_seeding = -1, verbose = True):
    if (recursive_seeding < 0):
        count = -2
    else:
        count = 0
    city_list = copy.deepcopy(city_tour)
    distance  = city_list[1]*2
    iteration = 0
    while (count < recursive_seeding):
        if (verbose == True):
            print('Iteration = ', iteration, 'Distance = ', round(city_list[1], 2))  
        best_route = copy.deepcopy(city_list)
        seed       = copy.deepcopy(city_list)        
        for i in range(0, len(city_list[0]) - 2):
            for j in range(i+1, len(city_list[0]) - 1):
                best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
                best_route[0][-1]    = best_route[0][0]     
                best_route[1]        = distance_calc(distance_matrix, best_route)                    
                if (city_list[1] > best_route[1]):
                    city_list = copy.deepcopy(best_route)         
                best_route = copy.deepcopy(seed)
        count     = count + 1
        iteration = iteration + 1  
        if (distance > city_list[1] and recursive_seeding < 0):
             distance          = city_list[1]
             count             = -2
             recursive_seeding = -1
        elif(city_list[1] >= distance and recursive_seeding < 0):
            count              = -1
            recursive_seeding  = -2
    return city_list[0], city_list[1]

############################################################################

# Function: Bitonic Tour
def bitonic_tour(coordinates, distance_matrix, local_search = True, verbose = True):
    sorted_indices = np.argsort(coordinates[:, 0])           
    coords_sorted  = coordinates[sorted_indices]
    dist_sorted    = distance_matrix[sorted_indices][:, sorted_indices]
    n              = len(coords_sorted)
    if (n <= 1):
        return 0.0, sorted_indices.tolist()
    elif (n == 2):
        return dist_sorted[0, 1] + dist_sorted[1, 0], sorted_indices.tolist()
    dp           = np.full((n, n), np.inf)
    parent       = [[None] * n for _ in range(0, n)] 
    dp[0, 1]     = dist_sorted[0, 1]
    parent[0][1] = None
    for j in range(2, n):
        for i in range(0, j):
            if (i == 0):
                dp[0, j]     = dp[0, j - 1] + dist_sorted[j - 1, j]
                parent[0][j] = (0, j - 1)
            else:
                best_val = np.inf
                best_k   = None
                for k in range(0, i):
                    candidate = dp[k, i] + dist_sorted[k, j]
                    if (candidate < best_val):
                        best_val = candidate
                        best_k   = k
                dp[i, j]     = best_val
                parent[i][j] = (best_k, i)
    distance      = dp[0, n - 1] + dist_sorted[0, n - 1]
    route_indices = [n - 1]
    i, j          = 0, n - 1
    while (True):
        if (verbose == True):
            print('Node = ', j+1)
        pval = parent[i][j]
        if (pval is None):
            route_indices.append(i)
            break
        route_indices.append(pval[1])
        i, j = pval
    route_indices.reverse()
    route    = sorted_indices[route_indices].tolist()
    route    = [item + 1 for item in route]
    route.append(route[0])
    distance = distance_calc(distance_matrix, [route, 1])
    seed     = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################

