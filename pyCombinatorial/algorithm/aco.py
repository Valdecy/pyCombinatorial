############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Ant Colony Optimization
 
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
    return city_list[0], city_list[1]

############################################################################

# Function: Initial Attractiveness
def attractiveness(distance_matrix):
    h = np.zeros((distance_matrix.shape[0], distance_matrix.shape[0]))  
    for i in range(0, distance_matrix.shape[0]):
        for j in range(0, distance_matrix.shape[1]):
            if (i == j or distance_matrix[i,j] == 0):
                h[i, j] = 0.000001
            else:
                h[i, j] = 1/distance_matrix[i,j]   
    return h

# Function: Probability Matrix 
def city_probability(h, thau, city = 0, alpha = 1, beta = 2, city_list = []):
    probability = np.zeros((h.shape[0], 3)) # ['atraction','probability','cumulative_probability']
    for i in range(0, probability.shape[0]):
        if (i+1 not in city_list):
            probability[i, 0] = (thau[i, city]**alpha)*(h[i, city]**beta)
    for i in range(0, probability.shape[0]):
        if (i+1 not in city_list and probability[:,0].sum() != 0):
            probability[i, 1] = probability[i, 0]/probability[:,0].sum()
        if (i == 0):
            probability[i, 2] = probability[i, 1] 
        else:
            probability[i, 2] = probability[i, 1] + probability[i - 1, 2]     
    if (len(city_list) > 0):
        for i in range(0, len(city_list)):
            probability[city_list[i]-1, 2] = 0.0            
    return probability

# Function: Select Next City
def city_selection(probability_matrix, city_list = []):
    random = int.from_bytes(os.urandom(8), byteorder = 'big') / ((1 << 64) - 1)
    city   = 0
    for i in range(0, probability_matrix.shape[0]):
        if (random <= probability_matrix[i, 2] and i+1 not in city_list):
          city = i + 1
          break     
    return city

# Function: Update Thau
def update_thau(distance_matrix, thau, city_list = []):
    distance = 0
    for i in range(0, len(city_list)-1):
        j        = i + 1
        distance = distance + distance_matrix[city_list[i]-1,city_list[j]-1] 
    pheromone = 1  
    for i in range(0, len(city_list)-1):
        j          = i + 1 
        m          = city_list[i]-1
        n          = city_list[j]-1
        thau[m, n] = thau[m, n] + pheromone        
    return thau

# Function: Ants City List
def ants_path(distance_matrix, h, thau, alpha, beta, full_list, ants, local_search):
    distance           = np.sum(distance_matrix.sum())
    best_city_list     = []
    best_path_distance = []
    for ant in range(0, ants):
        city_list = []
        initial   = random.randrange(1, distance_matrix.shape[0])
        city_list.append(initial)           
        for i in range(0, distance_matrix.shape[0] - 1):
            probability = city_probability(h, thau, city = i, alpha = alpha, beta = beta, city_list = city_list)
            path_point  = city_selection(probability, city_list = city_list)
            if (path_point == 0):
                path_point = [value for value in full_list if value not in city_list][0]
            city_list.append(path_point)
        city_list.append(city_list[0])
        path_distance = 0
        for i in range(0, len(city_list)-1):
            j             = i + 1
            path_distance = path_distance + distance_matrix[city_list[i]-1,city_list[j]-1] 
        if (distance > path_distance):
            best_city_list     = copy.deepcopy(city_list)
            best_path_distance = path_distance
            distance           = path_distance
    best_route                         = copy.deepcopy([best_city_list])
    best_route.append(best_path_distance)
    if (local_search == True):
        best_city_list, best_path_distance = local_search_2_opt(distance_matrix, city_tour = best_route, recursive_seeding = -1)
    thau = update_thau(distance_matrix, thau, city_list = best_city_list)
    return best_city_list, best_path_distance, thau

############################################################################

# ACO Function
def ant_colony_optimization(distance_matrix, ants = 5, iterations = 50, alpha = 1, beta = 2, decay = 0.05, local_search = True, verbose = True): 
    count       = 0  
    best_route  = [] 
    full_list   = list(range(1, distance_matrix.shape[0] + 1))
    distance    = np.sum(distance_matrix.sum())
    h           = attractiveness(distance_matrix)
    thau        = np.ones((distance_matrix.shape[0], distance_matrix.shape[0]))  
    while (count <= iterations):
        if (verbose == True and count > 0):
            print('Iteration = ', count, 'Distance = ', round(best_route[1], 2))            
        city_list, path_distance, thau = ants_path(distance_matrix, h, thau, alpha, beta, full_list, ants, local_search)
        thau                           = thau*(1 - decay)
        if (distance > path_distance):
            best_route = copy.deepcopy([city_list])
            best_route.append(path_distance)
            distance   = best_route[1]
        count = count + 1   
    route, distance = best_route
    return route, distance

############################################################################
