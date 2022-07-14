############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Local Search-2-opt Stochastic
 
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

############################################################################

# Function: 2_opt Stochastic
def local_search_2_opt_stochastic(distance_matrix, city_tour, recursive_seeding = 150, verbose = True):
    count     = 0
    city_list = copy.deepcopy(city_tour)
    while (count < recursive_seeding):
        if (verbose == True):
            print('Iteration = ', count, 'Distance = ', round(city_list[1], 2))  
        best_route = copy.deepcopy(city_list)
        seed       = copy.deepcopy(city_list)        
        for i in range(0, len(city_list[0]) - 2):
            for j in range(i+1, len(city_list[0]) - 1):
                m, n  = random.sample(range(0, len(city_tour[0])-1), 2)
                if (m > n):
                    m, n = n, m
                best_route[0][m:n+1] = list(reversed(best_route[0][m:n+1]))           
                best_route[0][-1]    = best_route[0][0]              
                best_route[1]        = distance_calc(distance_matrix, best_route)                     
                if (best_route[1] < city_list[1]):
                    city_list[1] = copy.deepcopy(best_route[1])
                    for k in range(0, len(city_list[0])): 
                        city_list[0][k] = best_route[0][k]          
                best_route = copy.deepcopy(seed)
        count = count + 1  
    return city_list[0], city_list[1]

############################################################################
