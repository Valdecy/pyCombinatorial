############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Local Search-Scatter Search

# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import random
import copy
import os

from operator import itemgetter

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

# Function: Initial Seed
def seed_function(distance_matrix):
    seed     = [[],float('inf')]
    sequence = random.sample(list(range(1, distance_matrix.shape[0]+1)), distance_matrix.shape[0])
    sequence.append(sequence[0])
    seed[0]  = sequence
    seed[1]  = distance_calc(distance_matrix, seed)
    return seed

############################################################################

# Function: Local Improvement 2_opt
def local_search_2_opt(distance_matrix, city_tour):
    city_list  = copy.deepcopy(city_tour)
    best_route = copy.deepcopy(city_list)
    seed       = copy.deepcopy(city_list)        
    for i in range(0, len(city_list[0]) - 2):
        for j in range(i+1, len(city_list[0]) - 1):
            best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
            best_route[0][-1]    = best_route[0][0]                          
            best_route[1]        = distance_calc(distance_matrix, best_route)           
            if (best_route[1] < city_list[1]):
                city_list[1] = copy.deepcopy(best_route[1])
                for n in range(0, len(city_list[0])): 
                    city_list[0][n] = best_route[0][n]          
            best_route = copy.deepcopy(seed) 
    return city_list

############################################################################

# Function: Crossover
def crossover_tsp(distance_matrix, reference_list, reverse_prob = 0.5, scramble_prob = 0.3):
    ix, iy    = random.sample(list(range(0,len(reference_list))), 2)
    parent_1  = reference_list[ix][0]
    parent_1  = parent_1[:-1]
    parent_2  = reference_list[iy][0]
    parent_2  = parent_2[:-1]
    offspring = [0]*len(parent_2)
    i, j = random.sample(list(range(0,len(parent_1))), 2)
    if (i > j):
        i, j = j, i
    rand_1 = int.from_bytes(os.urandom(8), byteorder = 'big') / ((1 << 64) - 1)
    if (rand_1 < reverse_prob):
        parent_1[i:j+1] = list(reversed(parent_1[i:j+1]))
    offspring[i:j+1] = parent_1[i:j+1]
    parent_2         = [x for x in parent_2 if x not in parent_1[i:j+1]]
    rand_2           = int.from_bytes(os.urandom(8), byteorder = 'big') / ((1 << 64) - 1)
    if (rand_2 < scramble_prob):
        random.shuffle(parent_2)
    count = 0
    for i in range(0, len(offspring)):
        if (offspring[i] == 0):
            offspring[i] = parent_2[count]
            count        = count + 1
    offspring.append(offspring[0])
    offspring    = [offspring, 1]
    offspring[1] = distance_calc(distance_matrix, offspring)
    return offspring

############################################################################

# Function: Scatter Search
def scatter_search(distance_matrix, city_tour, iterations = 50, reference_size = 25, reverse_prob = 0.5, scramble_prob = 0.3, verbose = True):
    count          = 0
    best_solution  = copy.deepcopy(city_tour)
    reference_list = []
    for i in range(0, reference_size):
        reference_list.append(seed_function(distance_matrix))   
    while (count < iterations):    
        if (verbose == True):
            print('Iteration = ', count, 'Distance = ', round(best_solution[1], 2))        
        candidate_list = []
        for i in range(0, reference_size):
            candidate_list.append(crossover_tsp(distance_matrix, reference_list = reference_list, reverse_prob = reverse_prob, scramble_prob = scramble_prob))          
        for i in range(0, reference_size):
            candidate_list[i] = local_search_2_opt(distance_matrix, city_tour = candidate_list[i])
        for i in range(0, reference_size):        
            reference_list.append(candidate_list[i])
        reference_list = sorted(reference_list, key = itemgetter(1))
        reference_list = reference_list[:reference_size]
        for i in range(0, reference_size):
            if (reference_list[i][1] < best_solution[1]):
                best_solution = copy.deepcopy(reference_list[i]) 
        count = count + 1
    route, distance = best_solution
    return route, distance

############################################################################
