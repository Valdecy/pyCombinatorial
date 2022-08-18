############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: Karp-Steele Patching Algorithm
 
# GitHub Repository: <https://github.com/Valdecy>

############################################################################

# Required Libraries
#import copy
import numpy as np

from collections import defaultdict
from scipy import optimize

###############################################################################

# Function: Cycle Finder (Adapted from:  https://gist.github.com/qpwo/272df112928391b2c83a3b67732a5c25; Author: Luke Harold Miles; email: luke@cs.uky.edu; Site: https://lukemiles.org
def simple_cycles(G):
    def _unblock(thisnode, blocked, B):
        stack = set([thisnode])
        while stack:
            node = stack.pop()
            if node in blocked:
                blocked.remove(node)
                stack.update(B[node])
                B[node].clear()
    G    = {v: set(nbrs) for (v,nbrs) in G.items()}
    sccs = strongly_connected_components(G)
    while sccs:
        scc       = sccs.pop()
        startnode = scc.pop()
        path      = [startnode]
        blocked   = set()
        closed    = set()
        blocked.add(startnode)
        B         = defaultdict(set)
        stack     = [ (startnode,list(G[startnode])) ]
        while stack:
            thisnode, nbrs = stack[-1]
            if nbrs:
                nextnode = nbrs.pop()
                if nextnode == startnode:
                    yield path[:]
                    closed.update(path)
                elif nextnode not in blocked:
                    path.append(nextnode)
                    stack.append( (nextnode, list(G[nextnode])) )
                    closed.discard(nextnode)
                    blocked.add(nextnode)
                    continue
            if not nbrs:
                if thisnode in closed:
                    _unblock(thisnode, blocked, B)
                else:
                    for nbr in G[thisnode]:
                        if thisnode not in B[nbr]:
                            B[nbr].add(thisnode)
                stack.pop()
                path.pop()
        remove_node(G, startnode)
        H = subgraph(G, set(scc))
        sccs.extend(strongly_connected_components(H))

# Function: SCC       
def strongly_connected_components(graph):
    index_counter = [0]
    stack         = []
    lowlink       = {}
    index         = {}
    result        = []   
    def _strong_connect(node):
        index[node]      = index_counter[0]
        lowlink[node]    = index_counter[0]
        index_counter[0] = index_counter[0] + 1
        stack.append(node) 
        successors       = graph[node]
        for successor in successors:
            if successor not in index:
                _strong_connect(successor)
                lowlink[node] = min(lowlink[node],lowlink[successor])
            elif successor in stack:
                lowlink[node] = min(lowlink[node],index[successor])
        if lowlink[node] == index[node]:
            connected_component = []
            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node: break
            result.append(connected_component[:])
    for node in graph:
        if node not in index:
            _strong_connect(node)
    return result

# Function: Remove Node
def remove_node(G, target):
    del G[target]
    for nbrs in G.values():
        nbrs.discard(target)

# Function: Subgraph
def subgraph(G, vertices):
    return {v: G[v] & vertices for v in vertices}

###############################################################################

# Function: Tour Distance
def distance_calc(distance_matrix, city_tour):
    distance = 0
    for k in range(0, len(city_tour[0])-1):
        m        = k + 1
        distance = distance + distance_matrix[city_tour[0][k]-1, city_tour[0][m]-1]            
    return distance

############################################################################

