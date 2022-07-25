############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Twice-Around the Tree Algorithm (Double Tree Algorithm)
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import networkx as nx
import numpy as np

from scipy.sparse.csgraph import minimum_spanning_tree

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

# Function: Twice-Around the Tree Algorithm
def tat_algorithm(distance_matrix, local_search = True, verbose = True):
    # Minimum Spanning Tree T
    graph_T = minimum_spanning_tree(distance_matrix)
    graph_T = graph_T.toarray().astype(int)
    # Double Minimum Spanning Tree H
    graph_H = np.zeros((graph_T.shape))
    for i in range(0, graph_T.shape[0]):
        for j in range(0, graph_T.shape[1]):
            if (graph_T[i,j] > 0):
                graph_H[i,j] = 1 #graph_T[i,j]
                graph_H[j,i] = 1 #graph_T[i,j]    
    # Eulerian Path
    H = nx.from_numpy_matrix(graph_H)
    if (nx.is_eulerian(H)):
        euler = list(nx.eulerian_path(H))
    else:
        H     = nx.eulerize(H)
        euler = list(nx.eulerian_path(H))
    # Shortcutting
    route = []
    for path in euler:
        i, j = path
        if (i not in route):
            route.append(i)
        if (j not in route):
            route.append(j)
    route    = route + [route[0]]
    route    = [item + 1 for item in route]
    distance = distance_calc(distance_matrix, [route, 1])
    seed     = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################

