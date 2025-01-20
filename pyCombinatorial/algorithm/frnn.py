############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: FRNN (Fixed Radius Near Neighbor)
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy as np
import random

from scipy.spatial import KDTree

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

############################################################################

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

# Function: Possible Segments
def segments_3_opt(n):
    x       = []
    a, b, c = 0, 0, 0
    for i in range(0, n):
        a = i
        for j in range(i + 1, n):
            b = j
            for k in range(j + 1, n + (i > 0)):
                c = k
                x.append((a, b, c))    
    return x

############################################################################

# Function: 3_opt
def local_search_3_opt(distance_matrix, city_tour, recursive_seeding = -1, verbose = True):
    if (recursive_seeding < 0):
        count = recursive_seeding - 1
    else:
        count = 0
    city_list     = [city_tour[0][:-1], city_tour[1]]
    city_list_old = city_list[1]*2
    iteration     = 0
    while (count < recursive_seeding):
        if (verbose == True):
            print('Iteration = ', iteration, 'Distance = ', round(city_list[1], 2))  
        best_route   = copy.deepcopy(city_list)
        best_route_1 = [[], 1]
        seed         = copy.deepcopy(city_list)     
        x            = segments_3_opt(len(city_list[0]))
        for item in x:
            i, j, k = item   
            A       = best_route[0][:i+1] + best_route[0][i+1:j+1]
            a       = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1]))
            B       = best_route[0][j+1:k+1]
            b       = list(reversed(B))
            C       = best_route[0][k+1:]
            c       = list(reversed(C))
            trial   = [ 
                        [a + B + C], 
                        [A + b + C], 
                        [A + B + c],
                        [A + b + c], 
                        [a + b + C], 
                        [a + B + c], 
                        [a + b + c]             
                      ] 
            for item in trial:   
                best_route_1[0] = item[0]
                best_route_1[1] = distance_calc(distance_matrix, [best_route_1[0] + [best_route_1[0][0]], 1])
                if (best_route_1[1]  < best_route[1]):
                    best_route = [best_route_1[0], best_route_1[1]]
                if (best_route[1] < city_list[1]):
                    city_list = [best_route[0], best_route[1]]              
            best_route = copy.deepcopy(seed) 
        count     = count + 1  
        iteration = iteration + 1  
        if (city_list_old > city_list[1] and recursive_seeding < 0):
             city_list_old     = city_list[1]
             count             = -2
             recursive_seeding = -1
        elif(city_list[1] >= city_list_old and recursive_seeding < 0):
            count              = -1
            recursive_seeding  = -2
    city_list = [city_list[0] + [city_list[0][0]], city_list[1]]
    return city_list[0], city_list[1]

############################################################################

# Function: Two-Opt Swap
def two_opt_swap(tour, i, k):
    new_tour = tour[:i] + tour[i:k+1][::-1] + tour[k+1:]
    return new_tour

# Function: FRNN 
def fixed_radius_nn(coordinates, distance_matrix, ratio = 1.5, local_search = True, verbose = True):
    n            = len(coordinates)
    initial_tour = random.sample(list(range(0, distance_matrix.shape[0])), distance_matrix.shape[0])
    route        = initial_tour
    distance     = distance_calc(distance_matrix, [[c+1 for c in route], 1])
    kd_tree      = KDTree(coordinates)
    improvement  = True
    avg_distance = np.mean([np.linalg.norm(coordinates[i] - coordinates[j]) for i in range(0, len(coordinates)) for j in range(i+1, len(coordinates))])
    r            = avg_distance * ratio
    count        = 1
    while (improvement == True):
        improvement = False
        if (verbose == True):
            print('KD Tree Search = ', count, 'Distance = ',  round(distance, 2))
            count = count + 1
        for i in range(0, n - 1):
            neighbors = kd_tree.query_ball_point(coordinates[route[i]], r = r)  
            for neighbor_index in neighbors:
                if (neighbor_index <= i or neighbor_index >= n):
                    continue
                new_tour   = two_opt_swap(route, i, neighbor_index)
                new_length = distance_calc(distance_matrix, [[c+1 for c in new_tour]+[new_tour[0]+1], 1])
                if (new_length < distance):
                    route       = new_tour
                    distance    = new_length
                    improvement = True
    route = [item + 1 for item in route]
    route.append(route[0])
    distance = distance_calc(distance_matrix,  [route, 1])
    seed  = [route, distance]
    if (local_search == True):
        route, distance = local_search_3_opt(distance_matrix, city_tour = seed, recursive_seeding = -1, verbose = True)
    return route, distance

############################################################################
