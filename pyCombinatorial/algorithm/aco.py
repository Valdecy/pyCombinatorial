############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Ant Colony Optimization
 
# GitHub Repository: <https://github.com/Valdecy> 

############################################################################

# Required Libraries
import copy
import numpy as np

############################################################################

# Helper: Calculate Path Distance
def calculate_distance(distance_matrix, city_list):
    path_distance = 0
    for i in range(0, len(city_list) - 1):
        path_distance = path_distance + distance_matrix[city_list[i]-1, city_list[i+1]-1]
    path_distance = path_distance + distance_matrix[city_list[-1]-1, city_list[0]-1]
    return path_distance

# Helper: Perform Local Search (Optional)
def local_search_2_opt(distance_matrix, city_tour, recursive_seeding = -1):
    city_list, best_path_distance = city_tour[0], city_tour[1]
    improved                      = True
    while (improved == True):
        improved = False
        for i in range(1, len(city_list) - 2):
            for j in range(i + 1, len(city_list) - 1):
                new_city_list      = city_list[:]
                new_city_list[i:j] = city_list[i:j][::-1]
                new_distance       = calculate_distance(distance_matrix, new_city_list)
                if (new_distance < best_path_distance):
                    best_path_distance = new_distance
                    city_list          = new_city_list
                    improved           = True
    return city_list, best_path_distance

############################################################################

# Helper: Calculate Attractiveness
def attractiveness(distance_matrix):
    h = 1 / (distance_matrix + 1e-10) 
    np.fill_diagonal(h, 0)
    return h

# Helper: Update Pheromone Matrix
def update_thau(distance_matrix, thau, city_list):
    path_distance = 0
    for i in range(len(city_list) - 1):
        path_distance = path_distance + distance_matrix[city_list[i]-1, city_list[i+1]-1]
    path_distance = path_distance + distance_matrix[city_list[-1]-1, city_list[0]-1]  
    for i in range(len(city_list) - 1):
        thau[city_list[ i ]-1, city_list[i+1]-1] = thau[city_list[ i ]-1, city_list[i+1]-1] + 1 / path_distance
        thau[city_list[i+1]-1, city_list[ i ]-1] = thau[city_list[i+1]-1, city_list[ i ]-1] + 1 / path_distance
    thau[city_list[-1]-1, city_list[ 0]-1] = thau[city_list[-1]-1, city_list[ 0]-1] + 1 / path_distance
    thau[city_list[ 0]-1, city_list[-1]-1] = thau[city_list[ 0]-1, city_list[-1]-1] + 1 / path_distance
    return thau

# Helper: Generate Ant Paths
def ants_path(distance_matrix, h, thau, alpha, beta, full_list, ants, local_search):
    best_path_distance = float('inf')
    best_city_list     = None
    for _ in range(0, ants):
        city_list = [np.random.choice(full_list)]
        while (len(city_list) < len(full_list)):
            current_city  = city_list[-1]
            probabilities = []
            for next_city in full_list:
                if (next_city not in city_list):
                    p = (thau[current_city-1, next_city-1] ** alpha) * (h[current_city-1, next_city-1] ** beta)
                    probabilities.append(p)
                else:
                    probabilities.append(0)
            probabilities = np.array(probabilities) / np.sum(probabilities)
            next_city     = np.random.choice(full_list, p = probabilities)
            city_list.append(next_city)
        path_distance = calculate_distance(distance_matrix, city_list)
        if (path_distance < best_path_distance):
            best_city_list     = copy.deepcopy(city_list)
            best_path_distance = path_distance
            
    if (local_search == True):
        best_city_list, best_path_distance = local_search_2_opt(distance_matrix, city_tour = [best_city_list, best_path_distance])
    thau = update_thau(distance_matrix, thau, city_list = best_city_list)
    return best_city_list, best_path_distance, thau

############################################################################

# ACO Function
def ant_colony_optimization(distance_matrix, ants = 5, iterations = 50, alpha = 1, beta = 2, decay = 0.05, local_search = True, verbose = True):
    count      = 0
    best_route = []
    full_list  = list(range(1, distance_matrix.shape[0] + 1))
    distance   = np.sum(distance_matrix.sum())
    h          = attractiveness(distance_matrix)
    thau       = np.ones((distance_matrix.shape[0], distance_matrix.shape[0]))
    while (count <= iterations):
        if (verbose == True and count > 0):
            print(f'Iteration = {count}, Distance = {round(best_route[1], 2)}')
        city_list, path_distance, thau = ants_path(distance_matrix, h, thau, alpha, beta, full_list, ants, local_search)
        thau                           = thau*(1 - decay)
        if (distance > path_distance):
            best_route = copy.deepcopy([city_list])
            best_route.append(path_distance)
            distance   = best_route[1]
        count = count + 1
    init_city = best_route[0][0]
    best_route[0].append(init_city)
    return best_route[0], best_route[1]

############################################################################
