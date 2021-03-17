############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Ant Colony Optimization
 
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

# Function: Initial Attractiveness
def attractiveness(Xdata):
    h = np.zeros((Xdata.shape[0], Xdata.shape[0]))  
    for i in range(0, Xdata.shape[0]):
        for j in range(0, Xdata.shape[1]):
            if (i == j or Xdata[i,j] == 0):
                h[i, j] = 0.000001
            else:
                h[i, j] = 1/Xdata[i,j]   
    return h

# Function: Probability Matrix 
def city_probability(h, thau, city = 0, alpha = 1, beta = 2, city_list = []):
    probability = np.zeros((h.shape[0], 3)) # ['atraction','probability','cumulative_probability']
    for i in range(0, probability.shape[0]):
        if (i+1 not in city_list):
            probability[i, 0] = (thau[i, city]**alpha)*(h[i, city]**beta)
    for i in range(0, probability.shape[0]):
        if (i+1 not in city_list and probability[:,0].sum() != 0):
            probability[i, 1] = probability[i, 0]/probability[:,0].sum()
        if (i == 0):
            probability[i, 2] = probability[i, 1] 
        else:
            probability[i, 2] = probability[i, 1] + probability[i - 1, 2]     
    if (len(city_list) > 0):
        for i in range(0, len(city_list)):
            probability[city_list[i]-1, 2] = 0.0            
    return probability

# Function: Select Next City
def city_selection(probability_matrix, city_list = []):
    random = int.from_bytes(os.urandom(8), byteorder = 'big') / ((1 << 64) - 1)
    city = 0
    for i in range(0, probability_matrix.shape[0]):
        if (random <= probability_matrix[i, 2] and i+1 not in city_list):
          city = i+1
          break     
    return city

# Function: Update Thau
def update_thau(Xdata, thau, city_list = []):
    distance = 0
    for i in range(0, len(city_list)-1):
        j = i + 1
        distance = distance + Xdata[city_list[i]-1,city_list[j]-1] 
    pheromone = 1  
    for i in range(0, len(city_list)-1):
        j = i + 1 
        thau[city_list[i]-1,city_list[j]-1] = thau[city_list[i]-1,city_list[j]-1] + pheromone        
    return thau

# Function: 2_opt
def local_search_2_opt(Xdata, city_tour, recursive_seeding = -1):
    if (recursive_seeding < 0):
        count = -2
    else:
        count = 0
    city_list_new = copy.deepcopy([city_tour[0]])
    city_list_new.append(city_tour[1])
    city_list_old = city_list_new[1]*2
    iteration     = 0
    while (count < recursive_seeding):
        best_route = copy.deepcopy(city_list_new)
        seed       = copy.deepcopy(city_list_new)        
        for i in range(0, len(city_list_new[0]) - 2):
            for j in range(i+1, len(city_list_new[0]) - 1):
                best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
                best_route[0][-1]    = best_route[0][0]              
                best_route[1]        = distance_calc(Xdata, best_route)                     
                if (city_list_new[1] > best_route[1]):
                    city_list_new = copy.deepcopy(best_route)         
                best_route = copy.deepcopy(seed)
        count = count + 1
        iteration = iteration + 1  
        if (city_list_old > city_list_new[1] and recursive_seeding < 0):
             city_list_old = city_list_new[1]
             count         = -2
             recursive_seeding = -1
        elif(city_list_new[1] >= city_list_old and recursive_seeding < 0):
            count = -1
            recursive_seeding = -2
    return city_list_new[0], city_list_new[1]

# Function: Ants City List
def ants_path(Xdata, h, thau, alpha, beta, full_list, ants):
    distance           = np.sum(Xdata.sum())
    best_city_list     = []
    best_path_distance = []
    for ant in range(0, ants):
        city_list = []
        initial   = random.randrange(1, Xdata.shape[0])
        city_list.append(initial)           
        for i in range(0, Xdata.shape[0] - 1):
            probability = city_probability(h, thau, city = i, alpha = alpha, beta = beta, city_list = city_list)
            path_point  = city_selection(probability, city_list = city_list)
            if (path_point == 0):
                path_point = [value for value in full_list if value not in city_list][0]
            city_list.append(path_point)
        city_list.append(city_list[0])
        path_distance = 0
        for i in range(0, len(city_list)-1):
            j = i + 1
            path_distance = path_distance + Xdata[city_list[i]-1,city_list[j]-1] 
        if (distance > path_distance):
            best_city_list     = copy.deepcopy(city_list)
            best_path_distance = path_distance
            distance           = path_distance
    best_route = copy.deepcopy([best_city_list])
    best_route.append(best_path_distance)
    best_city_list, best_path_distance = local_search_2_opt(Xdata, city_tour = best_route, recursive_seeding = -1)
    thau = update_thau(Xdata, thau, city_list = best_city_list)
    return best_city_list, best_path_distance, thau

# ACO Function
def ant_colony_optimization(Xdata, ants = 5, iterations = 50, alpha = 1, beta = 2, decay = 0.05): 
    count       = 0  
    best_route  = [] 
    full_list   = list(range(1, Xdata.shape[0] + 1))
    distance    = np.sum(Xdata.sum())
    h           = attractiveness(Xdata)
    thau        = np.ones((Xdata.shape[0], Xdata.shape[0]))  
    while (count <= iterations):
        if (count > 0):
            print('Iteration = ', count, ' -> Distance = ', best_route[1])            
        city_list, path_distance, thau = ants_path(Xdata, h, thau, alpha, beta, full_list, ants)
        thau = thau*(1 - decay)
        if (distance > path_distance):
            best_route = copy.deepcopy([city_list])
            best_route.append(path_distance)
            distance   = best_route[1]
        count = count + 1    
    print(best_route)       
    return  best_route