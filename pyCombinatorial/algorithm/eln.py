############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Elastic Net
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy as np

############################################################################

# Function: Decoder  
def decoder(ds):
    dx       = np.copy(ds)
    nc_pairs = []
    for i in range(0, dx.shape[0]):
        c       = dx.min(axis = 1).argmin()
        n       = dx[c,:].argmin()
        dx[c,:] = float('+inf')
        dx[:,n] = float('+inf')
        nc_pairs.append((n, c))
    nc_pairs.sort(key = lambda x: x[0])
    route = [x[1] for x in nc_pairs]
    route = route + [route[0]]
    route = [item+1 for item in route]
    return route

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

# Function: Initial Neurons
def initial_neurons(coordinates, n_neurons, radius):
    theta    = np.linspace(0, 2 * np.pi, n_neurons, False)
    centroid = coordinates.mean(axis = 0)
    neurons  = np.vstack((np.cos(theta), np.sin(theta)))
    neurons  = neurons * radius
    neurons  = neurons + centroid[:, np.newaxis]
    neurons  = neurons.T
    return neurons

 # Function: Update Weights 
def update_weights(coordinates, neurons, k):
    dt = coordinates[:, np.newaxis] - neurons
    ds = np.sum((dt**2), axis = 2)
    ws = np.exp(-ds / (2 * (k ** 2)))
    sr = ws.sum(axis = 1)
    ws = ws / sr[:, np.newaxis]
    return ds, dt, ws

############################################################################

# Function: Elastic Net (Adapted from: https://github.com/larose/ena)
def elastic_net_tsp(coordinates, distance_matrix, alpha = 0.2, beta = 2.0, k = 0.2, learning_rate = 0.99, learning_upt = 25, iterations = 7000, n_neurons = 100, radius = 0.1, local_search = True, verbose = True):
    n_neurons = int(max(2.5*coordinates.shape[0], n_neurons))
    k1        = k
    max_value = coordinates.max()
    min_value = coordinates.min()
    coords    = (coordinates - min_value) / (max_value - min_value + 0.0000000000000001)
    neurons   = initial_neurons(coords, n_neurons, radius)
    count     = 0
    route     = []
    distance  = float('+inf')
    d         = float('+inf')
    while (count <= iterations):
        if (verbose == True):
            print('Iteration = ', count, ' Distance = ', round(distance, 2))
        if (count % learning_upt == 0 and count > 0):
            k1 = max(0.01, k1 * learning_rate)
        ds, dt, ws = update_weights(coords, neurons, k1)
        D_force    = np.array([np.dot(ws[:,i], dt[:,i]) for i in range(0, n_neurons)])
        L_force    = np.concatenate((
                                      [ neurons[1]   - 2 * neurons[0]           + neurons[n_neurons-1] ], 
                                      [(neurons[i+1] - 2 * neurons[i]           + neurons[i-1]) for i in range(1, n_neurons-1) ], 
                                      [ neurons[0]   - 2 * neurons[n_neurons-1] + neurons[n_neurons-2] ] 
                                    ))
        neurons    = neurons + alpha * D_force + beta * k1 * L_force
        count      = count + 1
        r          = decoder(ds)
        d          = distance_calc(distance_matrix, [r, 1])
        if (d < distance):
            route    = [item for item in r]
            distance = d
    if (local_search == True):
        print('')
        print('Local Search...')
        print('')
        seed            = [route, distance]
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################
