############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Tabu Search
 
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

# Function:  Build Recency Based Memory and Frequency Based Memory (STM and LTM)
def build_stm_and_ltm(Xdata):
    n = int((Xdata.shape[0]**2 - Xdata.shape[0])/2)
    stm_and_ltm = np.zeros((n, 5)) # ['City 1','City 2','Recency', 'Frequency', 'Distance']
    count = 0
    for i in range (0, int((Xdata.shape[0]**2))):
        city_1 = i // (Xdata.shape[1])
        city_2 = i %  (Xdata.shape[1])
        if (city_1 < city_2):
            stm_and_ltm[count, 0] = city_1 + 1
            stm_and_ltm[count, 1] = city_2 + 1
            count = count + 1
    return stm_and_ltm

# Function: Swap
def local_search_2_swap(Xdata, city_tour, m, n):
    best_route = copy.deepcopy(city_tour)       
    best_route[0][m], best_route[0][n] = best_route[0][n], best_route[0][m]        
    best_route[0][-1]  = best_route[0][0]              
    best_route[1] = distance_calc(Xdata, best_route)                     
    city_list = copy.deepcopy(best_route)         
    return city_list
	
# Function: 2_opt
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

# Function: Diversification
def ltm_diversification (Xdata, stm_and_ltm, city_list, p_dest):
    stm_and_ltm = stm_and_ltm[stm_and_ltm[:,3].argsort()]
    stm_and_ltm = stm_and_ltm[stm_and_ltm[:,4].argsort()]
    lenght = random.sample((range(1, int(Xdata.shape[0]*p_dest))), 1)[0]
    for i in range(0, lenght):
        m = int(stm_and_ltm[i, 0] - 1)
        n = int(stm_and_ltm[i, 1] - 1)
        city_list = local_search_2_swap(Xdata, city_list, m, n)
        stm_and_ltm[i, 3] = stm_and_ltm[i, 3] + 1
        stm_and_ltm[i, 2] = 1
    return stm_and_ltm, city_list

# Function: 4 opt Stochastic
def local_search_4_opt_stochastic(Xdata, city_tour):
    best_route = copy.deepcopy(city_tour)
    best_route_03 = [[],float("inf")]
    best_route_04 = [[],float("inf")]
    best_route_11 = [[],float("inf")]
    best_route_22 = [[],float("inf")]
    best_route_27 = [[],float("inf")] 
    i, j, k, L = np.sort(random.sample(list(range(0,Xdata.shape[0])), 4))                                
    best_route_03[0] = best_route[0][:i+1] + best_route[0][k+1:L+1] + best_route[0][j+1:k+1] + best_route[0][i+1:j+1] + best_route[0][L+1:]
    best_route_03[1] = distance_calc(Xdata, best_route_03) # ADCB                      
    best_route_04[0] = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][j+1:k+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][L+1:]                  
    best_route_04[1] = distance_calc(Xdata, best_route_04)  # AbCd
    best_route_11[0] = best_route[0][:i+1] + best_route[0][k+1:L+1] + list(reversed(best_route[0][i+1:j+1])) + list(reversed(best_route[0][j+1:k+1])) + best_route[0][L+1:]
    best_route_11[1] = distance_calc(Xdata, best_route_11)   # ADbc                                          
    best_route_22[0] = best_route[0][:i+1] + list(reversed(best_route[0][j+1:k+1])) + list(reversed(best_route[0][k+1:L+1])) + best_route[0][i+1:j+1] + best_route[0][L+1:]
    best_route_22[1] = distance_calc(Xdata, best_route_22) # AcdB                       
    best_route_27[0] = best_route[0][:i+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][j+1:k+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][L+1:]
    best_route_27[1] = distance_calc(Xdata, best_route_27) # AdCb    
    best_route = copy.deepcopy(best_route_03)          
    if(best_route_04[1]  < best_route[1]):
        best_route = copy.deepcopy(best_route_04)
    elif(best_route_11[1]  < best_route[1]):
        best_route = copy.deepcopy(best_route_11)            
    elif(best_route_22[1]  < best_route[1]):
        best_route = copy.deepcopy(best_route_22)            
    elif(best_route_27[1]  < best_route[1]):
        best_route = copy.deepcopy(best_route_27)          
    return best_route
	
