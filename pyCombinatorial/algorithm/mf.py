############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Multifragment Heuristic
 
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

# Function:  MF
def multifragment_heuristic(distance_matrix, local_search = True, verbose = True):
    pairs = [ [i, j] for i in range(0, distance_matrix.shape[0]) for j in range(i, distance_matrix.shape[0]) if i != j]
    dist  = [ distance_matrix[item[0], item[1]] for item in pairs]
    idx   = sorted(range(0, len(dist)), key = dist.__getitem__)
    dist  = [dist[i]  for i in idx]
    pairs = [pairs[i] for i in idx]
    route = []
    for pair in pairs:
        i, j = pair
        if (i not in route and j not in route):
            route.append(i)
            route.append(j)
        elif (i in route and j not in route):
            pos = route.index(i)
            A   = route[:pos]
            B   = route[pos:]
            r1  = A + [j] + B
            r2  = [j] + A + B
            ra  = [node+1 for node in r1]
            rb  = [node+1 for node in r2]
            ra  = ra + [ra[0]]
            rb  = rb + [rb[0]]
            d1  = distance_calc(distance_matrix, [ra, 1])
            d2  = distance_calc(distance_matrix, [rb, 1]) 
            if (d1 <= d2):
                route = [item for item in r1]
            else:
                route = [item for item in r2]
        elif (i not in route and j in route):
            pos = route.index(j)
            A   = route[:pos]
            B   = route[pos:]
            r1  = A + [i] + B
            r2  = [i] + A + B
            ra  = [node + 1 for node in r1]
            rb  = [node + 1 for node in r2]
            ra  = ra + [ra[0]]
            rb  = rb + [rb[0]]
            d1  = distance_calc(distance_matrix, [ra, 1])
            d2  = distance_calc(distance_matrix, [rb, 1]) 
            if (d1 <= d2):
                route = [item for item in r1]
            else:
                route = [item for item in r2]
    route    = route + [route[0]]
    route    = [node + 1 for node in route]
    distance = distance_calc(distance_matrix, [route, 1])
    seed     = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################
