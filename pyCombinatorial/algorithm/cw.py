############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Clarke & Wright  (Savings Heuristic)
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy

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

# Function: Memory List
def memory_list(nodes, pairs, sav):
    memory = [ nodes[1:], [[] for item in nodes[1:]], [[] for item in nodes[1:]]] # Node, # Pair, # Savings
    for i in range(0, len(pairs)):
       m, n = pairs[i]
       m, n = m-1, n-1 
       memory[1][m].append(n+1)
       memory[2][m].append(sav[i])
    for i in range(0, len(pairs)):
        m, n = pairs[i]
        for j in range(0, len(memory[0])):
            if (n == memory[0][j]):
                memory[1][j].append(m)
                memory[2][j].append(sav[i])
    return memory

# Function: Next Neighbour to Enter
def next_neighbour(memory, pairs, A, B, route):
    a      = A - 1
    b      = B - 1
    val_a  = max(memory[2][a])
    idx_a  = memory[2][a].index(val_a)
    val_b  = max(memory[2][b])
    idx_b  = memory[2][b].index(val_b)
    if (val_a >= val_b):   
        candidate = memory[1][a][idx_a]
        route     = [candidate] + route
        pair      = [candidate, A]
        pair.sort()
    else:
        candidate = memory[1][b][idx_b]
        route     = route + [candidate]
        pair      = [candidate, B]
        pair.sort()
    idx = pairs.index(tuple(pair))
    return route, idx

############################################################################

# Function:  CW
def clarke_wright_savings(distance_matrix, local_search = True, verbose = True):
    nodes = [item for item in list(range(0, distance_matrix.shape[0])) ]
    pairs = [ (nodes[i], nodes[j]) for i in range(1, len(nodes)-1) for j in range(i+1, len(nodes))]
    sav   = [ distance_matrix[i,0] + distance_matrix[j, 0] - distance_matrix[i, j]  for i,j in pairs]
    idx   = sav.index(max(sav))
    pair  = pairs[idx]
    route = list(pair)
    while (len(route) < distance_matrix.shape[0]-1):
        sav[idx]   = float('-inf')
        A          = route[0]
        B          = route[-1]
        if (len(route) >= 3):
            for i in route:
                if (A != i):
                    pair     = [A, i]
                    pair.sort()
                    pair     = tuple(pair)
                    idx      = pairs.index(tuple(pair))
                    sav[idx] = float('-inf')
                if (B != i):
                    pair     = [B, i]
                    pair.sort()
                    pair     = tuple(pair)
                    idx      = pairs.index(tuple(pair))
                    sav[idx] = float('-inf')
        memory     = memory_list(nodes, pairs, sav)
        route, idx = next_neighbour(memory, pairs, A, B, route)
    route    = [0] + route + [0]
    route    = [node+1 for node in route]
    distance = distance_calc(distance_matrix, [route, 1])
    seed     = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################

