############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Extremal Optimization
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy  as np
import random
import os

from matplotlib import pyplot as plt 
plt.style.use('bmh')

############################################################################

# Function: Tour Distance
def distance_calc(Xdata, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m = k + 1
        distance = distance + Xdata[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

# Function: Euclidean Distance 
def euclidean_distance(x, y):       
    distance = 0
    for j in range(0, len(x)):
        distance = (x[j] - y[j])**2 + distance   
    return distance**(1/2) 

# Function: Initial Seed
def seed_function(Xdata):
    seed     = [[],float("inf")]
    sequence = random.sample(list(range(1,Xdata.shape[0]+1)), Xdata.shape[0])
    sequence.append(sequence[0])
    seed[0]  = sequence
    seed[1]  = distance_calc(Xdata, seed)
    return seed

# Function: Build Coordinates
def build_coordinates(distance_matrix):  
    a           = distance_matrix[0,:].reshape(distance_matrix.shape[0], 1)
    b           = distance_matrix[:,0].reshape(1, distance_matrix.shape[0])
    m           = (1/2)*(a**2 + b**2 - distance_matrix**2)
    w, u        = np.linalg.eig(np.matmul(m.T, m))
    s           = (np.diag(np.sort(w)[::-1]))**(1/2) 
    coordinates = np.matmul(u, s**(1/2))
    coordinates = coordinates.real[:,0:2]
    return coordinates

# Function: Build Distance Matrix
def build_distance_matrix(coordinates):
   a = coordinates
   b = a.reshape(np.prod(a.shape[:-1]), 1, a.shape[-1])
   return np.sqrt(np.einsum('ijk,ijk->ij',  b - a,  b - a)).squeeze()

# Function: Add Arrow
def add_arrow(line, direction = 'right', size = 20, color = 'k'):
    if color is None:
        color = line.get_color()
    x = line.get_xdata()
    y = line.get_ydata()
    s_idx = 0
    if direction == 'right':
        e_idx = s_idx + 1
    else:
        e_idx = s_idx - 1
    line.axes.annotate('', xytext = (x[s_idx], y[s_idx]), xy = (x[e_idx], y[e_idx]), arrowprops = dict(arrowstyle = '-|>', color = color), size = size)
    return

# Function: Tour Plot
def plot_tour(Xdata, city_tour = [], size_x = 10, size_y = 10):
    coordinates = 0
    no_lines    = False
    if (Xdata.shape[0] == Xdata.shape[1]):
      coordinates = build_coordinates(Xdata)
      if (len(city_tour) == 0):
        city_tour = seed_function(Xdata)
        no_lines  = True  
    else:
      coordinates = np.copy(Xdata)
      if (len(city_tour) == 0):
        city_tour = seed_function(build_distance_matrix(coordinates))
        no_lines  = True 
    xy = np.zeros((len(city_tour[0]), 2))
    for i in range(0, len(city_tour[0])):
        if (i < len(city_tour[0])):
            xy[i, 0] = coordinates[city_tour[0][i]-1, 0]
            xy[i, 1] = coordinates[city_tour[0][i]-1, 1]
        else:
            xy[i, 0] = coordinates[city_tour[0][0]-1, 0]
            xy[i, 1] = coordinates[city_tour[0][0]-1, 1]
    plt.figure(figsize = [size_x, size_y])
    if (no_lines == True):
      for i in range(0, xy.shape[0]):
        plt.plot(xy[i, 0], xy[i, 1], marker = 's', alpha = 1, markersize = 7, color = 'grey',  linestyle = 'None')
        plt.text(xy[i,0], xy[i,1], 'c-'+str(city_tour[0][i]))
    else: 
      for i in range(0, xy.shape[0]-1):
        line = plt.plot(xy[i:i+2, 0], xy[i:i+2, 1], marker = 's', alpha = 1, markersize = 7, color = 'grey')[0]
        add_arrow(line)
        plt.text(xy[i,0], xy[i,1], 'c-'+str(city_tour[0][i]))
      line = plt.plot(xy[0:2,0], xy[0:2,1], marker = 's', alpha = 1, markersize = 7, color = 'red')[0]
      add_arrow(line, color = 'r')
      plt.plot(xy[1,0], xy[1,1], marker = 's', alpha = 1, markersize = 7, color = 'grey')
    return

############################################################################

# Function: Rank Cities
def ranking(Xdata, city = 0, tau = 1.8):
    rank = np.zeros((Xdata.shape[0], 4))
    for i in range(0, rank.shape[0]):
        rank[i,0] = Xdata[i,city]
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
    fitness = np.zeros((rank.shape[0], 5))
    fitness[:,0]  = city_tour[0][0:-1]
    fitness[:,1]  = city_tour[0][-2:-1] + city_tour[0][0:-2]
    fitness[:,2] = city_tour[0][1:]
    for i in range(0, fitness.shape[0]):
        left  = rank[np.where(rank[:,1] == fitness[i, 1])]
        right = rank[np.where(rank[:,1] == fitness[i, 2])]
        fitness[i, 3] = 3/(left[0,2] + right[0,2])    
        fitness[i, 4] = fitness[i, 3]**(-tau) 
    sum_prob = fitness[:, 4].sum()
    for i in range(0, fitness.shape[0]):
        fitness[i, 4] = fitness[i, 4]/sum_prob
    fitness = fitness[fitness[:,-1].argsort()]
    for i in range(1, fitness.shape[0]):
        fitness[i,4] = fitness[i,4] + fitness[i-1,4]
    ix =  1
    iy = -1 # left
    iz = -1 # rigth
    iw =  1 # change
    rand = int.from_bytes(os.urandom(8), byteorder = "big") / ((1 << 64) - 1)
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
def exchange(Xdata, city_tour, iy = 1, ix = 2, iz = 3, iw = 4):
    best_route = copy.deepcopy(city_tour)    
    tour = copy.deepcopy(city_tour)
    if (iy == -1 and city_tour[0].index(iw) < city_tour[0].index(ix)):
        i = city_tour[0].index(ix) - 1
        j = city_tour[0].index(ix)
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]  = best_route[0][0]   
        i = city_tour[0].index(iw)
        j = city_tour[0].index(ix) - 1
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]  = best_route[0][0] 
        best_route[1] = distance_calc(Xdata, city_tour = best_route)
    elif (iy == -1 and city_tour[0].index(iw) > city_tour[0].index(ix)):  
        i = city_tour[0].index(ix)
        j = city_tour[0].index(iw)
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]  = best_route[0][0] 
        best_route[1] = distance_calc(Xdata, city_tour = best_route)
    elif (iz == -1 and city_tour[0].index(iw) < city_tour[0].index(ix)): 
        i = city_tour[0].index(iw)
        j = city_tour[0].index(ix)
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]  = best_route[0][0] 
        best_route[1] = distance_calc(Xdata, city_tour = best_route)
    elif (iz == -1 and city_tour[0].index(iw) > city_tour[0].index(ix)):  
        i = city_tour[0].index(ix)
        j = city_tour[0].index(ix) + 1
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]  = best_route[0][0]   
        i = city_tour[0].index(ix) + 1
        j = city_tour[0].index(iw)
        best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
        best_route[0][-1]  = best_route[0][0] 
        best_route[1] = distance_calc(Xdata, city_tour = best_route)       
    if (best_route[1] < tour[1]):
        tour[1] = copy.deepcopy(best_route[1])
        for n in range(0, len(tour[0])): 
            tour[0][n] = best_route[0][n]                        
    return tour

# Function: Extremal Optimization
def extremal_optimization(Xdata, city_tour, iterations = 50, tau = 1.8):
    count = 0
    best_solution = copy.deepcopy(city_tour)
    while (count < iterations):
        for i in range(0, Xdata.shape[0]):
            rank = ranking(Xdata, city = i, tau = tau)
            iy, ix, iz, iw = roulette_wheel(rank, city_tour, tau = tau)
            city_tour = exchange(Xdata, city_tour, iy = iy, ix = ix, iz = iz, iw = iw)
        if (city_tour[1] < best_solution[1]):
            best_solution = copy.deepcopy(city_tour) 
        count = count + 1
        city_tour = copy.deepcopy(best_solution)
        print('Iteration = ', count, '-> Distance = ', best_solution[1])
    print('Best Solution = ', best_solution)
    return best_solution