############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - LNS - Large Neighborhood Search 
 
# GitHub Repository: <https://github.com/Valdecy> 

############################################################################

# Required Libraries
import copy
import numpy as np
import random

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

# Function: Tour Distance
def distance_point(tour, distance_matrix):
    tour_shifted = np.roll(tour, shift = -1)
    return np.sum(distance_matrix[tour, tour_shifted])

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
def random_removal(city_tour, neighborhood_size):
    removed   = random.sample(city_tour[1:], neighborhood_size)
    city_tour = [t for t in city_tour if t not in removed]
    return removed, city_tour

# Function: Insertion
def best_insertion(removed_nodes, city_tour, distance_matrix):
    for node in removed_nodes:
        best_insertion_cost  = float('inf')
        best_insertion_index = -1
        for i in range(1, len(city_tour) + 1):
            last_node      = city_tour[i - 1]
            next_node      = city_tour[i % len(city_tour)]
            insertion_cost = (distance_matrix[last_node, node] + distance_matrix[node, next_node] - distance_matrix[last_node, next_node])
            if (insertion_cost < best_insertion_cost):
                best_insertion_cost  = insertion_cost
                best_insertion_index = i
        city_tour.insert(best_insertion_index, node)
    return city_tour

############################################################################

# Function: Large Neighborhood Search
def large_neighborhood_search(distance_matrix, iterations = 1000, neighborhood_size = 4, local_search = True, verbose = True):
    initial_tour = list(range(0, distance_matrix.shape[0]))
    random.shuffle(initial_tour)
    route        = initial_tour.copy()
    distance     = distance_point(route, distance_matrix)
    count        = 0
    while (count <= iterations):
        if (verbose == True and count > 0):
            print('Iteration = ', count, 'Distance = ', round(distance, 2))  
        city_tour                = route.copy()
        removed_nodes, city_tour = random_removal(city_tour, neighborhood_size)
        new_tour                 = best_insertion(removed_nodes, city_tour, distance_matrix)
        new_tour_distance        = distance_point(new_tour, distance_matrix)
        if (new_tour_distance < distance):
            route    = new_tour
            distance = new_tour_distance
        count  = count + 1
    route = route + [route[0]]
    route = [item + 1 for item in route]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, [route, distance], -1, verbose)
    return route, distance

############################################################################