# Function: Patch Cycles a and b
def patch_cycles(a, b, distance_matrix):
    a       = [item for item in a]
    a       = a + [a[0]]
    b       = [item for item in b]
    b       = b + [b[0]]
    pairs_a = [ (a[i], a[i+1]) for i in range(0, len(a)-1)]
    pairs_b = [ (b[i], b[i+1]) for i in range(0, len(b)-1)]
    pairs   = pairs_a + pairs_b
    temp    = []
    val     = []
    links   = []
    del_lks = []
    for m in pairs_a:
        m1, m2 = m
        for n in pairs_b:
            n1, n2 = n
            link_1 = (n1, m1)
            link_2 = (n2, m2)
            link_3 = (n2, m1)
            link_4 = (n1, m2)
            links.append([link_1, link_2, link_3, link_4])
            del_lks.append([m, n])
    for i in range(0, len(del_lks)):
        i1, i2     = del_lks[i]
        pairs.remove(i1)
        pairs.remove(i2)
        a, b, c, d = links[i]
        pairs_ab   = [item for item in pairs]
        pairs_cd   = [item for item in pairs]
        pairs_ab.append(b)
        pairs_cd.append(d)
        search_ab  = [a]
        search_cd  = [c]
        while len(pairs_ab) > 0:
            for j in pairs_ab:
                if (search_ab[-1][1] == j[0]):
                    search_ab.append(j)
                    pairs_ab.remove(j)
                    break
                if (search_ab[-1][1] == j[1]):
                    j1, j2 = j
                    search_ab.append((j2,j1))
                    pairs_ab.remove(j)
                    break
        while len(pairs_cd) > 0:
            for j in pairs_cd:
                if (search_cd[-1][1] == j[0]):
                    search_cd.append(j)
                    pairs_cd.remove(j)
                    break
                if (search_cd[-1][1] == j[1]):
                    j1, j2 = j
                    search_cd.append((j2,j1))
                    pairs_cd.remove(j)
                    break
        pairs   = pairs_a + pairs_b
        temp_ab = []
        temp_cd = []
        for k in search_ab:
            k1, k2 = k
            if (k1 not in temp_ab):
                temp_ab.append(k1)
            if (k2 not in temp_ab):
                temp_ab.append(k2)
        for k in search_cd:
            k1, k2 = k
            if (k1 not in temp_cd):
                temp_cd.append(k1)
            if (k2 not in temp_ab):
                temp_cd.append(k2)
        temp_ab = [item+1 for item in temp_ab]
        temp_ab = temp_ab + [temp_ab[0]]
        dist_ab = distance_calc(distance_matrix, [temp_ab, 1])
        temp_cd = [item+1 for item in temp_cd]
        temp_cd = temp_cd + [temp_cd[0]]
        dist_cd = distance_calc(distance_matrix, [temp_cd, 1])
        if (dist_ab < dist_cd):
            temp_ab = [item-1 for item in temp_ab[:-1]]
            temp.append(temp_ab)
            val.append(dist_ab)
        else:
            temp_cd = [item-1 for item in temp_cd[:-1]]
            temp.append(temp_cd)
            val.append(dist_cd)
    route    = temp[val.index(min(val))]
    distance = val[val.index(min(val))]
    return route, distance


############################################################################

# Function: Karp Steele Patching
def karp_steele_patching(distance_matrix, verbose = True):
    count      = 0
    route      = []
    dist       = np.copy(distance_matrix)
    np.fill_diagonal(dist, np.sum(dist))
    r, c       = optimize.linear_sum_assignment(dist)
    adj_m      = np.zeros((dist.shape))
    adj_m[r,c] = 1
    graph      = {}
    value      = [[] for i in range(adj_m.shape[0])]
    keys       = range(adj_m.shape[0])
    for i in range(0, adj_m.shape[0]):
        for j in range(0, adj_m.shape[0]):
            if (adj_m[i,j] == 1):
                value[i].append(j)
    for i in keys:
        graph[i] = value[i]  
    cycles = list(simple_cycles(graph))
    cycles = sorted(cycles, key = len)
    cycles.reverse()
    a      = cycles[0]
    #for cycle in cycles:
    for i in range(1, len(cycles)):
        b               = cycles[i]
        route, distance = patch_cycles(a, b, distance_matrix)
        a               = route
        if (verbose == True):
            print('Iteration = ', count, ' Visited Nodes = ', len(route))
        count = count + 1
    route    = route + [route[0]]
    route    = [item + 1 for item in route]
    distance = distance_calc(distance_matrix, [route, 1])
    return route, distance

############################################################################