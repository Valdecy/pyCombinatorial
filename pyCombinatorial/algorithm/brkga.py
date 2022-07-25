############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: BRKGA (Biased Random Key Genetic Algorithm)
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy  as np
import random
import os

############################################################################

# Function: Encoder
def encoder(seed):
    route      = seed[0][:-1]
    route      = [item - 1 for item in route]
    individual = [item - 1 for item in route]
    count      = 0
    for item in route:
        individual[item] = count*(1/len(route))
        count            = count + 1
    return individual

# Function: Decoder
def decoder(individual, distance_matrix, cost_only = False):
    dec      = sorted(range(0, len(individual)), key = individual.__getitem__)
    dec      = [item + 1 for item in dec]
    route    = dec + [dec[0]]
    distance = distance_calc(distance_matrix, [route, 1])
    if (cost_only == True):
        return distance
    else:
        return route, distance

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

# Function: Elite Local Search
def elite_ls(population, distance_matrix, elite):
    print('Preparing Elite...')
    for i in range(0, elite):
        idx             = random.sample(range(0, len(population) - 1), 1)[0]
        r, d            = decoder(population[idx], distance_matrix, cost_only = False)
        seed            = [r, d]
        r, d            = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = False)
        seed            = [r, d]
        population[idx] = encoder(seed)
    return population

############################################################################

# Function: Initialize Variables
def initial_population(population_size, min_values, max_values):
    population = np.zeros((population_size, len(min_values)))
    for i in range(0, population_size):
        for j in range(0, len(min_values)):
             population[i,j] = random.uniform(min_values[j], max_values[j]) 
    return population

# Function: Offspring
def breeding(population, elite, bias):
    offspring = np.copy(population)
    for i in range (elite, offspring.shape[0]):
        parent_1 = random.sample(range(0, elite), 1)[0]
        parent_2 = random.sample(range(elite, len(population) - 1), 1)[0]
        for j in range(0, offspring.shape[1]):
            rand = int.from_bytes(os.urandom(8), byteorder = 'big') / ((1 << 64) - 1)                                
            if (rand <= bias):
                offspring[i,j] = population[parent_1, j]
            else:
                offspring[i,j] = population[parent_2, j]
    return offspring
 
# Function: Mutation
def mutation(population, mutants, min_values, max_values):
    mutated = initial_population(mutants, min_values, max_values)
    population[population.shape[0]-mutated.shape[0]:, :] = mutated
    return population

############################################################################

# BRKGA Function
def biased_random_key_genetic_algorithm(distance_matrix, population_size = 25, elite = 1, bias = 0.5, mutants = 10, generations = 50000, verbose = True): 
    count      = 0
    min_values = [0]*distance_matrix.shape[0]
    max_values = [1]*distance_matrix.shape[0]
    population = initial_population(population_size, min_values, max_values)
    population = elite_ls(population, distance_matrix, 1)
    cost       = [decoder(population[i,:].tolist(), distance_matrix, cost_only = True) for i in range(0, population.shape[0])]   
    idx        = sorted(range(0, len(cost)), key = cost.__getitem__)
    cost       = [cost[i] for i in idx]
    population = population[idx,:]
    elite_ind  = [population[0,:], cost[0]]
    while (count <= generations):  
        if (verbose == True):
            print('Generation = ', count, 'Distance = ', round(elite_ind[1], 2))  
        offspring  = breeding(population, elite, bias) 
        cost       = [decoder(offspring[i,:].tolist(), distance_matrix, cost_only = True) for i in range(0, offspring.shape[0])] 
        idx        = sorted(range(0, len(cost)), key = cost.__getitem__)
        cost       = [cost[i] for i in idx]
        population = offspring[idx,:]
        population = mutation(population, mutants, min_values, max_values)
        if(elite_ind[1] > cost[0]):
            elite_ind = [population[0,:], cost[0]]
        count = count + 1 
    route, distance = decoder(elite_ind[0].tolist(), distance_matrix, cost_only = False)
    return route, distance

############################################################################
