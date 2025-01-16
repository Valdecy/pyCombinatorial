############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - Util
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import numpy  as np
import random

############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

# Function: Initial Seed
def seed_function(distance_matrix):
    seed     = [[], float('inf')]
    sequence = random.sample(list(range(1, distance_matrix.shape[0]+1)), distance_matrix.shape[0])
    sequence.append(sequence[0])
    seed[0]  = sequence
    seed[1]  = distance_calc(distance_matrix, seed)
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

# Function: LatLong -> Cartesian
def latlong_to_cartesian(lat_long):
    if (hasattr(lat_long, 'values')): 
        lat_long = lat_long.values
    lat     = lat_long[:, 0]
    lon     = lat_long[:, 1]
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    R       = 6371.0
    x       = R * np.cos(lat_rad) * np.cos(lon_rad)
    y       = R * np.cos(lat_rad) * np.sin(lon_rad)
    #z       = R * np.sin(lat_rad)
    return np.column_stack((x, y))

# Function: Build Distance Matrix Lat Long
def latlong_distance_matrix(coordinates):
    coords_rad = np.radians(coordinates)
    coords_rad = coords_rad.values
    latitudes  = coords_rad[:, 0][:, np.newaxis]
    longitudes = coords_rad[:, 1][:, np.newaxis]
    dlat       = latitudes - latitudes.T
    dlon       = longitudes - longitudes.T
    a          = np.sin(dlat / 2)**2 + np.cos(latitudes) * np.cos(latitudes.T) * np.sin(dlon / 2)**2
    c          = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    R          = 6371.0
    return R * c

############################################################################
