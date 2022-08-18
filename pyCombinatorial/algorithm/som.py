############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: SOM (Self Organizing Maps)
 
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

# Function: Select Nearest Neuron
def select_neuron(neurons, individual):
    idx = np.linalg.norm(neurons - individual, axis = 1).argmin()
    return idx

# Function: Update Neurons
def update_neurons(neurons, n_coord, idx, nr, learning_rate, individual):
    radius  = np.clip(nr//10, 1, n_coord.shape[0]//10)
    delt    = np.absolute(idx - np.arange(neurons.shape[0]))
    dist    = np.minimum(delt, neurons.shape[0] - delt)
    noise   = np.exp(-(dist**2) / (2*(radius**2)))
    noise   = noise.reshape((-1, 1))
    neurons = neurons + noise * learning_rate * (individual - neurons)
    return neurons

############################################################################

# Function: SOM (adapted from https://github.com/diego-vicente/som-tsp)
def self_organizing_maps(coordinates, distance_matrix, size_multiplier = 4, iterations = 25000, decay_nr = 0.99997, decay_lr = 0.99997, learning_rate = 0.80, local_search = True, verbose = True):
    n_coord = (coordinates - np.min(coordinates)) / (np.max(coordinates) - np.min(coordinates) + 0.0000000000000001)
    neurons = np.random.rand(n_coord.shape[0]*size_multiplier, 2)
    nr      = n_coord.shape[0] 
    lr      = learning_rate
    count   = 0
    while (count <= iterations): 
        if (verbose == True):
            print('Iteration = ', count)
        individual = n_coord[np.random.randint(n_coord.shape[0], size = 1)[0],:]
        idx        = select_neuron(neurons, individual)
        neurons    = update_neurons(neurons, n_coord, idx, nr, lr, individual)
        lr         = lr * decay_lr
        nr         = nr * decay_nr
        if (nr < 1):
            count = iterations + 1
            print('Radius has Completely Decayed')
        if (lr  < 0.001):
            count = iterations + 1
            print('Learning Rate has Completely Decayed')
        count = count + 1
    selected = []
    route    = list(range(0, n_coord.shape[0]))
    for i in range(0, n_coord.shape[0]):
        selected.append(select_neuron(neurons, n_coord[i,:]))
    idx      = sorted(range(0, len(selected)), key = selected.__getitem__)
    route    = [route[i]  for i in idx]
    route    = route + [route[0]]
    route    = [node + 1 for node in route]
    distance = distance_calc(distance_matrix, [route, 1])
    seed     = [route, distance]
    if (verbose == True):
        print('')
        print('Distance = ', round(distance, 2))
        print('')
    if (local_search == True):
        if (verbose == True):
            print('Local Search...')
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = False)
        if (verbose == True):
            print('Distance = ', round(distance, 2) )
    return route, distance

############################################################################
