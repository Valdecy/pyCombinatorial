############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Concave Hull Algorithm
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
import copy
import numpy as np

from scipy.spatial import cKDTree, Delaunay

############################################################################

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

# Function: Check if Bounding Boxes Intersect
def bounding_boxes_intersection(a, b, c, d):
    LL1_x = min(a[0], b[0]); LL2_x = min(c[0], d[0])
    LL1_y = min(a[1], b[1]); LL2_y = min(c[1], d[1])
    UR1_x = max(a[0], b[0]); UR2_x = max(c[0], d[0])
    UR1_y = max(a[1], b[1]); UR2_y = max(c[1], d[1])
    return LL1_x <= UR2_x and UR1_x >= LL2_x and LL1_y <= UR2_y and UR1_y >= LL2_y

# Function: Check if a Point is on a Line
def point_on_line(a, b, c):
    b_ = (b[0] - a[0], b[1] - a[1])
    c_ = (c[0] - a[0], c[1] - a[1])
    r  = np.cross(b_, c_)
    return np.abs(r) < 0.0000000001

# Function: Check if a Point (c) is Right of a Line (a-b)
def right_of_line(a, b, c):
    b_ = (b[0] - a[0], b[1] - a[1])
    c_ = (c[0] - a[0], c[1] - a[1])
    return np.cross(b_, c_) < 0

# Function: Check if Line Segment (a-b) Touch or Cros Line Segment (c-d)
def line_segment_cross(a, b, c, d):
    return point_on_line(a, b, c) or point_on_line(a, b, d) or (right_of_line(a, b, c) ^ right_of_line(a, b, d))

# Function: Check if Line Segments (a-b) and (c-d) Intersects
def lines_intersection(a, b, c, d):
    return bounding_boxes_intersection and line_segment_cross(a, b, c, d) and line_segment_cross(c, d, a, b)
           
############################################################################      

# Function: K Nearest Neighbors of a Point
def k_nearest_neighbors(points, point_1, k):
    mytree             = cKDTree(points, leafsize = 10)
    distances, indices = mytree.query(point_1, k)
    return points[indices[:points.shape[0]]]

# Function: Sort Points by Angle
def sweep_points(k_points, point_1, point_0):
    angles = np.zeros(k_points.shape[0])
    i      = 0
    for k in k_points:
        angle     = np.arctan2(k[1] - point_1[1], k[0] - point_1[0]) - np.arctan2(point_0[1] - point_1[1], point_0[0] - point_1[0])
        angle     = np.rad2deg(angle)
        angle     = np.mod(angle + 360, 360)
        angles[i] = angle
        i         = i + 1
    return k_points[np.argsort(angles)]

# Function: Remove Point
def remove_point(points, point_):
    mask   = np.logical_or(points[:,0] != point_[0], points[:,1] != point_[1])
    mask   = [item for item in mask]
    coords = points[mask]
    return coords

############################################################################ 

#Function: Check if Points are Inside the Hull (Adapted from https://stackoverflow.com/questions/16750618/whats-an-efficient-way-to-find-if-a-point-lies-in-the-convex-hull-of-a-point-cl)
def in_hull(coordinates, hull):
    if (not isinstance(hull, Delaunay)):
        hull_ = Delaunay(hull)
    res = hull_.find_simplex(coordinates) >= 0
    res = res * 1
    if (np.sum(res) == coordinates.shape[0]):
        return True
    else:
        return False  

############################################################################

# Function: Concave Hull (Adapted from https://github.com/sebastianbeyer/concavehull)
def ConcaveHull(coordinates, k = 3):
    k          = np.clip(k, 3, float('+inf'))
    points     = np.copy(coordinates)
    point_     = coordinates[np.argmin(coordinates[:,1])]
    hull       = []
    hull.append(point_)
    points     = remove_point(coordinates, point_)
    point_1    = point_
    point_0    = (point_1[0] + 10, point_1[1])
    step       = 2
    while ( (not np.array_equal(point_, point_1) or (step == 2)) and points.size > 0 ):
        if (step == 5):
            points = np.append(points, [point_], axis = 0)
        k_points = k_nearest_neighbors(points, point_1, k)
        c_points = sweep_points(k_points, point_1, point_0)
        m        = True
        i        = 0
        while ((m == True) and (i < c_points.shape[0])):
                i = i + 1
                if (np.array_equal(c_points[i-1], point_)):
                    pt = 1
                else:
                    pt = 0
                j = 2
                m = False
                while ((m == False) and (j < np.shape(hull)[0] - pt)):
                    m = lines_intersection(hull[step - 1 - 1], c_points[i - 1], hull[step - 1 - j - 1], hull[step - j - 1])
                    j = j + 1
        if (m == True):
            return ConcaveHull(coordinates, k + 1)
        point_0 = point_1
        point_1 = c_points[i-1]
        hull.append(point_1)
        points  = remove_point(points, point_1)
        step    = step + 1
    if (not in_hull(coordinates, hull)):
        return ConcaveHull(coordinates, k + 1)
    idx = []
    for coords in hull:
        a   = coords
        b   = np.where((coordinates == a).all(axis = 1))[0][0]
        idx.append(b)
    return idx

############################################################################

# Function: Concave Hull
def concave_hull_algorithm(coordinates, distance_matrix, local_search = True, verbose = True):
    hull        = ConcaveHull(coordinates, k = 3)
    idx_h       = [item+1 for item in hull]
    idx_h_pairs = [(idx_h[i], idx_h[i+1]) for i in range(0, len(idx_h)-1)]
    idx_h_pairs.append((idx_h[-1], idx_h[0]))
    idx_in      = [item for item in list(range(1, coordinates.shape[0]+1)) if item not in idx_h]
    for _ in range(0, len(idx_in)):
        x = []
        y = []
        z = []
        for i in range(0, len(idx_in)):
            L           = idx_in[i]
            cost        = [(distance_matrix[m-1, L-1], distance_matrix[L-1, n-1], distance_matrix[m-1, n-1]) for m, n in idx_h_pairs]
            cost_idx    = [(m, L, n) for m, n in idx_h_pairs]
            cost_vec_1  = [ item[0] + item[1]  - item[2] for item in cost]
            cost_vec_2  = [(item[0] + item[1]) / (item[2] + 0.00000000000000001) for item in cost]
            x.append(cost_vec_1.index(min(cost_vec_1)))
            y.append(cost_vec_2[x[-1]])
            z.append(cost_idx[x[-1]])
        m, L, n     = z[y.index(min(y))]
        idx_in.remove(L)
        ins         = idx_h.index(m)
        idx_h.insert(ins + 1, L)
        idx_h_pairs = [ (idx_h[i], idx_h[i+1]) for i in range(0, len(idx_h)-1)]
        idx_h_pairs.append((idx_h[-1], idx_h[0]))
    route    = idx_h
    distance = distance_calc(distance_matrix, [route, 1])
    seed     = [route, distance]
    if (local_search == True):
        route, distance = local_search_2_opt(distance_matrix, seed, recursive_seeding = -1, verbose = verbose)
    return route, distance

############################################################################