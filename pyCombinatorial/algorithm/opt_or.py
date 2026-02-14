############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Or-Opt
#
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

# Function: Insertion
def insertion(city_tour, distance_matrix, chain_length = 5, k_min = 1, k_max = 10, lambda_val = 0.1, vf_mode = True):

    # -------------------------------------------------------------------------

    def total_distance(dist_mat, route_idxs):
        total = 0.0
        for idx in range(1, len(route_idxs)):
            total = total + dist_mat[route_idxs[idx - 1]][route_idxs[idx]]
        return total

    # -------------------------------------------------------------------------

    route = copy.deepcopy(city_tour[0])
    if route[0] != route[-1]:
        route = route + [route[0]]
    current_distance = total_distance(distance_matrix, route)
    n                = len(route) - 1  
    if isinstance(distance_matrix, np.ndarray):
        if distance_matrix.ndim != 2 or distance_matrix.shape[0] != distance_matrix.shape[1]:
            raise ValueError("distance_matrix must be a square 2D array.")
        if n <= 1:
            avg_graph_cost = 1.0
        else:
            avg_graph_cost = distance_matrix[np.triu_indices(n, k=1)].mean()
            if not np.isfinite(avg_graph_cost) or avg_graph_cost <= 0:
                avg_graph_cost = 1.0
    else:
        if n <= 1:
            avg_graph_cost = 1.0
        else:
            s   = 0.0
            cnt = 0
            for a in range(n):
                for b in range(a + 1, n):
                    s   = s + distance_matrix[a][b]
                    cnt = cnt + 1
            avg_graph_cost = s / cnt if cnt else 1.0

    k_sequence = list(range(int(k_max), int(k_min) - 1, -1))
    max_passes = max(1, int(chain_length))
    for _pass in range(0, max_passes):
        improved_any = False
        if vf_mode:
            for i in range(1, len(route) - 1):
                for k in k_sequence:         
                    if i + k >= len(route):
                        continue
                    i1, i2 = route[i - 1], route[i]
                    i3, i4 = route[i + k - 1], route[i + k]
                    g      = (distance_matrix[i1][i2] +
                              distance_matrix[i3][i4] -
                              distance_matrix[i1][i4])
                    d_bar  = current_distance / max(1, n)
                    l_bar  = (2.0 * avg_graph_cost) - d_bar
                    if g <= lambda_val * l_bar:
                        continue
                    segment = route[i:i + k]
                    rem     = route[:i] + route[i + k:]
                    moved   = False
                    for j in range(1, len(rem)):
                        temp = rem[:j] + segment + rem[j:]
                        cost = total_distance(distance_matrix, temp)
                        if cost + 1e-12 < current_distance:
                            route            = temp
                            current_distance = cost
                            improved_any     = True
                            moved            = True
                            break  
                    if moved:
                        break
        else:
            for k in k_sequence:
                improved_k = True
                while improved_k:
                    improved_k = False
                    last_idx   = len(route) - 1
                    for i in range(1, last_idx):
                        if i + k > last_idx:
                            continue
                        i1, i2 = route[i - 1], route[i]
                        i3, i4 = route[i + k - 1], route[i + k]
                        g      = (distance_matrix[i1][i2] +
                                  distance_matrix[i3][i4] -
                                  distance_matrix[i1][i4])
                        d_bar  = current_distance / max(1, n)
                        l_bar  = (2.0 * avg_graph_cost) - d_bar
                        if g <= lambda_val * l_bar:
                            continue
                        segment = route[i:i + k]
                        rem     = route[:i] + route[i + k:]
                        for j in range(1, len(rem)):
                            temp = rem[:j] + segment + rem[j:]
                            cost = total_distance(distance_matrix, temp)
                            if cost + 1e-12 < current_distance:
                                route            = temp
                                current_distance = cost
                                improved_k       = True
                                improved_any     = True
                                break  
                        if improved_k:
                            break  
        if not improved_any:
            break
    return route, current_distance

# Function: Or - Opt
def local_search_or_opt(city_tour, distance_matrix, iterations = 100, chain_length = 3, k1 = 1, k2 = 5, lbd = 0.1, vf = True, local_search = True, verbose = True):
    route      = city_tour[0]
    distance   = city_tour[1]
    route      = [item - 1 for item in route]
    no_improve = 0
    for i in range(0, iterations):
        new_route, new_distance = insertion([route, distance], distance_matrix, chain_length, k1, k2, lbd, vf)
        if new_distance < distance:
            route      = copy.deepcopy(new_route)
            distance   = new_distance
            no_improve = 0  
        else:
            no_improve = no_improve + 1
        if no_improve >= 2:
            break  
        if (verbose == True):
            print('Iteration = ', i, 'Distance = ', round(distance, 2)) 
    route = [item + 1 for item in route]
    if (local_search == True):
        print('')
        print('Local Search:')
        route, distance = local_search_2_opt(distance_matrix, [route, distance], recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################