############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Extremal Optimization

# GitHub Repository: <https://github.com/Valdecy> 

############################################################################

# Required Libraries
import numpy  as np
import copy
import os

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

############################################################################

# Function: Rank Cities
def ranking(distance_matrix, city = 0, tau = 1.8):
    rank = np.zeros((distance_matrix.shape[0], 4))
    for i in range(0, rank.shape[0]):
        rank[i,0] = distance_matrix[i,city]
        rank[i,1] = i + 1
    rank = rank[rank[:,0].argsort()]
    for i in range(0, rank.shape[0]):
        rank[i,2] = i
        if (i> 0):
            rank[i,3] = i**(-tau)
    sum_prob = rank[:, 3].sum()
    for i in range(0, rank.shape[0]):
        rank[i, 3] = rank[i, 3]/sum_prob
    rank = rank[rank[:,-1].argsort()]
    for i in range(1, rank.shape[0]):
        rank[i,3] = rank[i,3] + rank[i-1,3]
    return rank

# Function: Selection
def roulette_wheel(rank, city_tour, tau = 1.8):
    fitness       = np.zeros((rank.shape[0], 5))
    fitness[:,0]  = city_tour[0][0:-1]
    fitness[:,1]  = city_tour[0][-2:-1] + city_tour[0][0:-2]
    fitness[:,2]  = city_tour[0][1:]
    for i in range(0, fitness.shape[0]):
        left          = rank[np.where(rank[:,1] == fitness[i, 1])]
        right         = rank[np.where(rank[:,1] == fitness[i, 2])]
        fitness[i, 3] = 3/(left[0,2] + right[0,2])    
        fitness[i, 4] = fitness[i, 3]**(-tau) 
    sum_prob = fitness[:, 4].sum()
    for i in range(0, fitness.shape[0]):
        fitness[i, 4] = fitness[i, 4]/sum_prob
    fitness = fitness[fitness[:,-1].argsort()]
    for i in range(1, fitness.shape[0]):
        fitness[i,4] = fitness[i,4] + fitness[i-1,4]
    ix   =  1
    iy   = -1 # left
    iz   = -1 # rigth
    iw   =  1 # change
    rand = int.from_bytes(os.urandom(8), byteorder = 'big') / ((1 << 64) - 1)
    for i in range(0, fitness.shape[0]):
        if (rand <= fitness[i, 4]):
          ix    = fitness[i, 0]
          iw    = fitness[i, 0]
          left  = rank[np.where(rank[:,1] == fitness[i, 1])]
          right = rank[np.where(rank[:,1] == fitness[i, 2])]
          if (left[0,0] > right[0,0]):
              iy = fitness[i, 1]
              iz = -1
          else:
              iy = -1
              iz = fitness[i, 2]              
          break
    while (ix == iw):
        rand = int.from_bytes(os.urandom(8), byteorder = "big") / ((1 << 64) - 1)
        for i in range(0, rank.shape[0]):
            if (rand <= rank[i, 3]):
              iw = fitness[i, 0]
              break      
    return iy, ix, iz, iw

# Function: Exchange
def exchange(distance_matrix, city_tour, iy = 1, ix = 2, iz = 3, iw = 4):
    best_route = copy.deepcopy(city_tour)    
    tour       = copy.deepcopy(city_tour)
    if (iy == -1 and city_tour[0].index(iw) < city_tour[0].index(ix)):
        i                    = city_tour[0].index(ix) - 1
        j                    = city_tour[0].index(ix)
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]    = best_route[0][0]   
        i = city_tour[0].index(iw)
        j = city_tour[0].index(ix) - 1
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]    = best_route[0][0] 
        best_route[1]        = distance_calc(distance_matrix, city_tour = best_route)
    elif (iy == -1 and city_tour[0].index(iw) > city_tour[0].index(ix)):  
        i                    = city_tour[0].index(ix)
        j                    = city_tour[0].index(iw)
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]    = best_route[0][0] 
        best_route[1]        = distance_calc(distance_matrix, city_tour = best_route)
    elif (iz == -1 and city_tour[0].index(iw) < city_tour[0].index(ix)): 
        i                    = city_tour[0].index(iw)
        j                    = city_tour[0].index(ix)
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]    = best_route[0][0] 
        best_route[1]        = distance_calc(distance_matrix, city_tour = best_route)
    elif (iz == -1 and city_tour[0].index(iw) > city_tour[0].index(ix)):  
        i                    = city_tour[0].index(ix)
        j                    = city_tour[0].index(ix) + 1
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]    = best_route[0][0]   
        i = city_tour[0].index(ix) + 1
        j = city_tour[0].index(iw)
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]    = best_route[0][0] 
        best_route[1]        = distance_calc(distance_matrix, city_tour = best_route)       
    if (best_route[1] < tour[1]):
        tour[1] = copy.deepcopy(best_route[1])
        for n in range(0, len(tour[0])): 
            tour[0][n] = best_route[0][n]                        
    return tour

############################################################################

# Function: Extremal Optimization
def extremal_optimization(distance_matrix, city_tour, iterations = 50, tau = 1.8, verbose = True):
    count         = 0
    best_solution = copy.deepcopy(city_tour)
    while (count < iterations):
        if (verbose == True):
            print('Iteration = ', count, 'Distance = ', round(best_solution[1], 2))  
        for i in range(0, distance_matrix.shape[0]):
            rank           = ranking(distance_matrix, city = i, tau = tau)
            iy, ix, iz, iw = roulette_wheel(rank, city_tour, tau = tau)
            city_tour      = exchange(distance_matrix, city_tour, iy = iy, ix = ix, iz = iz, iw = iw)
        if (city_tour[1] < best_solution[1]):
            best_solution = copy.deepcopy(city_tour) 
        count     = count + 1
        city_tour = copy.deepcopy(best_solution)
    route, distance = best_solution
    return route, distance

############################################################################
