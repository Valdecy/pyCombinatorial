############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Hopfield Network
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy as np
import random

###############################################################################

# Function: Initial Seed
def seed_function(distance_matrix):
    seed     = [[], float('inf')]
    sequence = random.sample(list(range(1, distance_matrix.shape[0]+1)), distance_matrix.shape[0])
    sequence.append(sequence[0])
    seed[0]  = sequence
    seed[1]  = distance_calc(distance_matrix, seed)
    return seed

###############################################################################

# Function: Encoder
def encoder(seed):
    r, d = seed
    u    = np.zeros((len(r)-1, len(r)-1))
    for i in range(0, len(r[:-1])):
        j       = r[i] - 1
        u[j, i] = 1
    return u

# Function: Decoder
def decoder(u, distance_matrix):
    route = np.where(u == 1)[1].tolist()
    if (len(route) == 0):
        route = np.argmax(u, axis = 1).tolist()
    route = [item for item in route if route.count(item) == 1]
    route = [route.index(item) for item in range(0, len(route)) if item in route]
    if (len(route) < distance_matrix.shape[0]):
        complete = list(range(0, distance_matrix.shape[0]))
        complete = [item for item in complete if item not in route]
        route    = route + complete       
    route    = route + [route[0]]
    route    = [item+1 for item in route]
    distance = distance_calc(distance_matrix, [route, 1])
    return route, distance

###############################################################################

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

# Function: Update Neurons
def update_neurons(u, A, B, C, D, alpha, sigma, dist_m):
    n = dist_m.shape[0]
    for iteration in range(0, n**2):
        x       = random.randint(0, n - 1)
        i       = random.randint(0, n - 1)
        A_      = 0
        mask    = np.ones(u[x, :].shape, dtype = bool)
        mask[i] = False
        A_      = A_ + np.sum(u[x, mask])
        A_      = A_ * (-A)
        B_      = 0
        mask    = np.ones(u[x, :].shape, dtype = bool)
        mask[x] = False
        B_      = B_ + np.sum(u[mask, i])
        B_      = B_ * (-B)
        C_      = 0
        C_      = C_ + np.sum(u)
        C_      = C_ - (n + sigma)
        C_      = C_ * (-C)
        D_      = 0
        for y in range(0, n):
            if (0 < i < n - 1):
                D_ = D_ + dist_m[x, y] * (u[y, i-1] + u[y, i+1])
            elif (i == 0):
                D_ = D_ + dist_m[x, y] * (u[y,  -1] + u[y, i+1])
            elif (i == n - 1):
                D_ = D_ + dist_m[x, y] * (u[y, i-1] + u[y,   0])
        D_      = D_ * (-D)
        u[x, i] = 0.5*( 1.0 + np.tanh(alpha * (A_ + B_ + C_ + D_)))
    return u

# Function: Error Function
#def e_function(u, A, B, C, D, sigma, dist_m):
    #A_ = 0
    #n  = dist_m.shape[0]
    #for x in range(0, n):
        #for i in range(0, n):
            #for j in range(0, n):
                #if (i != j):
                    #A_ = A_ + u[x, i] * u[x, j]
    #A_ = A_ * (A/2.0)
    #B_ = 0
    #for i in range(0, n):
        #for x in range(0, n):
           # for y in range(0, n):
                #if (x != y):
                    #B_ = B_ + u[x, i] * u[y, i]
    #B_ = B_ * (B/2.0)
    #C_ = 0
    #for x in range(0, n):
        #for i in range(0, n):
            #C_ = C_ + u[x, i]
    #C_ = C_ - ((n + sigma)**2)
    #C_ = C_ * (C/2.0)
    #D_ = 0
    #for x in range(0, n):
        #for y in range(0, n):
            #for i in range(0, n):
                #if (0 < i < n - 1):
                    #D_ = D_ + dist_m[x, y] * u[x, i] * (u[y, i+1] + u[y, i-1])
                #elif (i == 0):
                    #D_ = D_ + dist_m[x, y] * (u[y, -1] + u[y, i+1])
                #elif (i == n - 1):
                    #D_ = D_ + dist_m[x, y] * (u[y, i-1] + u[y, 0])
    #D_ = D_ * (D/2.0)
    #t  = A_ + B_ + C_ + D_
    #return t

############################################################################

# Function: Hopfield Network  
def hopfield_network_tsp(distance_matrix, alpha = 50, sigma = 1, A = 100, B = 100, C = 90, D = 100, trials = 25, iterations = 1500, local_search = True, verbose = True):
    count     = 0
    rep       = 0
    n         = distance_matrix.shape[0]
    mask      = np.ones(distance_matrix.shape, dtype = bool)
    np.fill_diagonal(mask, 0)
    max_value = distance_matrix[mask].max()
    min_value = distance_matrix[mask].min()
    dist_m    = (distance_matrix - min_value) / (max_value - min_value + 0.0000000000000001)
    np.fill_diagonal(dist_m, 0)
    sol_r     = []
    sol_d     = []
    u         = np.random.uniform(low = 0.0, high = 0.03, size = (n, n))
    if (local_search == True):
        r, d = decoder(u, distance_matrix)
        r, d = local_search_2_opt(distance_matrix, [r, d], recursive_seeding = -1, verbose = False)
        u    = encoder([r, d])
    while (count < iterations):
        row = np.sum(u, axis = 0)
        col = np.sum(u, axis = 1)
        if (np.all(row == 1) and np.all(col == 1)):   
            r, d = decoder(u, distance_matrix)
            if (local_search == True):
                r, d = local_search_2_opt(distance_matrix, [r, d], recursive_seeding = -1, verbose = False)
                u    = encoder([r, d])
            sol_r.append(r)
            sol_d.append(d)
            if (verbose == True):
                print('Iteration = ', count, ' Distance = ', round(min(sol_d), 2))
            if (r == sol_r[-1]):
                rep = rep + 1
                if (rep > trials):
                    rep = 0
                    u   = np.random.uniform(low = 0.0, high = 0.03, size = (n, n))
                    if (local_search == True):
                        r, d = decoder(u, distance_matrix)
                        r, d = local_search_2_opt(distance_matrix, [r, d], recursive_seeding = -1, verbose = False)
                        u    = encoder([r, d])
                        sol_r.append(r)
                        sol_d.append(d)
        else:
            if (verbose == True):
                if (len(sol_d) > 0):
                    print('Iteration = ', count, ' Distance = ', round(min(sol_d), 2))
                else:
                    print('Iteration = ', count, ' Distance = No Convergence')
            rep = rep + 1
            if (rep > trials):
                rep  = 0
                u    = np.random.uniform(low = 0.0, high = 0.03, size = (n, n))
                if (local_search == True):
                    r, d = decoder(u, distance_matrix)
                    r, d = local_search_2_opt(distance_matrix, [r, d], recursive_seeding = -1, verbose = False)
                    u    = encoder([r, d])
                    sol_r.append(r)
                    sol_d.append(d)
        u     = update_neurons(u, A, B, C, D, alpha, sigma, dist_m)
        r, d  = decoder(u, distance_matrix)
        u     = encoder([r, d])
        count = count + 1
    if (len(sol_d) > 0):
        idx             = sol_d.index(min(sol_d))
        route, distance = sol_r[idx], sol_d[idx]
    else:
        if (verbose == True):
            print('Reparing Solution...')
            print('')
        route, distance = decoder(u, distance_matrix)
        route, distance = local_search_2_opt(distance_matrix, [route, distance], recursive_seeding = -1, verbose = False)
        if (verbose == True):
            print('Distance = ', round(distance, 2))
    return route, distance

############################################################################