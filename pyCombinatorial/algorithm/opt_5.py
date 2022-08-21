############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Local Search-5-opt
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

############################################################################

# Function: Possible Segments
def segments_5_opt(n):
    x             = []
    a, b, c, d, e = 0, 0, 0, 0, 0
    for i in range(0, n):
        a = i
        for j in range(i + 1, n):
            b = j
            for k in range(j + 1, n):
                c = k
                for L in range(k + 1, n):
                    d = L
                    for m in range(L + 1, n + (i > 0)):
                        e = m
                        x.append((a, b, c, d, e))    
    return x

############################################################################

# Function: 5_opt Stochastic
def local_search_5_opt(distance_matrix, city_tour, recursive_seeding = -1, verbose = True):
    if (recursive_seeding < 0):
        count = recursive_seeding - 1
    else:
        count = 0
    city_list     = [city_tour[0][:-1], city_tour[1]]
    city_list_old = city_list[1]*2
    iteration     = 0
    while (count < recursive_seeding):
        if (verbose == True):
            print('Iteration = ', iteration, 'Distance = ', round(city_list[1], 2))  
        best_route   = copy.deepcopy(city_list)
        best_route_1 = [[], 1]
        seed         = copy.deepcopy(city_list)     
        x            = segments_5_opt(len(city_list[0]))
        for item in x:
            i, j, k, L, m = item   
            A             = best_route[0][:i+1] + best_route[0][i+1:j+1]
            a             = best_route[0][:i+1] + list(reversed(best_route[0][i+1:j+1]))
            B             = best_route[0][j+1:k+1]
            b             = list(reversed(B))
            C             = best_route[0][k+1:L+1]
            c             = list(reversed(C))
            D             = best_route[0][L+1:m+1]
            d             = list(reversed(D))
            E             = best_route[0][m+1:]
            e             = list(reversed(E))
            trial         = [ 
                                # Original Tour
                                #[ A  +  B  +  C  +  D  +  E ],
                                
                                # Permutation
                                [ A  +  B  +  C  +  E  +  D ], 
                                [ A  +  B  +  D  +  C  +  E ],
                                [ A  +  B  +  D  +  E  +  C ],
                                [ A  +  B  +  E  +  C  +  D ],
                                [ A  +  B  +  E  +  D  +  C ],
                                [ A  +  C  +  B  +  D  +  E ],
                                [ A  +  C  +  B  +  E  +  D ],
                                [ A  +  C  +  D  +  B  +  E ],
                                [ A  +  C  +  E  +  B  +  D ],
                                [ A  +  D  +  B  +  C  +  E ],
                                [ A  +  D  +  C  +  B  +  E ],
                                
                                
                                
                                # 1 
                                [ a  +  B  +  C  +  D  +  E ],
                                [ a  +  B  +  C  +  E  +  D ],
                                [ a  +  B  +  D  +  C  +  E ],
                                [ a  +  B  +  D  +  E  +  C ],
                                [ a  +  B  +  E  +  C  +  D ],
                                [ a  +  B  +  E  +  D  +  C ],
                                [ a  +  C  +  B  +  D  +  E ],
                                [ a  +  C  +  B  +  E  +  D ],
                                [ a  +  C  +  D  +  B  +  E ],
                                [ a  +  C  +  E  +  B  +  D ],
                                [ a  +  D  +  B  +  C  +  E ],
                                [ a  +  D  +  C  +  B  +  E ],
                                
                                [ A  +  b  +  C  +  D  +  E ],
                                [ A  +  b  +  C  +  E  +  D ],
                                [ A  +  b  +  D  +  C  +  E ],
                                [ A  +  b  +  D  +  E  +  C ],
                                [ A  +  b  +  E  +  C  +  D ],
                                [ A  +  b  +  E  +  D  +  C ],
                                [ A  +  C  +  b  +  D  +  E ],
                                [ A  +  C  +  b  +  E  +  D ],
                                [ A  +  C  +  D  +  b  +  E ],
                                [ A  +  C  +  E  +  b  +  D ],
                                [ A  +  D  +  b  +  C  +  E ],
                                [ A  +  D  +  C  +  b  +  E ],
                                
                                [ A  +  B  +  c  +  D  +  E ],
                                [ A  +  B  +  c  +  E  +  D ],
                                [ A  +  B  +  D  +  c  +  E ],
                                [ A  +  B  +  D  +  E  +  c ],
                                [ A  +  B  +  E  +  c  +  D ],
                                [ A  +  B  +  E  +  D  +  c ],
                                [ A  +  c  +  B  +  D  +  E ],
                                [ A  +  c  +  B  +  E  +  D ],
                                [ A  +  c  +  D  +  B  +  E ],
                                [ A  +  c  +  E  +  B  +  D ],
                                [ A  +  D  +  B  +  c  +  E ],
                                [ A  +  D  +  c  +  B  +  E ],
                                
                                [ A  +  B  +  C  +  d  +  E ],
                                [ A  +  B  +  C  +  E  +  d ],
                                [ A  +  B  +  d  +  C  +  E ],
                                [ A  +  B  +  d  +  E  +  C ],
                                [ A  +  B  +  E  +  C  +  d ],
                                [ A  +  B  +  E  +  d  +  C ],
                                [ A  +  C  +  B  +  d  +  E ],
                                [ A  +  C  +  B  +  E  +  d ],
                                [ A  +  C  +  d  +  B  +  E ],
                                [ A  +  C  +  E  +  B  +  d ],
                                [ A  +  d  +  B  +  C  +  E ],
                                [ A  +  d  +  C  +  B  +  E ],
                                
                                [ A  +  B  +  C  +  D  +  e ],
                                [ A  +  B  +  C  +  e  +  D ],
                                [ A  +  B  +  D  +  C  +  e ],
                                [ A  +  B  +  D  +  e  +  C ],
                                [ A  +  B  +  e  +  C  +  D ],
                                [ A  +  B  +  e  +  D  +  C ],
                                [ A  +  C  +  B  +  D  +  e ],
                                [ A  +  C  +  B  +  e  +  D ],
                                [ A  +  C  +  D  +  B  +  e ],
                                [ A  +  C  +  e  +  B  +  D ],
                                [ A  +  D  +  B  +  C  +  e ],
                                [ A  +  D  +  C  +  B  +  e ],
                                
                                
                                
                                # 2
                                [ a  +  b  +  C  +  E  +  D ], 
                                [ a  +  b  +  D  +  C  +  E ],
                                [ a  +  b  +  D  +  E  +  C ],
                                [ a  +  b  +  E  +  C  +  D ],
                                [ a  +  b  +  E  +  D  +  C ],
                                [ a  +  C  +  b  +  D  +  E ],
                                [ a  +  C  +  b  +  E  +  D ],
                                [ a  +  C  +  D  +  b  +  E ],
                                [ a  +  C  +  E  +  b  +  D ],
                                [ a  +  D  +  B  +  C  +  E ],
                                [ a  +  D  +  C  +  b  +  E ],
                                
                                [ a  +  B  +  c  +  E  +  D ], 
                                [ a  +  B  +  D  +  c  +  E ],
                                [ a  +  B  +  D  +  E  +  c ],
                                [ a  +  B  +  E  +  c  +  D ],
                                [ a  +  B  +  E  +  D  +  c ],
                                [ a  +  c  +  B  +  D  +  E ],
                                [ a  +  c  +  B  +  E  +  D ],
                                [ a  +  c  +  D  +  B  +  E ],
                                [ a  +  c  +  E  +  B  +  D ],
                                [ a  +  D  +  B  +  c  +  E ],
                                [ a  +  D  +  c  +  B  +  E ],
                                
                                [ a  +  B  +  C  +  E  +  d ], 
                                [ a  +  B  +  d  +  C  +  E ],
                                [ a  +  B  +  d  +  E  +  C ],
                                [ a  +  B  +  E  +  C  +  d ],
                                [ a  +  B  +  E  +  d  +  C ],
                                [ a  +  C  +  B  +  d  +  E ],
                                [ a  +  C  +  B  +  E  +  d ],
                                [ a  +  C  +  d  +  B  +  E ],
                                [ a  +  C  +  E  +  B  +  d ],
                                [ a  +  d  +  B  +  C  +  E ],
                                [ a  +  d  +  C  +  B  +  E ],
                                
                                [ a  +  B  +  C  +  e  +  D ], 
                                [ a  +  B  +  D  +  C  +  e ],
                                [ a  +  B  +  D  +  e  +  C ],
                                [ a  +  B  +  e  +  C  +  D ],
                                [ a  +  B  +  e  +  D  +  C ],
                                [ a  +  C  +  B  +  D  +  e ],
                                [ a  +  C  +  B  +  e  +  D ],
                                [ a  +  C  +  D  +  B  +  e ],
                                [ a  +  C  +  e  +  B  +  D ],
                                [ a  +  D  +  B  +  C  +  e ],
                                [ a  +  D  +  C  +  B  +  e ],
                                
                                [ A  +  b  +  c  +  D  +  E ],
                                [ A  +  b  +  c  +  E  +  D ],
                                [ A  +  b  +  D  +  c  +  E ],
                                [ A  +  b  +  D  +  E  +  c ],
                                [ A  +  b  +  E  +  c  +  D ],
                                [ A  +  b  +  E  +  D  +  c ],
                                [ A  +  c  +  b  +  D  +  E ],
                                [ A  +  c  +  b  +  E  +  D ],
                                [ A  +  c  +  D  +  b  +  E ],
                                [ A  +  c  +  E  +  b  +  D ],
                                [ A  +  D  +  b  +  c  +  E ],
                                [ A  +  D  +  c  +  b  +  E ],
                                
                                [ A  +  b  +  C  +  d  +  E ],
                                [ A  +  b  +  C  +  E  +  d ],
                                [ A  +  b  +  d  +  C  +  E ],
                                [ A  +  b  +  d  +  E  +  C ],
                                [ A  +  b  +  E  +  C  +  d ],
                                [ A  +  b  +  E  +  d  +  C ],
                                [ A  +  C  +  b  +  d  +  E ],
                                [ A  +  C  +  b  +  E  +  d ],
                                [ A  +  C  +  d  +  b  +  E ],
                                [ A  +  C  +  E  +  b  +  d ],
                                [ A  +  d  +  b  +  C  +  E ],
                                [ A  +  d  +  C  +  b  +  E ],
                                
                                [ A  +  b  +  C  +  D  +  e ],
                                [ A  +  b  +  C  +  e  +  D ],
                                [ A  +  b  +  D  +  C  +  e ],
                                [ A  +  b  +  D  +  e  +  C ],
                                [ A  +  b  +  e  +  C  +  D ],
                                [ A  +  b  +  e  +  D  +  C ],
                                [ A  +  C  +  b  +  D  +  e ],
                                [ A  +  C  +  b  +  e  +  D ],
                                [ A  +  C  +  D  +  b  +  e ],
                                [ A  +  C  +  e  +  b  +  D ],
                                [ A  +  D  +  b  +  C  +  e ],
                                [ A  +  D  +  C  +  b  +  e ],
                                
                                [ A  +  B  +  c  +  d  +  E ],
                                [ A  +  B  +  c  +  E  +  d ],
                                [ A  +  B  +  d  +  c  +  E ],
                                [ A  +  B  +  d  +  E  +  c ],
                                [ A  +  B  +  E  +  c  +  d ],
                                [ A  +  B  +  E  +  d  +  c ],
                                [ A  +  c  +  B  +  d  +  E ],
                                [ A  +  c  +  B  +  E  +  d ],
                                [ A  +  c  +  d  +  B  +  E ],
                                [ A  +  c  +  E  +  B  +  d ],
                                [ A  +  d  +  B  +  c  +  E ],
                                [ A  +  d  +  c  +  B  +  E ],
                                
                                [ A  +  B  +  c  +  D  +  e ],
                                [ A  +  B  +  c  +  e  +  D ],
                                [ A  +  B  +  D  +  c  +  e ],
                                [ A  +  B  +  D  +  e  +  c ],
                                [ A  +  B  +  e  +  c  +  D ],
                                [ A  +  B  +  e  +  D  +  c ],
                                [ A  +  c  +  B  +  D  +  e ],
                                [ A  +  c  +  B  +  e  +  D ],
                                [ A  +  c  +  D  +  B  +  e ],
                                [ A  +  c  +  e  +  B  +  D ],
                                [ A  +  D  +  B  +  c  +  e ],
                                [ A  +  D  +  c  +  B  +  e ],
                                
                                [ A  +  B  +  C  +  d  +  e ],
                                [ A  +  B  +  C  +  e  +  d ],
                                [ A  +  B  +  d  +  C  +  e ],
                                [ A  +  B  +  d  +  e  +  C ],
                                [ A  +  B  +  e  +  C  +  d ],
                                [ A  +  B  +  e  +  d  +  C ],
                                [ A  +  C  +  B  +  d  +  e ],
                                [ A  +  C  +  B  +  e  +  d ],
                                [ A  +  C  +  d  +  B  +  e ],
                                [ A  +  C  +  e  +  B  +  d ],
                                [ A  +  d  +  B  +  C  +  e ],
                                [ A  +  d  +  C  +  B  +  e ],
                                
                                
                                
                                # 3
                                [ a  +  b  +  c  +  E  +  D ], 
                                [ a  +  b  +  D  +  c  +  E ],
                                [ a  +  b  +  D  +  E  +  c ],
                                [ a  +  b  +  E  +  c  +  D ],
                                [ a  +  b  +  E  +  D  +  c ],
                                [ a  +  c  +  b  +  D  +  E ],
                                [ a  +  c  +  b  +  E  +  D ],
                                [ a  +  c  +  D  +  b  +  E ],
                                [ a  +  c  +  E  +  b  +  D ],
                                [ a  +  D  +  b  +  c  +  E ],
                                [ a  +  D  +  c  +  b  +  E ],
                                
                                [ a  +  b  +  C  +  E  +  d ], 
                                [ a  +  b  +  d  +  C  +  E ],
                                [ a  +  b  +  d  +  E  +  C ],
                                [ a  +  b  +  E  +  C  +  d ],
                                [ a  +  b  +  E  +  d  +  C ],
                                [ a  +  C  +  b  +  d  +  E ],
                                [ a  +  C  +  b  +  E  +  d ],
                                [ a  +  C  +  d  +  b  +  E ],
                                [ a  +  C  +  E  +  b  +  d ],
                                [ a  +  d  +  b  +  C  +  E ],
                                [ a  +  d  +  C  +  b  +  E ],
                                
                                [ a  +  b  +  C  +  e  +  D ], 
                                [ a  +  b  +  D  +  C  +  e ],
                                [ a  +  b  +  D  +  e  +  C ],
                                [ a  +  b  +  e  +  C  +  D ],
                                [ a  +  b  +  e  +  D  +  C ],
                                [ a  +  C  +  b  +  D  +  e ],
                                [ a  +  C  +  b  +  e  +  D ],
                                [ a  +  C  +  D  +  b  +  e ],
                                [ a  +  C  +  e  +  b  +  D ],
                                [ a  +  D  +  b  +  C  +  e ],
                                [ a  +  D  +  C  +  b  +  e ],
                                
                                [ a  +  B  +  c  +  E  +  d ], 
                                [ a  +  B  +  d  +  c  +  E ],
                                [ a  +  B  +  d  +  E  +  c ],
                                [ a  +  B  +  E  +  c  +  d ],
                                [ a  +  B  +  E  +  d  +  c ],
                                [ a  +  c  +  B  +  d  +  E ],
                                [ a  +  c  +  B  +  E  +  d ],
                                [ a  +  c  +  d  +  B  +  E ],
                                [ a  +  c  +  E  +  B  +  d ],
                                [ a  +  d  +  B  +  c  +  E ],
                                [ a  +  d  +  c  +  B  +  E ],

                                [ a  +  B  +  c  +  e  +  D ], 
                                [ a  +  B  +  D  +  c  +  e ],
                                [ a  +  B  +  D  +  e  +  c ],
                                [ a  +  B  +  e  +  c  +  D ],
                                [ a  +  B  +  e  +  D  +  c ],
                                [ a  +  c  +  B  +  D  +  e ],
                                [ a  +  c  +  B  +  e  +  D ],
                                [ a  +  c  +  D  +  B  +  e ],
                                [ a  +  c  +  e  +  B  +  D ],
                                [ a  +  D  +  B  +  c  +  e ],
                                [ a  +  D  +  c  +  B  +  e ],
                                
                                [ a  +  B  +  C  +  e  +  d ], 
                                [ a  +  B  +  d  +  C  +  e ],
                                [ a  +  B  +  d  +  e  +  C ],
                                [ a  +  B  +  e  +  C  +  d ],
                                [ a  +  B  +  e  +  d  +  C ],
                                [ a  +  C  +  B  +  d  +  e ],
                                [ a  +  C  +  B  +  e  +  d ],
                                [ a  +  C  +  d  +  B  +  e ],
                                [ a  +  C  +  e  +  B  +  d ],
                                [ a  +  d  +  B  +  C  +  e ],
                                [ a  +  d  +  C  +  B  +  e ],
                                
                                [ A  +  b  +  c  +  d  +  E ],
                                [ A  +  b  +  c  +  E  +  d ],
                                [ A  +  b  +  d  +  c  +  E ],
                                [ A  +  b  +  d  +  E  +  c ],
                                [ A  +  b  +  E  +  c  +  d ],
                                [ A  +  b  +  E  +  d  +  c ],
                                [ A  +  c  +  b  +  d  +  E ],
                                [ A  +  c  +  b  +  E  +  d ],
                                [ A  +  c  +  d  +  b  +  E ],
                                [ A  +  c  +  E  +  b  +  d ],
                                [ A  +  d  +  b  +  c  +  E ],
                                [ A  +  d  +  c  +  b  +  E ],
                                
                                [ A  +  b  +  c  +  D  +  e ],
                                [ A  +  b  +  c  +  e  +  D ],
                                [ A  +  b  +  D  +  c  +  e ],
                                [ A  +  b  +  D  +  e  +  c ],
                                [ A  +  b  +  e  +  c  +  D ],
                                [ A  +  b  +  e  +  D  +  c ],
                                [ A  +  c  +  b  +  D  +  e ],
                                [ A  +  c  +  b  +  e  +  D ],
                                [ A  +  c  +  D  +  b  +  e ],
                                [ A  +  c  +  e  +  b  +  D ],
                                [ A  +  D  +  b  +  c  +  e ],
                                [ A  +  D  +  c  +  b  +  e ],
                                
                                [ A  +  b  +  C  +  d  +  e ],
                                [ A  +  b  +  C  +  e  +  d ],
                                [ A  +  b  +  d  +  C  +  e ],
                                [ A  +  b  +  d  +  e  +  C ],
                                [ A  +  b  +  e  +  C  +  d ],
                                [ A  +  b  +  e  +  d  +  C ],
                                [ A  +  C  +  b  +  d  +  e ],
                                [ A  +  C  +  b  +  e  +  d ],
                                [ A  +  C  +  d  +  b  +  e ],
                                [ A  +  C  +  e  +  b  +  d ],
                                [ A  +  d  +  b  +  C  +  e ],
                                [ A  +  d  +  C  +  b  +  e ],
                                
                                [ A  +  B  +  c  +  d  +  e ],
                                [ A  +  B  +  c  +  e  +  d ],
                                [ A  +  B  +  d  +  c  +  e ],
                                [ A  +  B  +  d  +  e  +  c ],
                                [ A  +  B  +  e  +  c  +  d ],
                                [ A  +  B  +  e  +  d  +  c ],
                                [ A  +  c  +  B  +  d  +  e ],
                                [ A  +  c  +  B  +  e  +  d ],
                                [ A  +  c  +  d  +  B  +  e ],
                                [ A  +  c  +  e  +  B  +  d ],
                                [ A  +  d  +  B  +  c  +  e ],
                                [ A  +  d  +  c  +  B  +  e ],
                                
                                
                                
                                # 4
                                [ A  +  b  +  c  +  d  +  e ],
                                [ A  +  b  +  c  +  e  +  d ],
                                [ A  +  b  +  d  +  c  +  e ],
                                [ A  +  b  +  d  +  e  +  c ],
                                [ A  +  b  +  e  +  c  +  d ],
                                [ A  +  b  +  e  +  d  +  c ],
                                [ A  +  c  +  b  +  d  +  e ],
                                [ A  +  c  +  b  +  e  +  d ],
                                [ A  +  c  +  d  +  b  +  e ],
                                [ A  +  c  +  e  +  b  +  d ],
                                [ A  +  d  +  b  +  c  +  e ],
                                [ A  +  d  +  c  +  b  +  e ], 
                                
                                [ a  +  B  +  c  +  d  +  e ],
                                [ a  +  B  +  c  +  e  +  d ],
                                [ a  +  B  +  d  +  c  +  e ],
                                [ a  +  B  +  d  +  e  +  c ],
                                [ a  +  B  +  e  +  c  +  d ],
                                [ a  +  B  +  e  +  d  +  c ],
                                [ a  +  c  +  B  +  d  +  e ],
                                [ a  +  c  +  B  +  e  +  d ],
                                [ a  +  c  +  d  +  B  +  e ],
                                [ a  +  c  +  e  +  B  +  d ],
                                [ a  +  d  +  B  +  c  +  e ],
                                [ a  +  d  +  c  +  B  +  e ], 
                                
                                [ a  +  b  +  C  +  d  +  e ],
                                [ a  +  b  +  C  +  e  +  d ],
                                [ a  +  b  +  d  +  C  +  e ],
                                [ a  +  b  +  d  +  e  +  C ],
                                [ a  +  b  +  e  +  C  +  d ],
                                [ a  +  b  +  e  +  d  +  C ],
                                [ a  +  C  +  b  +  d  +  e ],
                                [ a  +  C  +  b  +  e  +  d ],
                                [ a  +  C  +  d  +  b  +  e ],
                                [ a  +  C  +  e  +  b  +  d ],
                                [ a  +  d  +  b  +  C  +  e ],
                                [ a  +  d  +  C  +  b  +  e ], 
                                
                                [ a  +  b  +  c  +  D  +  e ],
                                [ a  +  b  +  c  +  e  +  D ],
                                [ a  +  b  +  D  +  c  +  e ],
                                [ a  +  b  +  D  +  e  +  c ],
                                [ a  +  b  +  e  +  c  +  D ],
                                [ a  +  b  +  e  +  D  +  c ],
                                [ a  +  c  +  b  +  D  +  e ],
                                [ a  +  c  +  b  +  e  +  D ],
                                [ a  +  c  +  D  +  b  +  e ],
                                [ a  +  c  +  e  +  b  +  D ],
                                [ a  +  D  +  b  +  c  +  e ],
                                [ a  +  D  +  c  +  b  +  e ], 

                                [ a  +  b  +  c  +  d  +  E ],
                                [ a  +  b  +  c  +  E  +  d ],
                                [ a  +  b  +  d  +  c  +  E ],
                                [ a  +  b  +  d  +  E  +  c ],
                                [ a  +  b  +  E  +  c  +  d ],
                                [ a  +  b  +  E  +  d  +  c ],
                                [ a  +  c  +  b  +  d  +  E ],
                                [ a  +  c  +  b  +  E  +  d ],
                                [ a  +  c  +  d  +  b  +  E ],
                                [ a  +  c  +  E  +  b  +  d ],
                                [ a  +  d  +  b  +  c  +  E ],
                                [ a  +  d  +  c  +  b  +  E ], 
                                
                                
                                
                                # 5
                                [ a  +  b  +  c  +  d  +  e ],
                                [ a  +  b  +  c  +  e  +  d ],
                                [ a  +  b  +  d  +  c  +  e ],
                                [ a  +  b  +  d  +  e  +  c ],
                                [ a  +  b  +  e  +  c  +  d ],
                                [ a  +  b  +  e  +  d  +  c ],
                                [ a  +  c  +  b  +  d  +  e ],
                                [ a  +  c  +  b  +  e  +  d ],
                                [ a  +  c  +  d  +  b  +  e ],
                                [ a  +  c  +  e  +  b  +  d ],
                                [ a  +  d  +  b  +  c  +  e ],
                                [ a  +  d  +  c  +  b  +  e ], 
                            ] 
            for item in trial:   
                best_route_1[0] = item[0]
                best_route_1[1] = distance_calc(distance_matrix, [best_route_1[0] + [best_route_1[0][0]], 1])
                if (best_route_1[1]  < best_route[1]):
                    best_route = [best_route_1[0], best_route_1[1]]
                if (best_route[1] < city_list[1]):
                    city_list = [best_route[0], best_route[1]]              
            best_route = copy.deepcopy(seed) 
        count     = count + 1  
        iteration = iteration + 1  
        if (city_list_old > city_list[1] and recursive_seeding < 0):
             city_list_old     = city_list[1]
             count             = -2
             recursive_seeding = -1
        elif(city_list[1] >= city_list_old and recursive_seeding < 0):
            count              = -1
            recursive_seeding  = -2
    city_list = [city_list[0] + [city_list[0][0]], city_list[1]]
    return city_list[0], city_list[1]

############################################################################