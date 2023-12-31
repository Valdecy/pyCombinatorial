############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - ALNS - Adaptive Large Neighborhood Search 
 
# GitHub Repository: <https://github.com/Valdecy> 

############################################################################

# Required Libraries
import copy
import numpy as np
import random

############################################################################

# Function: Euclidean Distance
def euclidean_distance(point1, point2):
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

# Function: Tour Distance
def distance_point(distance_matrix, city_tour):
    distance = 0
    for i in range(0, len(city_tour) - 1):
        distance = distance + distance_matrix[city_tour[i]][city_tour[i + 1]]
    distance = distance + distance_matrix[city_tour[-1]][city_tour[0]]
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
    if (verbose == True):
        print('')
        print('Local Search')
        print('')
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

# Function: Removal
def removal_operators():
    def random_removal(city_tour, num_removals):
        removed = set()
        while (len(removed) < num_removals):
            removed.add(random.choice(city_tour[1:]))
        return list(removed)
    return [random_removal]

# Function: Insertion
def insertion_operators():
    def cheapest_insertion(removed_nodes, city_tour, distance_matrix):
        for node in removed_nodes:
            best_insertion_cost  = float('inf')
            best_insertion_index = -1
            for i in range(1, len(city_tour) + 1):
                insertion_cost = (distance_matrix[city_tour[i - 1]][node] + distance_matrix[node][city_tour[i % len(city_tour)]] - distance_matrix[city_tour[i - 1]][city_tour[i % len(city_tour)]])
                if (insertion_cost < best_insertion_cost):
                    best_insertion_cost  = insertion_cost
                    best_insertion_index = i
            city_tour.insert(best_insertion_index, node)
        return city_tour
    return [cheapest_insertion]

############################################################################

# Function: Adaptive Large Neighborhood Search
def adaptive_large_neighborhood_search(distance_matrix, iterations = 100, removal_fraction = 0.2, rho = 0.1, local_search = True, verbose = True):
    initial_tour       = list(range(0, distance_matrix.shape[0]))
    random.shuffle(initial_tour)
    route              = initial_tour.copy()
    distance           = distance_point(distance_matrix, route)
    removal_ops        = removal_operators()
    insertion_ops      = insertion_operators()
    weights_removal    = [1.0] * len(removal_ops)
    weights_insertion  = [1.0] * len(insertion_ops)
    count              = 0
    while (count <= iterations):
        if (verbose == True and count > 0):
            print('Iteration = ', count, 'Distance = ', round(distance, 2))     
        city_tour     = route.copy()
        removal_op    = random.choices(removal_ops,   weights = weights_removal)[0]
        insertion_op  = random.choices(insertion_ops, weights = weights_insertion)[0]
        num_removals  = int(removal_fraction * distance_matrix.shape[0])
        removed_nodes = removal_op(city_tour, num_removals)
        for node in removed_nodes:
            city_tour.remove(node)
        new_tour          = insertion_op(removed_nodes, city_tour, distance_matrix)
        new_tour_distance = distance_point(distance_matrix, new_tour)
        if (new_tour_distance < distance):
            route                                                = new_tour
            distance                                             = new_tour_distance
            weights_removal[removal_ops.index(removal_op)]       = weights_removal[removal_ops.index(removal_op)]       * (1 + rho)
            weights_insertion[insertion_ops.index(insertion_op)] = weights_insertion[insertion_ops.index(insertion_op)] * (1 + rho)
        else:
            weights_removal[removal_ops.index(removal_op)]       = weights_removal[removal_ops.index(removal_op)]       * (1 - rho)
            weights_insertion[insertion_ops.index(insertion_op)] = weights_insertion[insertion_ops.index(insertion_op)] * (1 - rho)
        total_weight_removal   = sum(weights_removal)
        total_weight_insertion = sum(weights_insertion)
        weights_removal        = [w / total_weight_removal   for w in weights_removal]
        weights_insertion      = [w / total_weight_insertion for w in weights_insertion]
        count                  = count + 1
    route = route + [route[0]]
    route = [item + 1 for item in route]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, [route, distance], -1, verbose)
    return route, distance

############################################################################