# Function: Tabu Update
def tabu_update(Xdata, stm_and_ltm, city_list, best_distance, tabu_list, p_dest, tabu_tenure = 20,  diversify = False):
    m_list = []
    n_list = []
    city_list = local_search_2_opt(Xdata, city_list) # itensification
    for i in range(0, stm_and_ltm.shape[0]):
        m = int(stm_and_ltm[i, 0] - 1)
        n = int(stm_and_ltm[i, 1] - 1)
        stm_and_ltm[i, -1] = local_search_2_swap(Xdata, city_list, m, n)[1] 
    stm_and_ltm = stm_and_ltm[stm_and_ltm[:,4].argsort()] # Distance
    m = int(stm_and_ltm[0,0]-1)
    n = int(stm_and_ltm[0,1]-1)
    recency = int(stm_and_ltm[0,2])
    distance = stm_and_ltm[0,-1]     
    if (distance < best_distance): # Aspiration Criterion -> by Objective
        city_list = local_search_2_swap(Xdata, city_list, m, n)
        i = 0
        while (i < stm_and_ltm.shape[0]):
            if (stm_and_ltm[i, 0] == m + 1 and stm_and_ltm[i, 1] == n + 1):
                stm_and_ltm[i, 2] = 1
                stm_and_ltm[i, 3] = stm_and_ltm[i, 3] + 1
                stm_and_ltm[i, -1] = distance
                if (stm_and_ltm[i, 3] == 1):
                    m_list.append(m + 1)
                    n_list.append(n + 1)
                i = stm_and_ltm.shape[0]
            i = i + 1
    else:
        i = 0
        while (i < stm_and_ltm.shape[0]):
            m = int(stm_and_ltm[i,0]-1)
            n = int(stm_and_ltm[i,1]-1)
            recency = int(stm_and_ltm[i,2]) 
            distance = local_search_2_swap(Xdata, city_list, m, n)[1]
            if (distance < best_distance):
                city_list = local_search_2_swap(Xdata, city_list, m, n)
            if (recency == 0):
                city_list = local_search_2_swap(Xdata, city_list, m, n)
                stm_and_ltm[i, 2] = 1
                stm_and_ltm[i, 3] = stm_and_ltm[i, 3] + 1
                stm_and_ltm[i, -1] = distance
                if (stm_and_ltm[i, 3] == 1):
                    m_list.append(m + 1)
                    n_list.append(n + 1)
                i = stm_and_ltm.shape[0]
            i = i + 1
    if (len(m_list) > 0): 
        tabu_list[0].append(m_list[0])
        tabu_list[1].append(n_list[0])
    if (len(tabu_list[0]) > tabu_tenure):
        i = 0
        while (i < stm_and_ltm.shape[0]):
            if (stm_and_ltm[i, 0] == tabu_list[0][0] and stm_and_ltm[i, 1] == tabu_list[1][0]):
                del tabu_list[0][0]
                del tabu_list[1][0]
                stm_and_ltm[i, 2] = 0
                i = stm_and_ltm.shape[0]
            i = i + 1          
    if (diversify == True):
        stm_and_ltm, city_list = ltm_diversification(Xdata, stm_and_ltm, city_list, p_dest) # diversification
        # city_list = local_search_4_opt_stochastic(Xdata, city_list) # diversification
    return stm_and_ltm, city_list, tabu_list

# Function: Tabu Search
def tabu_search(Xdata, city_tour, iterations = 150, tabu_tenure = 20, p_diver = 0.2, p_dest = 0.3):
    count = 0
    best_solution = copy.deepcopy(city_tour)
    stm_and_ltm = build_stm_and_ltm(Xdata)
    tabu_list = [[],[]]
    diversify = False
    no_improvement = 0
    while (count < iterations):
        stm_and_ltm, city_tour, tabu_list = tabu_update(Xdata, stm_and_ltm, city_tour, best_solution[1], tabu_list = tabu_list, p_dest = p_dest, tabu_tenure = tabu_tenure, diversify = diversify)
        if (city_tour[1] < best_solution[1]):
            best_solution = copy.deepcopy(city_tour)
            no_improvement = 0
            diversify = False
        else:
            if (no_improvement > 0 and no_improvement % int(p_diver*iterations) == 0):
                diversify = True
                no_improvement = 0
            else:
                diversify = False
            no_improvement = no_improvement + 1
        count = count + 1
        print('Iteration =', count, '-> Current =', city_tour[1], '-> best =', best_solution[1])
    print('Best Solution =', best_solution)
    return best_solution
