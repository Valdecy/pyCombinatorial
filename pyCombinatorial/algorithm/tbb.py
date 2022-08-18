############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Truncated Branch & Bound
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy as np

###############################################################################

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

###############################################################################

# Function: Truncated B&B
def truncated_branch_and_bound(distance_matrix, verbose = True):
    dist  = np.copy(distance_matrix)
    dist  = dist.astype(float)
    np.fill_diagonal(dist, float('+inf'))
    r_min = np.min(dist, axis = 1)
    dist  = dist - r_min.reshape(-1,1)
    c_min = np.min(dist, axis = 0)
    dist  = dist - c_min.reshape(1,-1)
    cost  = np.sum(r_min + c_min)
    k     = 0
    route = [k]
    nodes = [i for i in list(range(0, distance_matrix.shape[0])) if i not in route]
    count = 0
    while len(nodes) > 0:
        c_lst = []
        for i in nodes:
            reduced       = np.copy(dist)
            reduced[k, :] = float('+inf')
            reduced[:, i] = float('+inf')
            reduced[i, k] = float('+inf')
            r_min         = np.min(reduced, axis = 1)
            c_min         = np.min(reduced, axis = 0)
            r_min         = np.where(r_min == float('+inf'), 0, r_min)
            c_min         = np.where(c_min == float('+inf'), 0, c_min)
            c_lst.append(cost + dist[k, i] + np.sum(r_min + c_min))
        i          = nodes[c_lst.index(min(c_lst))]
        cost       = cost + min(c_lst)
        dist[k, :] = float('+inf')
        dist[:, i] = float('+inf')
        k          = i
        route.append(i)
        nodes.remove(i)
        if (verbose == True):
            print('Iteration = ', count, ' Visited Nodes = ', len(route))
        count = count + 1
    route           = route + [route[0]]
    route           = [item + 1 for item in route]
    distance        = distance_calc(distance_matrix, [route, 1])
    seed            = [route, distance]
    route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = False)
    return route, distance

###############################################################################
