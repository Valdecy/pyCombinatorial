############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Guided Search
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy  as np
import random

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

# Function: Stochastic 2_opt
def stochastic_2_opt(Xdata, city_tour):
    best_route = copy.deepcopy(city_tour)      
    i, j  = random.sample(range(0, len(city_tour[0])-1), 2)
    if (i > j):
        i, j = j, i
    best_route[0][i:j+1] = list(reversed(best_route[0][i:j+1]))           
    best_route[0][-1]  = best_route[0][0]              
    best_route[1] = distance_calc(Xdata, best_route)                     
    return best_route

#Function: Augmented Cost
def augumented_cost(Xdata, city_tour, penalty, limit):
    augmented = 0   
    for i in range(0, len(city_tour[0]) - 1):
        c1 = city_tour[0][i]
        c2 = city_tour[0][i + 1]      
        if c2 < c1:
            c1, c2 = c2, c1            
        augmented = augmented + Xdata[c1-1, c2-1] + (limit * penalty[c1-1][c2-1])    
    return augmented

# Function: Local Search
def local_search(Xdata, city_tour, penalty, max_attempts = 50, limit= 1):
    count = 0
    ag_cost = augumented_cost(Xdata, city_tour = city_tour, penalty = penalty, limit = limit)
    solution = copy.deepcopy(city_tour) 
    while (count < max_attempts):
        candidate = stochastic_2_opt(Xdata, city_tour = solution)
        candidate_augmented = augumented_cost(Xdata, city_tour = candidate, penalty = penalty, limit = limit)       
        if candidate_augmented < ag_cost:
            solution  = copy.deepcopy(candidate)
            ag_cost = augumented_cost(Xdata, city_tour = solution, penalty = penalty, limit = limit)
            count = 0
        else:
            count = count + 1                             
    return solution 

#Function: Utility
def utility (Xdata, city_tour, penalty, limit = 1):
    utilities = [0 for i in city_tour[0]]
    for i in range(0, len(city_tour[0]) - 1):
        c1 = city_tour[0][i]
        c2 = city_tour[0][i + 1]      
        if c2 < c1:
            c1, c2 = c2, c1            
        utilities[i] = Xdata[c1-1, c2-1] /(1 + penalty[c1-1][c2-1])  
    return utilities

#Function: Update Penalty
def update_penalty(penalty, city_tour, utilities):
    max_utility = max(utilities)   
    for i in range(0, len(city_tour[0]) - 1):
        c1 = city_tour[0][i]
        c2 = city_tour[0][i + 1]         
        if c2 < c1:
            c1, c2 = c2, c1        
        if (utilities[i] == max_utility):
            penalty[c1-1][c2-1] = penalty[c1-1][c2-1] + 1   
    return penalty

# Function: Guided Search
def guided_search(Xdata, city_tour, alpha = 0.3, local_search_optima = 1000, max_attempts = 20, iterations = 50):
    count = 0
    limit = alpha * (local_search_optima / len(city_tour[0]))  
    penalty = [[0 for i in city_tour[0]] for j in city_tour[0]]
    solution = copy.deepcopy(city_tour)
    best_solution = [[],float("inf")]
    while (count < iterations):
        solution = local_search(Xdata, city_tour = solution, penalty = penalty, max_attempts = max_attempts, limit = limit)
        utilities = utility(Xdata, city_tour = solution, penalty = penalty, limit = limit)
        penalty = update_penalty(penalty = penalty, city_tour = solution, utilities = utilities)
        if (solution[1] < best_solution[1]):
            best_solution = copy.deepcopy(solution) 
        count = count + 1
        print('Iteration = ', count, ' Distance ', best_solution[1])
    return best_solution