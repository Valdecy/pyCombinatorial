############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - 4-opt
 
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
                city_list = copy.deepcopy(best_route)         
            best_route = copy.deepcopy(seed) 
    # print("Best 2-opt solution found =", city_list[1])
    return city_list

# Function: 3_opt
def local_search_3_opt(Xdata, city_tour):
    city_list = copy.deepcopy(city_tour)
    best_route = copy.deepcopy(city_list)
    best_route_01 = [[],float("inf")]
    best_route_02 = [[],float("inf")]
    best_route_03 = [[],float("inf")]
    best_route_04 = [[],float("inf")]       
    seed = copy.deepcopy(city_list)        
    for i in range(0, len(city_list[0]) - 3):
        for j in range(i+1, len(city_list[0]) - 2):
            for k in range(j+1, len(city_list[0]) - 1): 
                best_route_01[0] = best_route[0][:i+1] + best_route[0][j+1:k+1] + best_route[0][i+1:j+1] + best_route[0][k+1:]
                best_route_01[1] = distance_calc(Xdata, best_route_01)
                best_route_02[0] = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1])) + list(reversed(best_route[0][j+1:k+1])) + best_route[0][k+1:]
                best_route_02[1] = distance_calc(Xdata, best_route_02)
                best_route_03[0] = best_route[0][:i+1] + list(reversed(best_route[0][j+1:k+1])) + best_route[0][i+1:j+1] + best_route[0][k+1:]
                best_route_03[1] = distance_calc(Xdata, best_route_03)
                best_route_04[0] = best_route[0][:i+1] + best_route[0][j+1:k+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][k+1:]
                best_route_04[1] = distance_calc(Xdata, best_route_04)
                       
                if(best_route_01[1]  < best_route[1]):
                    best_route = copy.deepcopy(best_route_01)                        
                elif(best_route_02[1]  < best_route[1]):
                    best_route = copy.deepcopy(best_route_02)                        
                elif(best_route_03[1]  < best_route[1]):
                    best_route = copy.deepcopy(best_route_03)                       
                elif(best_route_04[1]  < best_route[1]):
                    best_route = copy.deepcopy(best_route_04) 
                        
            if (best_route[1] < city_list[1]):
                city_list = copy.deepcopy(best_route)             
            best_route = copy.deepcopy(seed)
    #print("Best 3-opt solution found =", city_list[1])
    return city_list

