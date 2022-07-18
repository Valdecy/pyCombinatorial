############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Guided Search
 
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
def local_search(distance_matrix, city_tour, penalty, max_attempts = 50, limit= 1):
    count    = 0
    ag_cost  = augumented_cost(distance_matrix, city_tour, penalty, limit)
    solution = copy.deepcopy(city_tour) 
    while (count < max_attempts):
        candidate           = stochastic_2_opt(distance_matrix, solution)
        candidate_augmented = augumented_cost(distance_matrix, candidate, penalty, limit)       
        if candidate_augmented < ag_cost:
            solution  = copy.deepcopy(candidate)
            ag_cost   = augumented_cost(distance_matrix, solution, penalty, limit)
            count     = 0
        else:
            count = count + 1                             
    return solution 

############################################################################

#Function: Augmented Cost
def augumented_cost(distance_matrix, city_tour, penalty, limit):
    augmented = 0   
    for i in range(0, len(city_tour[0]) - 1):
        c1 = city_tour[0][i]
        c2 = city_tour[0][i + 1]      
        if c2 < c1:
            c1, c2 = c2, c1            
        augmented = augmented + distance_matrix[c1-1, c2-1] + (limit * penalty[c1-1][c2-1])    
    return augmented

#Function: Utility
def utility (distance_matrix, city_tour, penalty, limit = 1):
    utilities = [0 for i in city_tour[0]]
    for i in range(0, len(city_tour[0]) - 1):
        c1 = city_tour[0][i]
        c2 = city_tour[0][i + 1]      
        if c2 < c1:
            c1, c2 = c2, c1            
        utilities[i] = distance_matrix[c1-1, c2-1] /(1 + penalty[c1-1][c2-1])  
    return utilities

#Function: Update Penalty
def update_penalty(penalty, city_tour, utilities):
    max_utility = max(utilities)   
    for i in range(0, len(city_tour[0]) - 1):
        c1 = city_tour[0][i]
        c2 = city_tour[0][i + 1]         
        if c2 < c1:
            c1, c2 = c2, c1        
        if (utilities[i] == max_utility):
            penalty[c1-1][c2-1] = penalty[c1-1][c2-1] + 1   
    return penalty

############################################################################

# Function: Guided Search
def guided_search(distance_matrix, city_tour, alpha = 0.3, local_search_optima = 1000, max_attempts = 20, iterations = 50, verbose = True):
    count         = 0
    limit         = alpha * (local_search_optima / len(city_tour[0]))  
    penalty       = [[0 for i in city_tour[0]] for j in city_tour[0]]
    solution      = copy.deepcopy(city_tour)
    best_solution = [[],float('+inf')]
    while (count < iterations):
        if (verbose == True):
            print('Iteration = ', count, 'Distance = ', round(best_solution[1], 2)) 
        solution  = local_search(distance_matrix, city_tour = solution, penalty = penalty, max_attempts = max_attempts, limit = limit)
        utilities = utility(distance_matrix, city_tour = solution, penalty = penalty, limit = limit)
        penalty   = update_penalty(penalty = penalty, city_tour = solution, utilities = utilities)
        if (solution[1] < best_solution[1]):
            best_solution = copy.deepcopy(solution) 
        count = count + 1
    route, distance = best_solution
    return route, distance

############################################################################