############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Iterated Search
 
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
    i, j       = random.sample(list(range(0, len(city_tour[0])-1)), 2)
    if (i > j):
        i, j = j, i
    best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
    best_route[0][-1]    = best_route[0][0]              
    best_route[1]        = distance_calc(distance_matrix, best_route)                     
    return best_route

# Function: Local Search
def local_search(distance_matrix, city_tour, max_attempts = 50):
    count    = 0
    solution = copy.deepcopy(city_tour) 
    while (count < max_attempts):
        candidate = stochastic_2_opt(distance_matrix, solution)      
        if candidate[1] < solution[1]:
            solution  = copy.deepcopy(candidate)
            count     = 0
        else:
            count = count + 1                             
    return solution 

############################################################################

# Function: 4-opt Pertubation
def pertubation_4_opt(distance_matrix, city_tour):
    cl         = [city_tour[0][:-1], city_tour[1]]
    i, j, k, L = random.sample(list(range(0, len(cl[0]))), 4)
    idx        = [i, j, k, L]
    idx.sort()
    i, j, k, L = idx
    A          = cl[0][:i+1] + cl[0][i+1:j+1]
    B          = cl[0][j+1:k+1]
    b          = list(reversed(B))
    C          = cl[0][k+1:L+1]
    c          = list(reversed(C))
    D          = cl[0][L+1:]
    d          = list(reversed(D))
    trial      = [          
                  # 4-opt: Sequential
                  [A + b + c + d], [A + C + B + d], [A + C + b + d], [A + c + B + d], [A + D + B + c], 
                  [A + D + b + C], [A + d + B + c], [A + d + b + C], [A + d + b + c], [A + b + D + C], 
                  [A + b + D + c], [A + b + d + C], [A + C + d + B], [A + C + d + b], [A + c + D + B], 
                  [A + c + D + b], [A + c + d + b], [A + D + C + b], [A + D + c + B], [A + d + C + B],
                  
                  # 4-opt: Non-Sequential
                  [A + b + C + d], [A + D + b + c], [A + c + d + B], [A + D + C + B], [A + d + C + b]  
                 ]  
    item       = random.choice(trial)
    cl[0]      = item[0]
    cl[0]      = cl[0] + [cl[0][0]]
    cl[1]      = distance_calc(distance_matrix, cl)
    return cl

############################################################################

# Function: Iterated Search
def iterated_search(distance_matrix, city_tour, max_attempts = 20, iterations = 50, verbose = True):
    count         = 0
    solution      = copy.deepcopy(city_tour)
    best_solution = copy.deepcopy(city_tour)
    while (count < iterations):
        if (verbose == True):
            print('Iteration = ', count, 'Distance = ', round(best_solution[1], 2)) 
        if (distance_matrix.shape[0] > 4):
            solution = pertubation_4_opt(distance_matrix, solution)
        solution = local_search(distance_matrix, solution, max_attempts)
        if (solution[1] < best_solution[1]):
            best_solution = copy.deepcopy(solution) 
        count = count + 1
    route, distance = best_solution
    return route, distance

############################################################################