# Function: 4_opt
def local_search_4_opt(Xdata, city_tour, recursive_seeding = 1):
    if (recursive_seeding < 0):
        count = recursive_seeding - 1
    else:
        count = 0
    city_list = copy.deepcopy(city_tour)
    city_list_old = city_list[1]*2
    iteration = 0
    while (count < recursive_seeding):
        best_route    = copy.deepcopy(city_list)
        best_route_01 = local_search_2_opt(Xdata, best_route)
        best_route_02 = local_search_3_opt(Xdata, best_route)
        best_route_03 = [[],float("inf")]
        best_route_04 = [[],float("inf")]
        best_route_05 = [[],float("inf")]
        best_route_06 = [[],float("inf")]
        best_route_07 = [[],float("inf")]
        best_route_08 = [[],float("inf")] 
        best_route_09 = [[],float("inf")]
        best_route_10 = [[],float("inf")]
        best_route_11 = [[],float("inf")]
        best_route_12 = [[],float("inf")]
        best_route_13 = [[],float("inf")]
        best_route_14 = [[],float("inf")]
        best_route_15 = [[],float("inf")]
        best_route_16 = [[],float("inf")]
        best_route_17 = [[],float("inf")]
        best_route_18 = [[],float("inf")]
        best_route_19 = [[],float("inf")]
        best_route_20 = [[],float("inf")] 
        best_route_21 = [[],float("inf")]
        best_route_22 = [[],float("inf")]
        best_route_23 = [[],float("inf")]
        best_route_24 = [[],float("inf")]
        best_route_25 = [[],float("inf")]
        best_route_26 = [[],float("inf")] 
        best_route_27 = [[],float("inf")] 
        seed = copy.deepcopy(city_list)        
        for i in range(0, len(city_list[0]) - 4):
            for j in range(i+1, len(city_list[0]) - 3):
                for k in range(j+1, len(city_list[0]) - 2): 
                    for L in range(k+1, len(city_list[0]) - 1):                         
                        best_route_03[0] = best_route[0][:i+1] + best_route[0][k+1:L+1] + best_route[0][j+1:k+1] + best_route[0][i+1:j+1] + best_route[0][L+1:]
                        best_route_03[1] = distance_calc(Xdata, best_route_03)                        
                        best_route_04[0] = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][j+1:k+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][L+1:]                  
                        best_route_04[1] = distance_calc(Xdata, best_route_04)                        
                        best_route_05[0] = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1])) + list(reversed(best_route[0][j+1:k+1])) + list(reversed(best_route[0][k+1:L+1])) + best_route[0][L+1:]
                        best_route_05[1] = distance_calc(Xdata, best_route_05)                     
                        best_route_06[0] = best_route[0][:i+1] + best_route[0][j+1:k+1] + best_route[0][i+1:j+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][L+1:]
                        best_route_06[1] = distance_calc(Xdata, best_route_06)                       
                        best_route_07[0] = best_route[0][:i+1] + best_route[0][j+1:k+1] + list(reversed(best_route[0][i+1:j+1])) + list(reversed(best_route[0][k+1:L+1])) + best_route[0][L+1:]
                        best_route_07[1] = distance_calc(Xdata, best_route_07)                        
                        best_route_08[0] = best_route[0][:i+1] + list(reversed(best_route[0][j+1:k+1])) + best_route[0][i+1:j+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][L+1:]
                        best_route_08[1] = distance_calc(Xdata, best_route_08)                        
                        best_route_09[0] = best_route[0][:i+1] + best_route[0][k+1:L+1] + best_route[0][i+1:j+1] + list(reversed(best_route[0][j+1:k+1])) + best_route[0][L+1:]
                        best_route_09[1] = distance_calc(Xdata, best_route_09)                        
                        best_route_10[0] = best_route[0][:i+1] + best_route[0][k+1:L+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][j+1:k+1] + best_route[0][L+1:]
                        best_route_10[1] = distance_calc(Xdata, best_route_10)                        
                        best_route_11[0] = best_route[0][:i+1] + best_route[0][k+1:L+1] + list(reversed(best_route[0][i+1:j+1])) + list(reversed(best_route[0][j+1:k+1])) + best_route[0][L+1:]
                        best_route_11[1] = distance_calc(Xdata, best_route_11)                        
                        best_route_12[0] = best_route[0][:i+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][i+1:j+1] + list(reversed(best_route[0][j+1:k+1])) + best_route[0][L+1:]
                        best_route_12[1] = distance_calc(Xdata, best_route_12)
                        best_route_13[0] = best_route[0][:i+1] + list(reversed(best_route[0][k+1:L+1])) + list(reversed(best_route[0][i+1:j+1])) + best_route[0][j+1:k+1] + best_route[0][L+1:]
                        best_route_13[1] = distance_calc(Xdata, best_route_13)                        
                        best_route_14[0] = best_route[0][:i+1] + list(reversed(best_route[0][k+1:L+1])) + list(reversed(best_route[0][i+1:j+1])) + list(reversed(best_route[0][j+1:k+1])) + best_route[0][L+1:]
                        best_route_14[1] = distance_calc(Xdata, best_route_14)                       
                        best_route_15[0] = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][k+1:L+1] + best_route[0][j+1:k+1] + best_route[0][L+1:]
                        best_route_15[1] = distance_calc(Xdata, best_route_15)
                        best_route_16[0] = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][k+1:L+1] + list(reversed(best_route[0][j+1:k+1])) + best_route[0][L+1:]
                        best_route_16[1] = distance_calc(Xdata, best_route_16)                        
                        best_route_17[0] = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1])) + list(reversed(best_route[0][k+1:L+1])) + best_route[0][j+1:k+1] + best_route[0][L+1:]
                        best_route_17[1] = distance_calc(Xdata, best_route_17)
                        best_route_18[0] = best_route[0][:i+1] + best_route[0][j+1:k+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][i+1:j+1] + best_route[0][L+1:]
                        best_route_18[1] = distance_calc(Xdata, best_route_18)                       
                        best_route_19[0] = best_route[0][:i+1] + best_route[0][j+1:k+1] + list(reversed(best_route[0][k+1:L+1])) + list(reversed(best_route[0][i+1:j+1])) + best_route[0][L+1:]
                        best_route_19[1] = distance_calc(Xdata, best_route_19)                        
                        best_route_20[0] = best_route[0][:i+1] + list(reversed(best_route[0][j+1:k+1])) + best_route[0][k+1:L+1] + best_route[0][i+1:j+1] + best_route[0][L+1:]
                        best_route_20[1] = distance_calc(Xdata, best_route_20)                        
                        best_route_21[0] = best_route[0][:i+1] + list(reversed(best_route[0][j+1:k+1])) + best_route[0][k+1:L+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][L+1:]
                        best_route_21[1] = distance_calc(Xdata, best_route_21)                        
                        best_route_22[0] = best_route[0][:i+1] + list(reversed(best_route[0][j+1:k+1])) + list(reversed(best_route[0][k+1:L+1])) + best_route[0][i+1:j+1] + best_route[0][L+1:]
                        best_route_22[1] = distance_calc(Xdata, best_route_22)
                        best_route_23[0] = best_route[0][:i+1] + list(reversed(best_route[0][j+1:k+1])) + list(reversed(best_route[0][k+1:L+1])) + list(reversed(best_route[0][i+1:j+1])) + best_route[0][L+1:]
                        best_route_23[1] = distance_calc(Xdata, best_route_23)                      
                        best_route_24[0] = best_route[0][:i+1] + best_route[0][k+1:L+1] + best_route[0][j+1:k+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][L+1:]
                        best_route_24[1] = distance_calc(Xdata, best_route_24)                        
                        best_route_25[0] = best_route[0][:i+1] + best_route[0][k+1:L+1] + list(reversed(best_route[0][j+1:k+1])) + best_route[0][i+1:j+1] + best_route[0][L+1:]
                        best_route_25[1] = distance_calc(Xdata, best_route_25)
                        best_route_26[0] = best_route[0][:i+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][j+1:k+1] + best_route[0][i+1:j+1] + best_route[0][L+1:]
                        best_route_26[1] = distance_calc(Xdata, best_route_26)                        
                        best_route_27[0] = best_route[0][:i+1] + list(reversed(best_route[0][k+1:L+1])) + best_route[0][j+1:k+1] + list(reversed(best_route[0][i+1:j+1])) + best_route[0][L+1:]
                        best_route_27[1] = distance_calc(Xdata, best_route_27)
                        
                        if(best_route_01[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_01)                              
                        elif(best_route_02[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_02)
                        elif(best_route_03[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_03)       
                        elif(best_route_04[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_04)                    
                        elif(best_route_05[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_05)
                        elif(best_route_06[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_06)      
                        elif(best_route_07[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_07)                           
                        elif(best_route_08[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_08)                              
                        elif(best_route_09[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_09)                                
                        elif(best_route_10[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_10)                                
                        elif(best_route_11[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_11)                                
                        elif(best_route_12[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_12)                               
                        elif(best_route_13[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_13)
                        elif(best_route_14[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_14)                             
                        elif(best_route_15[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_15)                              
                        elif(best_route_16[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_16)                                
                        elif(best_route_17[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_17)
                        elif(best_route_18[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_18)                                
                        elif(best_route_19[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_19)                                
                        elif(best_route_20[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_20)
                        elif(best_route_21[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_21)                               
                        elif(best_route_22[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_22)                                
                        elif(best_route_23[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_23)
                        elif(best_route_24[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_24)
                        elif(best_route_25[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_25)
                        elif(best_route_26[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_26)       
                        elif(best_route_27[1]  < best_route[1]):
                            best_route = copy.deepcopy(best_route_27)
                            
                    if (best_route[1] < city_list[1]):
                        city_list = copy.deepcopy(best_route)             
                    best_route = copy.deepcopy(seed)
        count = count + 1  
        iteration = iteration + 1  
        print('Iteration = ', iteration, '-> Distance =', city_list[1])
        if (city_list_old > city_list[1] and recursive_seeding < 0):
             city_list_old = city_list[1]
             count = -2
             recursive_seeding = -1
        elif(city_list[1] >= city_list_old and recursive_seeding < 0):
            count = -1
            recursive_seeding = -2
    return city_list