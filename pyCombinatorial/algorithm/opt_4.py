############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Local Search-4-opt
 
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
def segments_4_opt(n):
    x          = []
    a, b, c, d = 0, 0, 0, 0
    for i in range(0, n):
        a = i
        for j in range(i + 1, n):
            b = j
            for k in range(j + 1, n):
                c = k
                for L in range(k + 1, n + (i > 0)):
                    d = L
                    x.append((a, b, c, d))    
    return x

############################################################################

# Function: 4_opt
def local_search_4_opt(distance_matrix, city_tour, recursive_seeding = -1, verbose = True):
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
        x            = segments_4_opt(len(city_list[0]))
        for item in x:
            i, j, k, L = item   
            A          = best_route[0][:i+1] + best_route[0][i+1:j+1]
            a          = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1]))
            B          = best_route[0][j+1:k+1]
            b          = list(reversed(B))
            C          = best_route[0][k+1:L+1]
            c          = list(reversed(C))
            D          = best_route[0][L+1:]
            d          = list(reversed(D))
            trial      = [ 
                           # Original Tour
                           #[A + B + C + D],
                           
                           # Permutation
                           [A + C + B + D],
                           [A + C + D + B],
                           
                           
                           # 1
                           [a + B + C + D],
                           [a + C + B + D],
                           [a + C + D + B],
                           
                           [A + b + C + D],
                           [A + C + b + D],
                           [A + C + D + b],
                           
                           [A + B + c + D],
                           [A + c + B + D],
                           [A + c + D + B],
                           
                           [A + B + C + d],
                           [A + C + B + d],
                           [A + C + d + B],
                           
                           
                           # 2
                           [a + b + C + D],
                           [a + C + b + D],
                           [a + C + D + b],
                           
                           [a + B + c + D],
                           [a + c + B + D],
                           [a + c + D + B],
                           
                           [a + B + C + d],
                           [a + C + B + d],
                           [a + C + d + B],
                           
                           [A + b + c + D],
                           [A + c + b + D],
                           [A + c + D + b],
                           
                           [A + b + C + d],
                           [A + C + b + d],
                           [A + C + d + b],
                           
                           [A + B + c + d],
                           [A + c + B + d],
                           [A + c + d + B],
                           
                           
                           
                           # 3
                           [a + b + c + D],
                           [a + c + b + D],
                           [a + c + D + b], 

                           [a + b + C + d],
                           [a + C + b + d],
                           [a + C + d + b],
                           
                           [a + B + c + d],
                           [a + c + B + d],
                           [a + c + d + B], 
                           
                           [A + b + c + d],
                           [A + c + b + d],
                           [A + c + d + b],
                           
                           
                           
                           # 4
                           [a + b + c + d],
                           [a + c + b + d],
                           [a + c + d + b],
                           
                         ]   
            for item in trial:   
                best_route_1[0] = item[0]
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

