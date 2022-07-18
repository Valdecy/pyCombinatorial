############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Local Search-Stochastic Hill Climbing
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import random
import copy

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

# Function: 2_opt
def local_search_2_opt(distance_matrix, city_tour, recursive_seeding = -1):
    if (recursive_seeding < 0):
        count = -2
    else:
        count = 0
    city_list = copy.deepcopy(city_tour)
    distance  = city_list[1]*2
    while (count < recursive_seeding):
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
        count = count + 1
        if (distance > city_list[1] and recursive_seeding < 0):
             distance          = city_list[1]
             count             = -2
             recursive_seeding = -1
        elif(city_list[1] >= distance and recursive_seeding < 0):
            count             = -1
            recursive_seeding = -2
    return city_list

############################################################################

# Function: Mutation
def mutate_candidate(distance_matrix, candidate):
    k  = random.sample(list(range(1, len(candidate[0])-1)), 2)
    k1 = k[0]
    k2 = k[1]  
    A  = candidate[0][k1]
    B  = candidate[0][k2]
    candidate[0][k1] = B
    candidate[0][k2] = A
    candidate[1]     = distance_calc(distance_matrix, candidate)
    candidate        = local_search_2_opt(distance_matrix, candidate, 2)
    return candidate

############################################################################

# Function: Stochastic Hill Climbing
def stochastic_hill_climbing(distance_matrix, city_tour, iterations = 50, verbose = True):
    count         = 0
    best_solution = copy.deepcopy(city_tour)  
    candidate     = copy.deepcopy(city_tour) 
    while (count < iterations):
        if (verbose == True):
            print('Iteration = ', count, 'Distance = ', round(best_solution[1], 2))
        candidate = mutate_candidate(distance_matrix, candidate)              
        if (candidate[1] < best_solution[1]):
            best_solution = copy.deepcopy(candidate) 
        count = count + 1
    route, distance = best_solution
    return route, distance

############################################################################