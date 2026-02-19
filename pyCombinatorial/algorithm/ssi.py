############################################################################

# Created by: Prof. Valdecy Pereira, D.Sc.
# UFF - Universidade Federal Fluminense (Brazil)
# email:  valdecy.pereira@gmail.com
# Lesson: pyCombinatorial - SSI (Spectral Seriation Initializer)
 
# GitHub Repository: <https://github.com/Valdecy> 

############################################################################

# Required Libraries
import numpy as np

from numba import njit
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import eigsh

############################################################################

# Function: Tour Lenght
@njit(fastmath = True)
def tour_length(tour, D):
    n = len(tour)
    L = 0.0
    for i in range(n):
        L = L + D[tour[i], tour[(i + 1) % n]]
    return L

# Function: 2-opt Passes
@njit(fastmath = True)
def two_opt(tour, D, max_passes):
    n        = len(tour)
    improved = True
    passes   = 0  
    while improved and passes < max_passes:
        improved = False
        passes   = passes + 1
        for i in range(0, n - 1):
            a_idx = tour[i]
            b_idx = tour[(i + 1)]
            k_end = n - 1 if i == 0 else n 
            for k in range(i + 2, k_end):
                c_idx        = tour[k]
                d_idx        = tour[(k + 1) % n]
                current_cost = D[a_idx, b_idx] + D[c_idx, d_idx]
                new_cost     = D[a_idx, c_idx] + D[b_idx, d_idx]       
                if new_cost < current_cost:
                    p1 = i + 1
                    p2 = k
                    while p1 < p2:
                        temp     = tour[p1]
                        tour[p1] = tour[p2]
                        tour[p2] = temp
                        p1       = p1 + 1
                        p2       = p2 - 1
                    improved = True  
    return tour

############################################################################

# Function: KNN
def knn_indices(D, k):
    return np.argsort(D, axis = 1)[:, 1 : k + 1]

# Function: Affinity
def build_affinity_sparse(D, k, sigma_mode, sigma_fixed):
    n    = D.shape[0]
    nbrs = knn_indices(D.astype(float), k)
    if sigma_mode == 'adaptive':
        sig = D[np.arange(n), nbrs[:, -1]].astype(float) + 1e-12
    else:
        sig = np.full(n, sigma_fixed, dtype = float)
    rows, cols, vals = [], [], []
    for i in range(n):
        si = sig[i]
        for j in nbrs[i]:
            sj = sig[j]
            dij = float(D[i, j])
            if sigma_mode == 'adaptive':
                w = np.exp(-(dij * dij) / (si * sj + 1e-12))
            else:
                w = np.exp(-(dij * dij) / (2.0 * sigma_fixed * sigma_fixed + 1e-12))
            rows.append(i); cols.append(j); vals.append(w)
    W = coo_matrix((vals, (rows, cols)), shape = (n, n)).tocsr()
    W = (W + W.T).tocsr()      
    W = W.tolil()              
    W.setdiag(0.0)
    W = W.tocsr()
    W.eliminate_zeros()
    return W

# Function: Laplacian
def laplacian_from_W(W):
    d = np.array(W.sum(axis = 1)).reshape(-1)
    return (diags(d) - W).tocsr()

# Function: Fiedler Vector
def fiedler_vector(L):
    vals, vecs = eigsh(L, k = 4, which = 'SM')
    idx        = np.argsort(vals)
    vals       = vals[idx]
    vecs       = vecs[:, idx]
    eps        = 1e-10
    j          = 0
    while j < len(vals) and vals[j] < eps:
        j = j + 1
    if j == 0 and len(vals) > 1:
        j = 1
    j = min(j, len(vals) - 1)
    return vecs[:, j].copy()

############################################################################

# Spectral Seriation Initializer
def spectral_seriation_initializer(D, k = 12, iterations = 800, sigma_noise = 0.003, sigma_mode = 'adaptive', sigma_fixed = 250.0, two_opt_passes = 10, rnd = 7, verbose = True):
    D         = np.asarray(D)
    n         = D.shape[0]
    rng       = np.random.default_rng(rnd)
    W         = build_affinity_sparse(D, k, sigma_mode, sigma_fixed)
    L         = laplacian_from_W(W)
    x         = fiedler_vector(L)
    best_L    = float("inf")
    best_tour = None
    for nt in range(0, iterations):
        x_noisy = x + rng.normal(0.0, sigma_noise, size = n)
        tour    = np.argsort(x_noisy).astype(np.int32)
        if rng.random() < 0.5:
            tour = tour[::-1]
        shift = int(rng.integers(0, n))
        tour  = np.roll(tour, shift)
        tour  = two_opt(tour, D, two_opt_passes)
        Lc    = tour_length(tour, D)
        if Lc < best_L:
            best_L    = Lc
            best_tour = tour
        if verbose:
            print('Iteration = ', nt, 'Distance = ', best_L)
    best_tour = [item + 1 for item in best_tour]
    best_tour.append(best_tour[0])
    return best_tour, int(best_L)


############################################################################
