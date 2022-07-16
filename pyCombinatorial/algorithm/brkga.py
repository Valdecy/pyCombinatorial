############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: BRKGA (Biased Random Key Genetic Algorithm)
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import numpy  as np
import random
import os

############################################################################

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

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

############################################################################

# Function: Initialize Variables
def initial_population(population_size, min_values, max_values):
    population = np.zeros((population_size, len(min_values)))
    for i in range(0, population_size):
        for j in range(0, len(min_values)):
             population[i,j] = random.uniform(min_values[j], max_values[j]) 
    return population

# Function: Offspring
def breeding(population, elite, elite_rate):
    offspring = np.copy(population)
    for i in range (elite, offspring.shape[0]):
        parent_1 = random.sample(range(0, elite), 1)[0]
        parent_2 = random.sample(range(elite, len(population) - 1), 1)[0]
        for j in range(0, offspring.shape[1]):
            rand = int.from_bytes(os.urandom(8), byteorder = 'big') / ((1 << 64) - 1)                                
            if (rand <= elite_rate):
                offspring[i,j] = population[parent_1, j]
            else:
                offspring[i,j] = population[parent_2, j]
    return offspring
 
# Function: Mutation
def mutation(offspring, mutants, min_values, max_values):
    mutated = initial_population(mutants, min_values, max_values)
    offspring[offspring.shape[0]-mutated.shape[0]:, :] = mutated
    return offspring

############################################################################

# BRKGA Function
def biased_random_key_genetic_algorithm(distance_matrix, population_size = 250, elite = 50, elite_rate = 0.5, mutants = 50, generations = 5000, verbose = True): 
    count      = 0
    min_values = [0]*distance_matrix.shape[0]
    max_values = [1]*distance_matrix.shape[0]
    population = initial_population(population_size, min_values, max_values)
    cost       = [decoder(population[i,:].tolist(), distance_matrix, cost_only = True) for i in range(0, population.shape[0])]   
    idx        = sorted(range(0, len(cost)), key = cost.__getitem__)
    cost       = [cost[i] for i in idx]
    population = population[idx,:]
    elite_ind  = [population[0,:], cost[0]]
    while (count <= generations):  
        if (verbose == True):
            print('Generation = ', count, 'Distance = ', round(elite_ind[1], 2))  
        offspring  = breeding(population, elite, elite_rate) 
        offspring  = mutation(offspring, mutants, min_values, max_values)
        cost       = [decoder(offspring[i,:].tolist(), distance_matrix, cost_only = True) for i in range(0, offspring.shape[0])] 
        idx        = sorted(range(0, len(cost)), key = cost.__getitem__)
        cost       = [cost[i] for i in idx]
        population = offspring[idx,:]
        if(elite_ind[1] > cost[0]):
            elite_ind = [population[0,:], cost[0]]
        count = count + 1 
    route, distance = decoder(elite_ind[0].tolist(), distance_matrix, cost_only = False)
    return route, distance

############################################################################
