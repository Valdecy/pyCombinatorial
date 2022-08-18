############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Branch & Bound
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import numpy as np

############################################################################

# Function: First Minimum Distance
def min_1(distance_matrix, i): 
    vector = distance_matrix[i,:].tolist()
    idx    = np.argsort(vector)
    m1     = vector[idx[1]]
    return m1

# Function: Second Minimum Distance
def min_2(distance_matrix, i): 
    vector = distance_matrix[i,:].tolist()
    idx    = np.argsort(vector)
    m2     = vector[idx[2]]
    return m2 

############################################################################

# Function: Branch
def explore_path(route, distance, distance_matrix, bound, weight, level, path, visited):  
    if (level == distance_matrix.shape[0]): 
        if (distance_matrix[path[level - 1], path[0]] != 0): 
            dist = weight + distance_matrix[path[level - 1], path[0]] 
            if (dist < distance): 
                distance                             = dist 
                route[:distance_matrix.shape[0] + 1] = path[:]
                route[distance_matrix.shape[0]]      = path[0]
        return route, distance, bound, weight, path, visited
    for i in range(0, distance_matrix.shape[0]): 
        if (distance_matrix[path[level-1], i] != 0 and visited[i] == False): 
            temp   = bound 
            weight = weight + distance_matrix[path[level - 1], i] 
            if (level == 1): 
                bound = bound - ((min_1(distance_matrix, path[level - 1]) + min_1(distance_matrix, i)) / 2) 
            else: 
                bound = bound - ((min_2(distance_matrix, path[level - 1]) + min_1(distance_matrix, i)) / 2)  
            if (bound + weight < distance): 
                path[level] = i 
                visited[i]  = True
                route, distance, bound, weight, path, visited = explore_path(route, distance, distance_matrix, bound, weight, level + 1, path, visited) 
            weight  = weight - distance_matrix[path[level - 1], i] 
            bound   = temp
            visited = [False] * len(visited) 
            for j in range(level): 
                if (path[j] != -1): 
                    visited[path[j]] = True
    return route, distance, bound, weight, path, visited

############################################################################

# Function: Branch and Bound (Adapted from: https://www.geeksforgeeks.org/traveling-salesman-problem-using-branch-and-bound-2/)
def branch_and_bound(distance_matrix): 
    distance   = float('+inf')
    path       = [  -1   ] * (distance_matrix.shape[0] + 1) 
    path[0]    = 0
    visited    = [ False ] *  distance_matrix.shape[0]
    visited[0] = True
    route      = [ None  ] * (distance_matrix.shape[0] + 1)
    weight     = 0
    level      = 1
    bound      = np.ceil(sum([ (min_1(distance_matrix, i) + min_2(distance_matrix, i)) for i in range(0, distance_matrix.shape[0])])/2) 
    route, distance, bound, weight, path, visited = explore_path(route, distance, distance_matrix, bound, weight, level, path, visited) 
    route      = [item+1 for item in route]
    return route, distance

############################################################################

