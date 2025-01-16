############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Double Q-Learning
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy as np
import random

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

# Function: Q-Table Init
def initialize_q_table(num_cities, seed):
    if seed is not None:
        np.random.seed(seed) 
    q_table            = np.zeros((num_cities, num_cities))
    num_noisy_elements = int(1 * num_cities * num_cities)
    idx                = np.random.choice(num_cities * num_cities, num_noisy_elements, replace = False)
    noise              = np.random.uniform(-0.01, 0.01, size = num_noisy_elements)
    q_table.flat[idx]  = noise
    return q_table

# Function: Reconstruct Route from Q-Tables
def reconstruct_route(q_table_a, q_table_b, distance_matrix, num_cities):
    start_city     = 0
    current_city   = start_city
    visited        = set([current_city])
    route          = [current_city]
    total_distance = 0
    while (len(visited) < num_cities):
        avg_q_values = (q_table_a[current_city] + q_table_b[current_city]) / 2
        next_city    = np.argmax([avg_q_values[city] if city not in visited else -np.inf for city in range(num_cities)])
        route.append(next_city)
        visited.add(next_city)
        total_distance = total_distance + distance_matrix[current_city, next_city]
        current_city   = next_city
    route.append(start_city)
    total_distance = total_distance + distance_matrix[current_city, start_city]
    return [city + 1 for city in route], total_distance

# Function: Double Q-Learning
def double_q_learning(distance_matrix, learning_rate = 0.1, discount_factor = 0.95, epsilon = 0.15, episodes = 5000, q_init_a = None, q_init_b = None, local_search = True, verbose = True):
    max_dist        = np.max(distance_matrix)
    distance_matrix = distance_matrix / max_dist 
    num_cities      = distance_matrix.shape[0]
    q_table_a       = initialize_q_table(num_cities, q_init_a)
    q_table_b       = initialize_q_table(num_cities, q_init_b)
    for episode in range(0, episodes):
        current_city = random.randint(0, num_cities - 1)
        visited      = set([current_city])
        while (len(visited) < num_cities):
            unvisited_cities = [city for city in range(0, num_cities) if city not in visited]
            if (random.random() < epsilon):
                next_city = random.choice(unvisited_cities)
            else:
                avg_q_values = (q_table_a[current_city] + q_table_b[current_city]) / 2
                next_city    = unvisited_cities[np.argmax(avg_q_values[unvisited_cities])]
            reward = -distance_matrix[current_city, next_city]
            if (random.random() < 0.5):
                max_q_b                            = max(q_table_b[next_city, unvisited_cities]) if unvisited_cities else 0
                q_table_a[current_city, next_city] = q_table_a[current_city, next_city] + learning_rate * (reward + discount_factor * max_q_b - q_table_a[current_city, next_city])
            else:
                max_q_a                            = max(q_table_a[next_city, unvisited_cities]) if unvisited_cities else 0
                q_table_b[current_city, next_city] = q_table_b[current_city, next_city] + learning_rate * (reward + discount_factor * max_q_a - q_table_b[current_city, next_city])
            current_city = next_city
            visited.add(current_city)
        if (verbose and episode % 100 == 0):
            print(f"Episode {episode}")
    distance_matrix = distance_matrix * max_dist
    route, distance = reconstruct_route(q_table_a, q_table_b, distance_matrix, num_cities)
    seed            = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance, q_table_a, q_table_b

############################################################################
