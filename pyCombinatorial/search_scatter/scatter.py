############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Scatter Search
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy  as np
import random
import os

from matplotlib import pyplot as plt 
plt.style.use('bmh')
from operator import itemgetter

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

# Function: Crossover
def crossover_tsp(Xdata, reference_list, reverse_prob = 0.5, scramble_prob = 0.3):
    ix, iy = random.sample(list(range(0,len(reference_list))), 2)
    parent_1 = reference_list[ix][0]
    parent_1 = parent_1[:-1]
    parent_2 = reference_list[iy][0]
    parent_2 = parent_2[:-1]
    offspring = [0]*len(parent_2)
    child = [[],float("inf")]
    i, j = random.sample(list(range(0,len(parent_1))), 2)
    if (i > j):
        i, j = j, i
    rand_1 = int.from_bytes(os.urandom(8), byteorder = "big") / ((1 << 64) - 1)
    if (rand_1 < reverse_prob):
        parent_1[i:j+1] = list(reversed(parent_1[i:j+1]))
    offspring[i:j+1] = parent_1[i:j+1]
    parent_2 = [x for x in parent_2 if x not in parent_1[i:j+1]]
    rand_2 = int.from_bytes(os.urandom(8), byteorder = "big") / ((1 << 64) - 1)
    if (rand_2 < scramble_prob):
        random.shuffle(parent_2)
    count = 0
    for i in range(0, len(offspring)):
        if (offspring[i] == 0):
            offspring[i] = parent_2[count]
            count = count + 1
    offspring.append(offspring[0])
    child[0] = offspring
    child[1] = distance_calc(Xdata, child)
    return child

# Function: Local Improvement 2_opt
def local_search_2_opt(Xdata, city_tour):
    city_list = copy.deepcopy(city_tour)
    best_route = copy.deepcopy(city_list)
    seed = copy.deepcopy(city_list)        
    for i in range(0, len(city_list[0]) - 2):
        for j in range(i+1, len(city_list[0]) - 1):
            best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
            best_route[0][-1]  = best_route[0][0]                          
            best_route[1] = distance_calc(Xdata, best_route)           
            if (best_route[1] < city_list[1]):
                city_list[1] = copy.deepcopy(best_route[1])
                for n in range(0, len(city_list[0])): 
                    city_list[0][n] = best_route[0][n]          
            best_route = copy.deepcopy(seed) 
    return city_list

# Function: Scatter Search
def scatter_search(Xdata, city_tour, iterations = 50, reference_size = 25, reverse_prob = 0.5, scramble_prob = 0.3):
    count = 0
    best_solution = copy.deepcopy(city_tour)
    reference_list = []
    for i in range(0, reference_size):
        reference_list.append(seed_function(Xdata))   
    while (count < iterations):            
        candidate_list = []
        for i in range(0, reference_size):
            candidate_list.append(crossover_tsp(Xdata, reference_list = reference_list, reverse_prob = reverse_prob, scramble_prob = scramble_prob))          
        for i in range(0, reference_size):
            candidate_list[i] = local_search_2_opt(Xdata, city_tour = candidate_list[i])
        for i in range(0, reference_size):        
            reference_list.append(candidate_list[i])
        reference_list = sorted(reference_list, key = itemgetter(1))
        reference_list = reference_list[:reference_size]
        for i in range(0, reference_size):
            if (reference_list[i][1] < best_solution[1]):
                best_solution = copy.deepcopy(reference_list[i]) 
        count = count + 1
        print('Iteration =', count, '-> Distance =', best_solution[1])
    print('Best Solution =', best_solution)
    return best_solution
