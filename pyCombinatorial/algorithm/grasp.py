############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - GRASP
  
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy  as np
import random
import os

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

# Function: Rank Cities by Distance
def ranking(distance_matrix, city = 0):
    rank = np.zeros((distance_matrix.shape[0], 2))  # ['Distance', 'City']
    for i in range(0, rank.shape[0]):
        rank[i,0] = distance_matrix[i,city]
        rank[i,1] = i + 1
    rank = rank[rank[:,0].argsort()]
    return rank

# Function: RCL
def restricted_candidate_list(distance_matrix, greediness_value = 0.5):
    seed     = [[], float('+inf')]
    sequence = []
    sequence.append(random.sample(list(range(1, distance_matrix.shape[0]+1)), 1)[0])
    count    = 1
    for i in range(0, distance_matrix.shape[0]):
        count = 1
        rand  = int.from_bytes(os.urandom(8), byteorder = 'big') / ((1 << 64) - 1)
        if (rand > greediness_value and len(sequence) < distance_matrix.shape[0]):
            next_city = int(ranking(distance_matrix, city = sequence[-1] - 1)[count,1])
            while next_city in sequence:
                count     = np.clip(count+1,1, distance_matrix.shape[0]-1)
                next_city = int(ranking(distance_matrix, city = sequence[-1] - 1)[count,1])
            sequence.append(next_city)
        elif (rand <= greediness_value and len(sequence) < distance_matrix.shape[0]):
            next_city = random.sample(list(range(1, distance_matrix.shape[0]+1)), 1)[0]
            while next_city in sequence:
                next_city = int(random.sample(list(range(1, distance_matrix.shape[0]+1)), 1)[0])
            sequence.append(next_city)
    sequence.append(sequence[0])
    seed[0] = sequence
    seed[1] = distance_calc(distance_matrix, seed)
    return seed

############################################################################

def greedy_randomized_adaptive_search_procedure(distance_matrix, city_tour, iterations = 50, rcl = 25, greediness_value = 0.5, verbose = True):
    count         = 0
    best_solution = copy.deepcopy(city_tour)
    while (count < iterations):
        if (verbose == True):
            print('Iteration = ', count, 'Distance = ', round(best_solution[1], 2))
        rcl_list = []
        for i in range(0, rcl):
            rcl_list.append(restricted_candidate_list(distance_matrix, greediness_value))
        candidate = int(random.sample(list(range(0,rcl)), 1)[0])
        city_tour = local_search_2_opt(distance_matrix, rcl_list[candidate], 2)
        while (city_tour[0] != rcl_list[candidate][0]):
            rcl_list[candidate] = copy.deepcopy(city_tour)
            city_tour           = local_search_2_opt(distance_matrix, rcl_list[candidate], 2)
        if (city_tour[1] < best_solution[1]):
            best_solution = copy.deepcopy(city_tour) 
        count = count + 1
    route, distance = best_solution
    return route, distance

############################################################################
