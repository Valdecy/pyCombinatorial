############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Sweep Algorithm
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy as np
np.seterr(divide = 'ignore', invalid = 'ignore')

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

# Function: Transform Cartesian to Polar (radians, degrees)
def cartesian_polar(distance_matrix, coordinates, initial = 0):
    x     = coordinates[:,0]
    y     = coordinates[:,1]
    rho   = np.array([distance_matrix[initial, j] for j in range(0, distance_matrix .shape[0])])
    phi   = np.arctan( (y - y[initial])/(x - x[initial]))
    phi   = np.nan_to_num(phi)
    polar = np.concatenate((rho.reshape(-1, 1), phi.reshape(-1, 1)), axis = 1)
    return polar

#def cartesian_polar(coordinates):
    #x     = coordinates[:,0]
    #y     = coordinates[:,1]
    #z     = x + y * 1j
    #rho   = np.abs(z)
    #phi   = np.angle(z)
    #polar = np.concatenate((rho.reshape(-1, 1), phi.reshape(-1, 1)), axis = 1)
    #return polar
    
#def polar_cartesian(polar):
    #rho       = polar[:,0]
    #phi       = polar[:,1]
    #z         = rho * np.exp(1j * phi)
    #x         = z.real
    #y         = z.imag
    #cartesian = np.concatenate((x.reshape(-1, 1), y.reshape(-1, 1)), axis = 1)
    #return cartesian

############################################################################

# Function: Sweep
def sweep(coordinates, distance_matrix, initial_location = -1, verbose = True):
    minimum  = float('+inf')
    distance = float('+inf')
    nodes    = np.array([i+1 for i in range(0, distance_matrix.shape[0])])
    route    = []
    for i in range(0, distance_matrix.shape[0]): 
        if (initial_location != -1):
            i = initial_location-1
        polar = cartesian_polar(distance_matrix, coordinates, initial = i)
        polar = np.c_[polar, nodes]
        polar = polar[polar[:, 1].argsort()]
        temp  = [int(polar[i,-1]) for i in range(0, distance_matrix.shape[0])]
        temp  = temp + [temp[0]]
        dist  = distance_calc(distance_matrix, [temp, 1])
        seed  = [temp, dist]
        r, d  = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = False)
        if (d < minimum):
            minimum  = d
            distance = d
            route    = [item for item in r]
        if (verbose == True):
            print('Iteration = ', i, 'Distance = ', round(distance, 2))
        if (initial_location == -1):
            continue
        else: 
            break
    return route, distance

############################################################################