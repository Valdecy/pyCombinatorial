############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Zero Suffix Method
 
# GitHub Repository: <https://github.com/Valdecy> 

############################################################################

# Required Libraries
import copy
import numpy as np

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

# Class: Find Union
class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank   = [0] * size
    
    def find(self, node):
        if (self.parent[node] != node):
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]
   
    def union(self, node1, node2):
        root1 = self.find(node1)
        root2 = self.find(node2)
        if (root1 != root2):
            if (self.rank[root1] > self.rank[root2]):
                self.parent[root2] = root1
            elif (self.rank[root1] < self.rank[root2]):
                self.parent[root1] = root2
            else:
                self.parent[root2] = root1
                self.rank[root1]   = self.rank[root1] + 1
    
    def connected(self, node1, node2):
        return self.find(node1) == self.find(node2)
    
############################################################################

# Function:REduce Matrix
def reduce_matrix(matrix):
    for i in range(0, matrix.shape[0]):
        valid_values = matrix[i, :][matrix[i, :] != np.inf]
        if (valid_values.size > 0):
            row_min      = np.min(valid_values)
            matrix[i, :] = matrix[i, :] - row_min
    for j in range(0, matrix.shape[1]):
        valid_values = matrix[:, j][matrix[:, j] != np.inf]
        if (valid_values.size > 0):
            col_min      = np.min(valid_values)
            matrix[:, j] = matrix[:, j] - col_min
    return matrix

# Function: Suffix Values
def find_suffix_values(matrix):
    suffix_values = np.full(matrix.shape, np.inf)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if (matrix[i, j] == 0):
                row_values          = np.delete(matrix[i, :], j)
                col_values          = np.delete(matrix[:, j], i)
                row_min             = np.min(row_values[row_values != np.inf]) if row_values[row_values != np.inf].size > 0 else 0
                col_min             = np.min(col_values[col_values != np.inf]) if col_values[col_values != np.inf].size > 0 else 0
                suffix_values[i, j] = row_min + col_min
    return suffix_values

# Function: Max Suffix
def select_zero_with_max_suffix(suffix_values, visited_rows, visited_cols):
    valid_suffix_values = suffix_values[suffix_values != np.inf]
    if (valid_suffix_values.size == 0):
        return None
    max_value  = np.max(valid_suffix_values)
    candidates = np.argwhere(suffix_values == max_value)
    for i, j in candidates:
        if i not in visited_rows and j not in visited_cols:
            return (i, j)
    return None

# Function: Path Build
def construct_path(path_pairs, n):
    route = [path_pairs[0][0]]
    visited = set(route)
    while len(route) < n:
        for pair in path_pairs:
            if (pair[0] == route[-1] and pair[1] not in visited):
                route.append(pair[1])
                visited.add(pair[1])
                break
        else:
            for pair in path_pairs:
                if (pair[0] not in visited):
                    route.append(pair[0])
                    visited.add(pair[0])
                    break
    route.append(route[0])  
    return route

############################################################################

# Function: Zero Suffix Method
def zero_suffix_method(distance_matrix, local_search = True, verbose = True):
    n            = distance_matrix.shape[0]
    matrix       = distance_matrix.copy()
    np.fill_diagonal(matrix, np.inf)
    path_pairs   = []
    visited_rows = set()
    visited_cols = set()
    uf           = UnionFind(n)
    iteration    = 0
    while (len(path_pairs) < n):
        if (verbose == True):
            print('Iteration: ', iteration)
        matrix        = reduce_matrix(matrix)
        suffix_values = find_suffix_values(matrix)
        zero          = select_zero_with_max_suffix(suffix_values, visited_rows, visited_cols)
        if (zero is None):
            break
        i, j = zero
        if (uf.connected(i, j) and len(path_pairs) < n - 1):
            matrix[i, j] = np.inf  
            continue
        path_pairs.append((i, j))
        visited_rows.add(i)
        visited_cols.add(j)
        uf.union(i, j)
        matrix[i, :] = np.inf
        matrix[:, j] = np.inf
        iteration    = iteration + 1
    route    = construct_path(path_pairs, n)
    route    = [item + 1 for item in route]
    distance = distance_calc(distance_matrix,  [route, 1])
    seed     = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, city_tour = seed, recursive_seeding = -1, verbose = True)
    return route, distance

############################################################################
