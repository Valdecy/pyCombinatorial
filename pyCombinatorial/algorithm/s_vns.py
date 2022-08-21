############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Variable Neighborhood Search

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

# Function: Stochastic 2_opt
def stochastic_2_opt(distance_matrix, city_tour):
    best_route = copy.deepcopy(city_tour)      
    i, j       = random.sample(range(0, len(city_tour[0])-1), 2)
    if (i > j):
        i, j = j, i
    best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
    best_route[0][-1]    = best_route[0][0]              
    best_route[1]        = distance_calc(distance_matrix, best_route)                     
    return best_route

# Function: Local Search
def local_search(distance_matrix, city_tour, max_attempts = 50, neighbourhood_size = 5):
    count    = 0
    solution = copy.deepcopy(city_tour) 
    while (count < max_attempts): 
        for i in range(0, neighbourhood_size):
            candidate = stochastic_2_opt(distance_matrix, solution)
        if candidate[1] < solution[1]:
            solution  = copy.deepcopy(candidate)
            count     = 0
        else:
            count = count + 1                             
    return solution 

############################################################################

# Function: Variable Neighborhood Search
def variable_neighborhood_search(distance_matrix, city_tour, max_attempts = 20, neighbourhood_size = 5, iterations = 50, verbose = True):
    count         = 0
    solution      = copy.deepcopy(city_tour)
    best_solution = copy.deepcopy(city_tour)
    while (count < iterations):
        if (verbose == True):
            print('Iteration = ', count, 'Distance = ', round(best_solution[1], 2))
        for i in range(0, neighbourhood_size):
            for j in range(0, neighbourhood_size):
                solution = stochastic_2_opt(distance_matrix, best_solution)
            solution = local_search(distance_matrix, solution, max_attempts, neighbourhood_size)
            if (solution[1] < best_solution[1]):
                best_solution = copy.deepcopy(solution) 
                break
        count = count + 1
    route, distance = best_solution
    return route, distance

############################################################################
