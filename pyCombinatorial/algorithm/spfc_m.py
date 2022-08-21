############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Space Filling Curve (Morton)
 
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

# Function: Get Morton 2D points. Adapted from: https://bertvandenbroucke.netlify.app/2019/01/18/space-filling-curves/
def get_morton_2d(coordinates):
    def get_idx(x, y, size):
      result = 0
      for i in range(0, size):
        result |= (x & 1) << (2 * i + 1)
        result |= (y & 1) << (2 * i)
        x      >>= 1
        y      >>= 1
      return result
    max_val = np.max(coordinates)+1
    limit   = -1
    k       = 1
    while (limit < max_val):
        limit = 2**k
        k     = k + 1
    idxs = [get_idx(coordinates[i, 0], coordinates[i, 1], k) for i in range(0, coordinates.shape[0])]
    idxs = sorted(range(len(idxs)), key = lambda k: idxs[k])
    return idxs

############################################################################

# Function: SFC (Morton)
def space_filling_curve_m(coordinates, distance_matrix, local_search = True, verbose = True):
    flag    = False
    n_coord = np.copy(coordinates)
    for i in range(0, coordinates.shape[0]):
        for j in range(0, coordinates.shape[1]):
            if ( coordinates[i,j] / int(coordinates[i,j]) > 1):
                flag = True
                break
    if (flag == True): 
        n_coord = n_coord*100
        n_coord = n_coord.astype(int)  
    else:
        n_coord  = n_coord.astype(int)    
    route    = get_morton_2d(n_coord)
    route    = route + [route[0]]
    route    = [item+1 for item in route]
    distance = distance_calc(distance_matrix, [route, 1])
    seed     = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################
