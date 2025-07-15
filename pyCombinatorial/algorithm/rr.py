############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Ruin & Recreate
#
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

# Function: Regret-2 Insertion 
def regret2_insertion(new_tour, to_insert, distance_matrix):
    new_tour  = [item-1 for item in new_tour]
    to_insert = [item-1 for item in to_insert]
    while to_insert:
        best_regret, best_city, best_pos = -np.inf, None, None
        for city in to_insert:
            insertion_costs = []
            for j in range(0, len(new_tour) - 1):
                prev, nxt = new_tour[j], new_tour[j + 1]
                delta     = distance_matrix[prev, city] + distance_matrix[city, nxt] - distance_matrix[prev, nxt]
                insertion_costs.append((delta, j + 1))
            if not insertion_costs:
                continue
            insertion_costs.sort(key=lambda x: x[0])
            d1, p1 = insertion_costs[0]
            d2     = insertion_costs[1][0] if len(insertion_costs) > 1 else d1
            regret = d2 - d1
            if regret > best_regret:
                best_regret = regret
                best_city   = city
                best_pos    = p1
        if best_city is None:
            break
        new_tour.insert(best_pos, best_city)
        to_insert.remove(best_city)
    new_tour = [item+1 for item in new_tour]
    return new_tour

############################################################################

# Function: Ruin & Recreate
def ruin_and_recreate(city_tour, distance_matrix, iterations = 100, ruin_rate = 0.50, local_search = True, verbose = True):
    city_list = copy.deepcopy(city_tour)
    removable = [city for city in city_list[0][:-1]]
    route     = city_list[0]
    distance  = city_list[1]
    best_r    = copy.deepcopy(route)
    best_d    = distance
    iteration = 0
    for _ in range(0, iterations):
        n_remove  = max(1, int(len(removable) * ruin_rate))
        to_remove = set(np.random.choice(removable, min(n_remove, len(removable)), replace = False))
        route     = [city for city in route if city not in to_remove]
        if route[0] != route[-1]:
            route.append(route[0])
        route    = regret2_insertion(route, to_remove, distance_matrix)
        distance = distance_calc(distance_matrix, [route, distance])
        if (verbose == True):
            print('Iteration = ', iteration, 'Distance = ', round(best_d, 2))  
        if distance < best_d:
            best_r = copy.deepcopy(route)
            best_d = distance
        iteration = iteration + 1
    if (local_search == True):
        print('')
        print('Local Search:')
        route, distance = local_search_2_opt(distance_matrix, [best_r, best_d], recursive_seeding = -1, verbose = verbose)
    return  best_r, best_d

############################################################################
