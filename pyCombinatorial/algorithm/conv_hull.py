############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Convex Hull Algorithm
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy

from scipy.spatial import ConvexHull  

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

# Function: Convex Hull
def convex_hull_algorithm(coordinates, distance_matrix, local_search = True, verbose = True):
    hull        = ConvexHull(coordinates)
    idx_h       = hull.vertices.tolist()
    idx_h       = [item+1 for item in idx_h]
    idx_h_pairs = [(idx_h[i], idx_h[i+1]) for i in range(0, len(idx_h)-1)]
    idx_h_pairs.append((idx_h[-1], idx_h[0]))
    idx_in      = [item for item in list(range(1, coordinates.shape[0]+1)) if item not in idx_h]
    for _ in range(0, len(idx_in)):
        x = []
        y = []
        z = []
        for i in range(0, len(idx_in)):
            L           = idx_in[i]
            cost        = [(distance_matrix[m-1, L-1], distance_matrix[L-1, n-1], distance_matrix[m-1, n-1]) for m, n in idx_h_pairs]
            cost_idx    = [(m, L, n) for m, n in idx_h_pairs]
            cost_vec_1  = [ item[0] + item[1]  - item[2] for item in cost]
            cost_vec_2  = [(item[0] + item[1]) / (item[2] + 0.00000000000000001) for item in cost]
            x.append(cost_vec_1.index(min(cost_vec_1)))
            y.append(cost_vec_2[x[-1]])
            z.append(cost_idx[x[-1]])
        m, L, n     = z[y.index(min(y))]
        idx_in.remove(L)
        ins         = idx_h.index(m)
        idx_h.insert(ins + 1, L)
        idx_h_pairs = [ (idx_h[i], idx_h[i+1]) for i in range(0, len(idx_h)-1)]
        idx_h_pairs.append((idx_h[-1], idx_h[0]))
    route    = idx_h + [idx_h[0]]
    distance = distance_calc(distance_matrix, [route, 1])
    seed     = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################
