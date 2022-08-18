############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Local Search-2.5-opt
 
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

############################################################################

# Function: Possible Segments
def segments_2_opt(n):
    x    = []
    a, b = 0, 0
    for i in range(0, n):
        a = i
        for j in range(i + 1, n + (i > 0)):
            b = j
            x.append((a, b))    
    return x

############################################################################

# Function: 2_5_opt
def local_search_2h_opt(distance_matrix, city_tour, recursive_seeding = -1, verbose = True):
    if (recursive_seeding < 0):
        count = recursive_seeding - 1
    else:
        count = 0
    city_list     = [city_tour[0][:-1], city_tour[1]]
    city_list_old = city_list[1]*2
    iteration     = 0
    while (count < recursive_seeding):
        if (verbose == True):
            print('Iteration = ', iteration, 'Distance = ', round(city_list[1], 2))  
        best_route   = copy.deepcopy(city_list)
        best_route_1 = [[], 1]
        seed         = copy.deepcopy(city_list)     
        x            = segments_2_opt(len(city_list[0]))
        for item in x:
            trial                = []
            i, j                 = item   
            best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1])) 
            trial.append([item for item in best_route[0]])
            insertion            = [item for item in best_route[0][j+1:]]
            positions            = list(range(i+1, j+1))
            for k in insertion:
                new_route = [item for item in best_route[0]]
                new_route.remove(k)
                for pos in positions:
                    new_route.insert(pos, k)
                    trial.append([item for item in new_route])
                    new_route.remove(k)
            for item in trial:   
                best_route_1[0] = item
                best_route_1[1] = distance_calc(distance_matrix, [best_route_1[0] + [best_route_1[0][0]], 1])
                if (best_route_1[1]  < best_route[1]):
                    best_route = [best_route_1[0], best_route_1[1]]
                if (best_route[1] < city_list[1]):
                    city_list = [best_route[0], best_route[1]]   
            best_route = copy.deepcopy(seed) 
        count     = count + 1  
        iteration = iteration + 1  
        if (city_list_old > city_list[1] and recursive_seeding < 0):
             city_list_old     = city_list[1]
             count             = -2
             recursive_seeding = -1
        elif(city_list[1] >= city_list_old and recursive_seeding < 0):
            count              = -1
            recursive_seeding  = -2
    city_list = [city_list[0] + [city_list[0][0]], city_list[1]]
    return city_list[0], city_list[1]

############################################################################
